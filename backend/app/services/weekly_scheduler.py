"""
Assemble un programme hebdomadaire de 7 jours (cahier des charges
etendu fourni par l'utilisateur, parties 6, 15-17, 26 : Weekly
Scheduler + Program Validator), par-dessus recommend_workout()
(module Sport, etape 6) -- jamais un nouveau moteur de scoring,
jamais un programme pre-calcule stocke par combinaison sport x
objectif x frequence x duree (partie 2/6 du cahier des charges :
explosion combinatoire a eviter absolument). Chaque appel regenere
la semaine a la volee, exactement comme recommend_workout() le fait
deja pour une seule seance.

Repartition des jours d'entrainement : heuristique d'espacement
simple (pas un solveur d'optimisation) -- suffisante pour eviter les
cas flagrants ("3 jours d'affilee") sans sur-ingenierie (partie 37 du
cahier des charges : pas de complexite artificielle).

Detection de conflits (partie 17) : simulation simple d'une
"recuperation attendue" qui se degrade apres un jour d'entrainement
intense/a charge et remonte apres un jour de repos, reinjectee dans
recommend_workout(recovery_score=...) -- reutilise le mecanisme deja
existant de l'etape 8 (un recovery_score bas fait deja baisser le RPE
cible et donc l'intensite proposee) plutot que d'inventer une
deuxieme logique d'intensite en parallele.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import GoalType, TrainingType
from app.models.profile import Profile
from app.services.recovery_service import compute_recovery_score
from app.services.sport_nutrition_bridge import (
    DEFAULT_WEIGHT_KG,
    estimate_calories_from_effort,
    get_nutrition_focus,
)
from app.services.training_programs import build_training_day_sequence
from app.services.training_recommender import LOAD_BASED_TYPES, recommend_workout
from app.services.training_service import get_primary_sport, list_exercises


# ============================================================
# CONSTANTES (configurables, memes conventions que les autres services
# du module Sport)
# ============================================================

DAY_LABELS = ["Jour 1", "Jour 2", "Jour 3", "Jour 4", "Jour 5", "Jour 6", "Jour 7"]

# Utilisee si l'utilisateur n'a pas de sport principal ou n'a pas
# renseigne de frequence (partie 21 : jamais d'erreur, un programme
# "healthy lifestyle" raisonnable par defaut).
DEFAULT_FREQUENCY_PER_WEEK = 3

# RPE a partir duquel une seance est consideree "a forte intensite"
# pour la detection de conflits (partie 17).
HIGH_INTENSITY_RPE_THRESHOLD = 7.5

# Simulation de la recuperation attendue au fil de la semaine (partie
# 26). Valeurs choisies pour degrader visiblement apres un effort
# intense sans jamais tomber a 0 (RECOVERY_FLOOR) ni depasser 1.0.
RECOVERY_DROP_AFTER_TRAINING = 0.3
RECOVERY_DROP_AFTER_HIGH_INTENSITY = 0.45
RECOVERY_GAIN_AFTER_REST = 0.35
RECOVERY_FLOOR = 0.15
RECOVERY_CEILING = 1.0
STARTING_RECOVERY = 0.8

REST_DAY_ACTIVITY_DURATION_MINUTES = 15


# ============================================================
# REPARTITION DES JOURS D'ENTRAINEMENT (partie 16)
# ============================================================

def _spaced_training_days(frequency_per_week: int) -> list[int]:
    """
    Indices (0-6) des jours d'entrainement, repartis au mieux sur les 7
    jours de la semaine. Heuristique simple (pas un solveur
    d'optimisation) : a haute frequence (5-7x/semaine), un minimum
    d'enchainements est mathematiquement inevitable -- la detection de
    conflits ci-dessous attenue alors l'intensite plutot que de
    pretendre les eliminer completement.
    """

    frequency_per_week = max(0, min(7, frequency_per_week))
    if frequency_per_week == 0:
        return []
    if frequency_per_week >= 7:
        return list(range(7))

    used: set[int] = set()
    for i in range(frequency_per_week):
        target = round(i * 7 / frequency_per_week) % 7
        while target in used:
            target = (target + 1) % 7
        used.add(target)

    return sorted(used)


def _weight_kg_for_user(db: Session, user_id: uuid.UUID) -> float:
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    if profile is not None and profile.current_weight_kg is not None:
        return float(profile.current_weight_kg)
    return DEFAULT_WEIGHT_KG


def _activity_level_for_user(db: Session, user_id: uuid.UUID):
    """Niveau d'activite du profil (regle 24, ActivityLevel), utilise par
    training_programs.build_training_day_sequence pour distinguer un
    profil sedentaire (Branche 1, sport ignore) d'un profil actif sans
    sport principal (Branche 6, hybride). None si le profil n'existe pas
    encore -- jamais d'erreur, build_training_day_sequence gere deja ce
    cas (retombe sur la branche hybride)."""
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    return profile.activity_level if profile is not None else None


def _fill_calories(workout: dict, weight_kg: float) -> dict:
    """Meme formule que routes/sport.py:_fill_estimated_calories, pour
    ne pas dupliquer une deuxieme estimation differente (etape 9)."""

    workout["estimated_calories_kcal"] = estimate_calories_from_effort(
        workout.get("planned_duration_minutes"), weight_kg, workout.get("target_rpe")
    )
    return workout


def _build_rest_day(db: Session, day_index: int, sport_slug: Optional[str] = None) -> dict:
    """
    Jour de repos/recuperation active : 1-2 activites legeres. On pioche
    d'abord dans les activites de recuperation SPECIFIQUES au sport de
    l'utilisateur (piscine pour le combat, footing de decharge pour la
    course...) puis on complete avec les generiques (marche, etirements).
    Jamais d'erreur si le catalogue est vide, le jour reste simplement un
    jour de repos sans activite suggeree (partie 21 : meme logique que le
    programme "sport = none").
    """

    allowed_types = {TrainingType.RECOVERY, TrainingType.MOBILITY}

    def _recovery_pool(slugs):
        return [
            e
            for e in list_exercises(db, sport_slug=slugs)
            if e.training_types
            and any(t in allowed_types for t in e.training_types)
        ]

    # Specifique au sport en priorite, puis generiques (sport_id is None).
    specific = _recovery_pool(sport_slug) if sport_slug else []
    generic = [e for e in _recovery_pool(None) if e.sport_id is None]

    # Jamais deux fois le meme exercice dans la journee.
    seen: set[str] = set()
    picked: list = []
    for e in specific + generic:
        if e.slug not in seen:
            seen.add(e.slug)
            picked.append(e)

    return {
        "day_label": DAY_LABELS[day_index],
        "day_type": "rest",
        "activities": [
            {"exercise_slug": e.slug, "duration_minutes": REST_DAY_ACTIVITY_DURATION_MINUTES}
            for e in picked[:2]
        ],
        "estimated_calories_kcal": 0.0,
    }


# ============================================================
# PROGRAM VALIDATOR (partie 31)
# ============================================================

def validate_weekly_program(days: list[dict], frequency_per_week: int) -> dict:
    """
    Verifications post-generation. Ne bloque jamais la reponse : les
    problemes detectes deviennent des avertissements, le programme
    reste utilisable meme imparfait -- regle generale deja appliquee
    partout ailleurs dans Fitapp (ne jamais faire echouer une
    recommandation faute de donnee ou de cas limite).
    """

    warnings: list[str] = []

    training_days = [d for d in days if d["day_type"] == "training"]
    if len(training_days) != frequency_per_week:
        warnings.append(
            f"Frequence visee {frequency_per_week}x/semaine, "
            f"{len(training_days)} jour(s) d'entrainement generes."
        )

    consecutive_high_intensity = 0
    for day in days:
        if day["day_type"] == "training" and day["workout"]["target_rpe"] >= HIGH_INTENSITY_RPE_THRESHOLD:
            consecutive_high_intensity += 1
            if consecutive_high_intensity >= 3:
                warnings.append(
                    f"{day['day_label']} : au moins 3 jours d'entrainement a forte "
                    "intensite proches les uns des autres, risque de surcharge "
                    "(partie 38 : privilegier la progressivite)."
                )
        else:
            consecutive_high_intensity = 0

    return {"valid": True, "warnings": warnings}


# ============================================================
# WEEKLY SCHEDULER (partie 15-17)
# ============================================================

def generate_weekly_program(
    db: Session,
    user_id: uuid.UUID,
    goal: Optional[GoalType] = None,
) -> dict:
    """
    Programme de 7 jours, regenere dynamiquement a chaque appel (partie
    6 : jamais de programme stocke par combinaison). Fonctionne aussi
    pour un utilisateur non-sportif (frequence par defaut, seances
    generiques via recommend_workout, jamais d'erreur -- partie 11).
    """

    primary = get_primary_sport(db, user_id)
    frequency_per_week = (
        primary.frequency_per_week
        if primary and primary.frequency_per_week
        else DEFAULT_FREQUENCY_PER_WEEK
    )

    # Sequence ordonnee des themes de la semaine (Branches 1-6 du
    # programme), sensible a la frequence ET au niveau -- remplace la
    # simple rotation cyclique par sport/objectif utilisee auparavant.
    # Longueur toujours egale a frequency_per_week (meme valeur que
    # celle utilisee ci-dessous pour repartir les jours d'entrainement).
    activity_level = _activity_level_for_user(db, user_id)
    sport_slug = primary.sport.slug if primary and primary.sport else None
    level = primary.level if primary else None
    day_sequence = build_training_day_sequence(
        sport_slug, activity_level, level, frequency_per_week, goal
    )

    training_day_indices = set(_spaced_training_days(frequency_per_week))
    weight_kg = _weight_kg_for_user(db, user_id)

    current_recovery = compute_recovery_score(db, user_id)["recovery_fraction"]
    if current_recovery is None:
        current_recovery = STARTING_RECOVERY

    days: list[dict] = []
    conflict_warnings: list[str] = []
    previous_was_high_intensity = False
    previous_dominant_type = None
    training_session_counter = 0
    previous_training_exercise_ids: set[uuid.UUID] = set()

    for day_index in range(7):
        if day_index not in training_day_indices:
            days.append(_build_rest_day(db, day_index, sport_slug))
            current_recovery = min(RECOVERY_CEILING, current_recovery + RECOVERY_GAIN_AFTER_REST)
            previous_was_high_intensity = False
            previous_dominant_type = None
            continue

        day_theme = day_sequence[training_session_counter % len(day_sequence)]

        workout = recommend_workout(
            db,
            user_id,
            goal=goal,
            recovery_score=current_recovery,
            session_index=training_session_counter,
            exclude_exercise_ids=previous_training_exercise_ids,
            theme=day_theme,
        )
        is_high_intensity = workout["target_rpe"] >= HIGH_INTENSITY_RPE_THRESHOLD
        same_load_type_as_previous = (
            previous_dominant_type in LOAD_BASED_TYPES
            and workout["training_type"] in LOAD_BASED_TYPES
        )

        if previous_was_high_intensity and (is_high_intensity or same_load_type_as_previous):
            # Conflit (partie 17) : on redemande une seance en simulant
            # une recuperation deja degradee, pour obtenir une variante
            # plus legere/differente sans dupliquer la logique
            # d'intensite de recommend_workout().
            conflict_warnings.append(
                f"{DAY_LABELS[day_index]} : conflit detecte (intensite ou groupe "
                "d'exercices a charge repete par rapport a la veille), seance "
                "regeneree avec une recuperation simulee plus basse."
            )
            adjusted_recovery = max(RECOVERY_FLOOR, current_recovery - RECOVERY_DROP_AFTER_HIGH_INTENSITY)
            workout = recommend_workout(
                db,
                user_id,
                goal=goal,
                recovery_score=adjusted_recovery,
                session_index=training_session_counter,
                exclude_exercise_ids=previous_training_exercise_ids,
                theme=day_theme,
            )
            is_high_intensity = workout["target_rpe"] >= HIGH_INTENSITY_RPE_THRESHOLD

        workout = _fill_calories(workout, weight_kg)

        days.append(
            {
                "day_label": DAY_LABELS[day_index],
                "day_type": "training",
                "workout": workout,
            }
        )

        training_session_counter += 1
        previous_training_exercise_ids = {
            item["exercise"].id for item in workout.get("exercises", []) if item.get("exercise")
        }
        drop = RECOVERY_DROP_AFTER_HIGH_INTENSITY if is_high_intensity else RECOVERY_DROP_AFTER_TRAINING
        current_recovery = max(RECOVERY_FLOOR, current_recovery - drop)
        previous_was_high_intensity = is_high_intensity
        previous_dominant_type = workout["training_type"]

    validation = validate_weekly_program(days, frequency_per_week)
    validation["warnings"] = conflict_warnings + validation["warnings"]

    total_calories = round(
        sum(
            (d["workout"]["estimated_calories_kcal"] or 0)
            for d in days
            if d["day_type"] == "training"
        ),
        1,
    )

    return {
        "sport_slug": primary.sport.slug if primary and primary.sport else None,
        "goal": goal,
        "frequency_per_week": frequency_per_week,
        "days": days,
        "estimated_weekly_calories_kcal": total_calories,
        "nutrition_focus": get_nutrition_focus(db, user_id),
        "validation": validation,
    }
