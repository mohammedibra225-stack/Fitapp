"""
Daily Health / Lifestyle Score + activites recommandees pour les
non-sportifs (module Sport, parties 13 et 14).

Combine plusieurs modules deja existants en un score quotidien unique,
SANS dupliquer leur logique :
    - nutrition   : calculate_calories() (app/services/nutrition.py) +
                    somme des Meal du jour (meme requete que
                    routes/nutrition_tracking.py:get_daily_summary)
    - hydration   : calculate_water_goal_ml() (app/services/hydration.py)
                    + somme des WaterLog du jour
    - activite    : DailyActivityLog (pas) + WorkoutLog (seance structuree)
    - sommeil     : SleepLog, via get_latest_sleep_log() de
                    recovery_service.py (reutilise, pas redefini)
    - recuperation: compute_recovery_score() (app/services/recovery_service.py)
    - consistance : proportion de jours des 7 derniers avec au moins une
                    donnee loguee (repas, eau, activite, sommeil ou seance)

    Lifestyle Score = nutrition x 35% + hydration x 20% + activity x 15%
                     + sleep x 15% + consistency x 10% + recovery x 5%

IMPORTANT (module Sport, partie 13) : ce score est uniquement un
indicateur de progression dans Fitapp, jamais un diagnostic medical --
le champ `disclaimer` le rappelle explicitement dans chaque reponse.

Fonctionne aussi bien pour un sportif que pour un non-sportif (sport =
none) : chaque sous-score retombe sur une valeur neutre si la donnee
correspondante manque, jamais d'erreur (meme regle que tout le module
Sport).
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.hydration import WaterLog
from app.models.lifestyle import DailyActivityLog, LifestyleProfile
from app.models.meal import Meal
from app.models.profile import Profile
from app.models.training_log import WorkoutLog
from app.services.hydration import calculate_water_goal_ml
from app.services.nutrition import calculate_calories
from app.services.recovery_service import compute_recovery_score, get_latest_sleep_log

# ============================================================
# POIDS DU SCORE (configurables, doivent totaliser 1.0 -- partie 13)
# ============================================================

LIFESTYLE_SCORE_WEIGHTS = {
    "nutrition": 0.35,
    "hydration": 0.20,
    "activity": 0.15,
    "sleep": 0.15,
    "consistency": 0.10,
    "recovery": 0.05,
}

NEUTRAL_SUBSCORE = 50.0  # utilise quand une donnee manque, ni penalise ni favorise

DEFAULT_STEPS_TARGET = 8000  # si LifestyleProfile.daily_steps_target absent
DEFAULT_SLEEP_TARGET_MINUTES = 480  # 8h, si LifestyleProfile.sleep_target_minutes absent

CONSISTENCY_WINDOW_DAYS = 7

# Classification indicative (partie 13), jamais un diagnostic medical.
LIFESTYLE_SCORE_LEVEL_THRESHOLDS: list[tuple[int, str]] = [
    (80, "excellent"),
    (60, "good"),
    (40, "fair"),
    (0, "low"),
]

DISCLAIMER = (
    "Ce score est un indicateur de progression dans Fitapp, "
    "pas un diagnostic medical."
)


def _classify(score: float) -> str:
    for threshold, level in LIFESTYLE_SCORE_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "low"


# ============================================================
# SOUS-SCORE NUTRITION
# ============================================================

def _get_daily_meal_totals(db: Session, user_id: uuid.UUID, on_date: date) -> Decimal:
    return db.execute(
        select(func.coalesce(func.sum(Meal.total_calories_kcal), 0)).where(
            Meal.user_id == user_id, Meal.consumed_on == on_date
        )
    ).scalar_one()


def _nutrition_score(db: Session, profile: Optional[Profile], on_date: date, user_id: uuid.UUID) -> float:
    """
    100 quand les calories consommees sont proches de l'objectif calcule
    (calculate_calories), decroit lineairement au-dela d'un ecart de 30%
    dans un sens ou dans l'autre. NEUTRAL_SUBSCORE si le profil est
    incomplet (jamais bloquant).
    """

    if profile is None or any(
        getattr(profile, f) is None
        for f in ("age", "sex", "height_cm", "current_weight_kg", "activity_level", "primary_goal")
    ):
        return NEUTRAL_SUBSCORE

    target = calculate_calories(
        weight_kg=float(profile.current_weight_kg),
        height_cm=float(profile.height_cm),
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal=profile.primary_goal,
    )["daily_calories"]

    consumed = float(_get_daily_meal_totals(db, user_id, on_date))
    if target <= 0:
        return NEUTRAL_SUBSCORE
    if consumed == 0:
        return 0.0

    deviation = abs(consumed - target) / target
    # 0% d'ecart -> 100, 30%+ d'ecart -> 0, lineaire entre les deux.
    score = 100 * (1 - min(1.0, deviation / 0.30))
    return round(max(0.0, score), 1)


# ============================================================
# SOUS-SCORE HYDRATATION
# ============================================================

def _hydration_score(db: Session, profile: Optional[Profile], on_date: date, user_id: uuid.UUID) -> float:
    if profile is None or profile.current_weight_kg is None or profile.activity_level is None:
        return NEUTRAL_SUBSCORE

    goal_ml = calculate_water_goal_ml(
        weight_kg=float(profile.current_weight_kg),
        activity_level=profile.activity_level,
    )
    consumed_ml = db.execute(
        select(func.coalesce(func.sum(WaterLog.quantity_ml), 0))
        .where(WaterLog.user_id == user_id, WaterLog.logged_on == on_date)
    ).scalar_one()

    if goal_ml <= 0:
        return NEUTRAL_SUBSCORE
    return round(min(100.0, (int(consumed_ml) / goal_ml) * 100), 1)


# ============================================================
# SOUS-SCORE ACTIVITE (partie 12 : distinct du sport structure)
# ============================================================

def _activity_score(
    db: Session, lifestyle_profile: Optional[LifestyleProfile], on_date: date, user_id: uuid.UUID
) -> float:
    steps_target = (
        lifestyle_profile.daily_steps_target
        if lifestyle_profile and lifestyle_profile.daily_steps_target
        else DEFAULT_STEPS_TARGET
    )

    activity_log = db.execute(
        select(DailyActivityLog).where(
            DailyActivityLog.user_id == user_id, DailyActivityLog.log_date == on_date
        )
    ).scalar_one_or_none()

    has_workout = db.execute(
        select(WorkoutLog.id)
        .where(WorkoutLog.user_id == user_id, func.date(WorkoutLog.performed_at) == on_date)
        .limit(1)
    ).scalar_one_or_none() is not None

    steps_score = None
    if activity_log is not None and activity_log.steps is not None and steps_target > 0:
        steps_score = min(100.0, (activity_log.steps / steps_target) * 100)

    workout_score = 90.0 if has_workout else None

    scores = [s for s in (steps_score, workout_score) if s is not None]
    return round(sum(scores) / len(scores), 1) if scores else NEUTRAL_SUBSCORE


# ============================================================
# SOUS-SCORE SOMMEIL
# ============================================================

def _sleep_score(
    db: Session, lifestyle_profile: Optional[LifestyleProfile], on_date: date, user_id: uuid.UUID
) -> float:
    sleep_log = get_latest_sleep_log(db, user_id, before=on_date)
    if sleep_log is None or sleep_log.duration_minutes is None:
        return NEUTRAL_SUBSCORE

    target = (
        lifestyle_profile.sleep_target_minutes
        if lifestyle_profile and lifestyle_profile.sleep_target_minutes
        else DEFAULT_SLEEP_TARGET_MINUTES
    )
    if target <= 0:
        return NEUTRAL_SUBSCORE
    return round(min(100.0, (sleep_log.duration_minutes / target) * 100), 1)


# ============================================================
# SOUS-SCORE CONSISTANCE
# ============================================================

def _has_any_log_on(db: Session, user_id: uuid.UUID, on_date: date) -> bool:
    checks = [
        select(Meal.id).where(Meal.user_id == user_id, Meal.consumed_on == on_date),
        select(WaterLog.id).where(WaterLog.user_id == user_id, WaterLog.logged_on == on_date),
        select(DailyActivityLog.id).where(
            DailyActivityLog.user_id == user_id, DailyActivityLog.log_date == on_date
        ),
        select(WorkoutLog.id).where(
            WorkoutLog.user_id == user_id, func.date(WorkoutLog.performed_at) == on_date
        ),
    ]
    for query in checks:
        if db.execute(query.limit(1)).scalar_one_or_none() is not None:
            return True
    return False


def _consistency_score(db: Session, user_id: uuid.UUID, on_date: date) -> float:
    days_with_data = sum(
        1
        for offset in range(CONSISTENCY_WINDOW_DAYS)
        if _has_any_log_on(db, user_id, on_date - timedelta(days=offset))
    )
    return round((days_with_data / CONSISTENCY_WINDOW_DAYS) * 100, 1)


# ============================================================
# SCORE GLOBAL
# ============================================================

def compute_daily_lifestyle_score(
    db: Session, user_id: uuid.UUID, on_date: Optional[date] = None
) -> dict:
    """Daily Health Score complet (module Sport, partie 13). Ne leve
    jamais d'erreur : chaque sous-score manquant retombe sur
    NEUTRAL_SUBSCORE, y compris pour un profil totalement vide."""

    on_date = on_date or date.today()

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()
    lifestyle_profile = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user_id)
    ).scalar_one_or_none()

    breakdown = {
        "nutrition": _nutrition_score(db, profile, on_date, user_id),
        "hydration": _hydration_score(db, profile, on_date, user_id),
        "activity": _activity_score(db, lifestyle_profile, on_date, user_id),
        "sleep": _sleep_score(db, lifestyle_profile, on_date, user_id),
        "consistency": _consistency_score(db, user_id, on_date),
        "recovery": compute_recovery_score(db, user_id, on_date=on_date)["recovery_fraction"] * 100,
    }

    total = sum(breakdown[key] * weight for key, weight in LIFESTYLE_SCORE_WEIGHTS.items())
    total = round(max(0.0, min(100.0, total)), 1)

    return {
        "date": on_date.isoformat(),
        "score": total,
        "level": _classify(total),
        "breakdown": {k: round(v, 1) for k, v in breakdown.items()},
        "disclaimer": DISCLAIMER,
    }


# ============================================================
# ACTIVITES RECOMMANDEES POUR NON-SPORTIFS (partie 14)
# ============================================================
# Recommandations facultatives, jamais des obligations (partie 14) :
# consultees seulement si LifestyleProfile.wants_activity_suggestions
# est vrai (ou si aucun profil n'existe encore -> comportement par
# defaut, cf. LifestyleProfile.wants_activity_suggestions=True).

SUGGESTED_ACTIVITIES = [
    {"slug": "marche_10", "label": "Marche 10 min", "duration_minutes": 10},
    {"slug": "marche_15", "label": "Marche 15 min", "duration_minutes": 15},
    {"slug": "marche_30", "label": "Marche 30 min", "duration_minutes": 30},
    {"slug": "mobilite_10", "label": "Mobilite 10 min", "duration_minutes": 10},
    {"slug": "etirements_10", "label": "Etirements 10 min", "duration_minutes": 10},
    {"slug": "petite_promenade", "label": "Petite promenade", "duration_minutes": None},
    {"slug": "repos", "label": "Repos", "duration_minutes": None},
]


def get_suggested_activities(
    db: Session, user_id: uuid.UUID, on_date: Optional[date] = None
) -> list[dict]:
    """Suggestions d'activites facultatives (partie 14). Liste vide si
    l'utilisateur a explicitement desactive ces suggestions -- jamais
    une erreur, jamais une obligation."""

    lifestyle_profile = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user_id)
    ).scalar_one_or_none()

    if lifestyle_profile is not None and not lifestyle_profile.wants_activity_suggestions:
        return []

    return SUGGESTED_ACTIVITIES


# ============================================================
# RESUME "AUJOURD'HUI" (activite quotidienne + suggestions)
# ============================================================

def get_daily_lifestyle_summary(
    db: Session, user_id: uuid.UUID, on_date: Optional[date] = None
) -> dict:
    """Regroupe l'activite quotidienne loguee (partie 12) et les
    suggestions facultatives (partie 14) pour un affichage 'aujourd'hui'."""

    on_date = on_date or date.today()

    activity_log = db.execute(
        select(DailyActivityLog).where(
            DailyActivityLog.user_id == user_id, DailyActivityLog.log_date == on_date
        )
    ).scalar_one_or_none()

    has_workout = db.execute(
        select(WorkoutLog.id)
        .where(WorkoutLog.user_id == user_id, func.date(WorkoutLog.performed_at) == on_date)
        .limit(1)
    ).scalar_one_or_none() is not None

    return {
        "date": on_date.isoformat(),
        "activity": {
            "steps": activity_log.steps if activity_log else None,
            "walking_duration_minutes": activity_log.walking_duration_minutes if activity_log else None,
            "distance_m": float(activity_log.distance_m) if activity_log and activity_log.distance_m is not None else None,
            "active_minutes": activity_log.active_minutes if activity_log else None,
        },
        "has_structured_workout_today": has_workout,
        "suggested_activities": get_suggested_activities(db, user_id, on_date),
    }
