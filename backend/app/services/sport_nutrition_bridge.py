"""
Pont Sport -> Nutrition/Hydratation (module Sport, parties 15, 16, 17).

Ce fichier NE remplace ni ne duplique :
    - app/services/nutrition.py     (calculate_calories, calculate_macros)
    - app/services/hydration.py     (calculate_water_goal_ml)

Il les enrichit : calcule une depense calorique et un besoin
d'hydratation SUPPLEMENTAIRES lies aux seances de sport reellement
effectuees (WorkoutLog) un jour donne, puis rappelle
calculate_calories/calculate_water_goal_ml pour produire un total
ajuste.

Fonctionne aussi bien pour :
    - un sportif (WorkoutLog present ce jour-la -> depense/hydratation
      additionnelles)
    - un non-sportif (aucun WorkoutLog -> additions a 0, comportement
      strictement identique au moteur nutritionnel de base, module
      Sport partie 11 : jamais d'erreur, jamais de sport obligatoire)

HYPOTHESES VALIDEES AVEC L'UTILISATEUR :
    - WorkoutLog n'a pas de champ calories_burned (contrairement a la
      WorkoutSession du cahier des charges). Quand la seance loguee
      derive d'un Workout planifie (based_on_workout_id) qui porte une
      estimated_calories_kcal, on la reutilise telle quelle
      ("planned_estimate"). Sinon, on retombe sur une formule simple
      poids x duree x intensite RPE ("fallback_formula"), moins
      precise mais jamais bloquante ("insufficient_data" si meme la
      duree manque).

AUTRE HYPOTHESE (a affiner si besoin, non bloquante) :
    - Le "focus nutritionnel" (partie 16) est indicatif, base sur le
      slug du sport principal de l'utilisateur (seed_sports.py) : une
      liste fermee et extensible, jamais une regle stricte.
    - Le decoupage "jour" utilise ici est UTC simple (partie 18 :
      determiner le jour selon le fuseau reel de l'utilisateur est
      laisse aux routes de l'etape 10, qui connaissent ce fuseau).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.profile import Profile
from app.models.training_log import WorkoutLog, WorkoutLogExercise
from app.services.hydration import calculate_water_goal_ml
from app.services.nutrition import calculate_calories, calculate_macros
from app.services.training_service import get_primary_sport


# ============================================================
# CONSTANTES (configurables, memes conventions que recovery_service.py)
# ============================================================

# Formule de secours quand aucune estimation planifiee n'est disponible :
#   depense = duree_minutes x poids_kg x KCAL_PER_KG_PER_MINUTE x facteur_rpe
# 0.1 kcal/kg/min correspond a un effort "modere" (~360 kcal/h pour 60kg),
# valeur mediane volontairement simple, meme esprit que ML_PER_KG dans
# hydration.py.
KCAL_PER_KG_PER_MINUTE = 0.1

DEFAULT_WEIGHT_KG = 70.0  # secours si jamais le poids est indisponible

# Facteur d'intensite applique a la formule de secours (calories ET
# hydratation), teste dans l'ordre decroissant : premier seuil atteint
# ou depasse gagne. RPE inconnu -> facteur neutre 1.0.
RPE_INTENSITY_FACTOR: list[tuple[float, float]] = [
    (9.0, 1.6),
    (7.0, 1.3),
    (5.0, 1.0),
    (3.0, 0.8),
    (0.0, 0.6),
]

# Hydratation additionnelle (partie 17) : ml par minute d'effort, module
# par la meme intensite RPE. 10 ml/min ~ 600 ml/h pour une seance
# moderee, coherent avec les recommandations usuelles (400-800 ml/h).
ML_PER_MINUTE_TRAINING = 10.0

# Focus nutritionnel indicatif (partie 16), base sur le sport principal
# (slugs de seed_sports.py, etape 4). Extensible : ajouter une entree
# ne casse rien pour les sports non listes (retourne None).
SPORT_NUTRITION_FOCUS: dict[str, list[str]] = {
    "musculation": ["proteines", "glucides_suffisants", "repas_post_workout"],
    "course": ["glucides", "hydratation", "repas_pre_entrainement", "recuperation"],
    "cyclisme": ["glucides", "hydratation", "recuperation"],
    "natation": ["glucides", "hydratation", "recuperation"],
    "football": ["glucides", "hydratation", "pre_entrainement", "post_entrainement"],
    "basketball": ["glucides", "hydratation", "pre_entrainement", "post_entrainement"],
    "boxe": ["glucides", "hydratation", "recuperation"],
    "arts_martiaux": ["glucides", "hydratation", "recuperation"],
    "fitness": ["proteines", "hydratation"],
    "cardio": ["glucides", "hydratation"],
}


# ============================================================
# INTENSITE (RPE) DE LA SEANCE
# ============================================================

def _rpe_intensity_factor(average_rpe: Optional[float]) -> float:
    """1.0 si RPE inconnu (neutre), sinon facteur croissant avec l'intensite."""

    if average_rpe is None:
        return 1.0
    for threshold, factor in RPE_INTENSITY_FACTOR:
        if average_rpe >= threshold:
            return factor
    return 1.0


def estimate_calories_from_effort(
    duration_minutes: Optional[float], weight_kg: float, average_rpe: Optional[float] = None
) -> float:
    """
    Formule de secours publique (duree x poids x intensite RPE), utilisee
    a la fois pour une seance deja loguee (estimate_session_calories,
    partie 15/16) et pour une seance encore RECOMMANDEE mais pas encore
    effectuee (app/routes/sport.py : previsualisation de
    estimated_calories_kcal avant que l'utilisateur ne demarre la
    seance). 0.0 si la duree est inconnue plutot qu'une erreur.
    """

    if duration_minutes is None:
        return 0.0
    factor = _rpe_intensity_factor(average_rpe)
    return round(duration_minutes * weight_kg * KCAL_PER_KG_PER_MINUTE * factor, 1)


def _session_average_rpe(log: WorkoutLog) -> Optional[float]:
    values = [
        float(s.rpe)
        for exercise in log.exercises
        for s in exercise.sets
        if s.rpe is not None
    ]
    return sum(values) / len(values) if values else None


# ============================================================
# LECTURE DES SEANCES DU JOUR
# ============================================================

def get_workout_logs_for_date(
    db: Session, user_id: uuid.UUID, on_date: date
) -> list[WorkoutLog]:
    """Seances reellement effectuees a une date precise (bornes UTC,
    voir HYPOTHESE partie 18 en tete de fichier)."""

    start = datetime.combine(on_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(on_date, time.max, tzinfo=timezone.utc)

    return (
        db.execute(
            select(WorkoutLog)
            .options(
                selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.sets),
                selectinload(WorkoutLog.based_on_workout),
            )
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.performed_at >= start,
                WorkoutLog.performed_at <= end,
            )
        )
        .scalars()
        .all()
    )


# ============================================================
# CALORIES PAR SEANCE (partie 15/16)
# ============================================================

def estimate_session_calories(log: WorkoutLog, weight_kg: float) -> tuple[float, str]:
    """
    Calories brulees pour UNE seance loguee.

    Retourne (calories, source) ou source vaut :
        "planned_estimate"   -> reprise de Workout.estimated_calories_kcal
        "fallback_formula"   -> duree x poids x intensite RPE
        "insufficient_data"  -> ni estimation planifiee ni duree connue
    """

    planned = log.based_on_workout
    if planned is not None and planned.estimated_calories_kcal is not None:
        return float(planned.estimated_calories_kcal), "planned_estimate"

    if log.duration_minutes is None:
        return 0.0, "insufficient_data"

    calories = estimate_calories_from_effort(
        log.duration_minutes, weight_kg, _session_average_rpe(log)
    )
    return calories, "fallback_formula"


def get_training_energy_for_date(
    db: Session, user_id: uuid.UUID, on_date: date, weight_kg: float
) -> dict:
    """Depense calorique additionnelle totale du jour, detail par
    seance inclus pour tracabilite (utile pour debug/UI)."""

    logs = get_workout_logs_for_date(db, user_id, on_date)

    sessions = []
    total = 0.0
    for log in logs:
        calories, source = estimate_session_calories(log, weight_kg)
        total += calories
        sessions.append(
            {
                "workout_log_id": str(log.id),
                "duration_minutes": log.duration_minutes,
                "calories_kcal": calories,
                "source": source,
            }
        )

    return {
        "date": on_date.isoformat(),
        "session_count": len(logs),
        "total_calories_kcal": round(total, 1),
        "sessions": sessions,
    }


# ============================================================
# HYDRATATION PAR SEANCE (partie 17)
# ============================================================

def estimate_session_hydration_ml(log: WorkoutLog) -> float:
    """Hydratation additionnelle pour UNE seance loguee."""

    if log.duration_minutes is None:
        return 0.0
    factor = _rpe_intensity_factor(_session_average_rpe(log))
    return round(log.duration_minutes * ML_PER_MINUTE_TRAINING * factor)


def get_training_hydration_for_date(
    db: Session, user_id: uuid.UUID, on_date: date
) -> dict:
    """Hydratation additionnelle totale du jour."""

    logs = get_workout_logs_for_date(db, user_id, on_date)
    total_ml = sum(estimate_session_hydration_ml(log) for log in logs)

    return {
        "date": on_date.isoformat(),
        "session_count": len(logs),
        "additional_hydration_ml": round(total_ml),
    }


# ============================================================
# FOCUS NUTRITIONNEL INDICATIF (partie 16)
# ============================================================

def get_nutrition_focus(db: Session, user_id: uuid.UUID) -> Optional[list[str]]:
    """Priorites nutritionnelles indicatives liees au sport principal.
    None si l'utilisateur n'a pas de sport principal (non-sportif :
    aucune priorite forcee, module Sport partie 11)."""

    primary = get_primary_sport(db, user_id)
    if primary is None or primary.sport is None:
        return None
    return SPORT_NUTRITION_FOCUS.get(primary.sport.slug)


# ============================================================
# RESUME QUOTIDIEN COMBINE (ce que les routes de l'etape 10 appelleront)
# ============================================================

def get_daily_nutrition_and_hydration(
    db: Session, user_id: uuid.UUID, on_date: Optional[date] = None
) -> dict:
    """
    Nutrition + hydratation du jour, sport inclus (parties 15-17).

    Reutilise integralement calculate_calories / calculate_macros /
    calculate_water_goal_ml : ce fichier ne fait qu'ajouter par-dessus
    la depense et le besoin d'hydratation lies a l'entrainement du
    jour. Pour un utilisateur sans aucune seance loguee ce jour-la
    (sportif au repos ou non-sportif), les valeurs ajustees sont
    strictement egales aux valeurs de base.

    Leve ValueError si le profil est incomplet, meme convention que
    app/services/nutrition.py (a charge des routes de l'etape 10 de
    convertir en HTTPException 400, comme le fait deja routes/nutrition.py).
    """

    on_date = on_date or date.today()

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    if profile is None:
        raise ValueError("Profile not found")

    required_fields = {
        "age": profile.age,
        "sex": profile.sex,
        "height_cm": profile.height_cm,
        "current_weight_kg": profile.current_weight_kg,
        "activity_level": profile.activity_level,
        "primary_goal": profile.primary_goal,
    }
    missing_fields = [f for f, v in required_fields.items() if v is None]
    if missing_fields:
        raise ValueError(f"Incomplete profile, missing fields: {missing_fields}")

    weight_kg = float(profile.current_weight_kg)

    base_nutrition = calculate_calories(
        weight_kg=weight_kg,
        height_cm=float(profile.height_cm),
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal=profile.primary_goal,
    )

    training_energy = get_training_energy_for_date(db, user_id, on_date, weight_kg)
    training_hydration = get_training_hydration_for_date(db, user_id, on_date)

    adjusted_calories = round(
        base_nutrition["daily_calories"] + training_energy["total_calories_kcal"], 2
    )
    adjusted_macros = calculate_macros(
        weight_kg=weight_kg,
        daily_calories=adjusted_calories,
        goal=profile.primary_goal,
    )

    base_hydration_ml = calculate_water_goal_ml(
        weight_kg=weight_kg,
        activity_level=profile.activity_level,
    )
    adjusted_hydration_ml = round(
        base_hydration_ml + training_hydration["additional_hydration_ml"]
    )

    return {
        "date": on_date.isoformat(),
        "base": base_nutrition,
        "training_energy": training_energy,
        "adjusted_daily_calories": adjusted_calories,
        "adjusted_macros": adjusted_macros,
        "base_hydration_ml": base_hydration_ml,
        "training_hydration": training_hydration,
        "adjusted_hydration_ml": adjusted_hydration_ml,
        "nutrition_focus": get_nutrition_focus(db, user_id),
    }
