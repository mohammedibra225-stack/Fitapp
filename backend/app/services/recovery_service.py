"""
Recovery Score (module Sport, partie 10).

Combine sommeil, fatigue ressentie, charge d'entrainement recente et
repos en un score unique 0-100, destine a etre branche sur le
recovery_score (0-1) deja accepte par recommend_workout() (etape 6) et
suggest_exercise_progression() (etape 7) -- ces deux fonctions n'ont
donc pas besoin d'etre modifiees : elles attendent deja ce parametre en
placeholder, c'est aux routes de l'etape 10 de faire le lien
(compute_recovery_score(...)["recovery_fraction"] -> recovery_score=...).

    Recovery Score = sommeil x 40% + fatigue x 25% + charge recente x 20% + repos x 15%

Classification (reprend RecoveryLevel, app/models/enums.py) :
    80-100 -> NORMAL        (aucune restriction)
    60-79  -> MODERATE
    40-59  -> REDUCE        (reduire l'intensite)
    0-39   -> REST_NEEDED   (recuperation / repos)

HYPOTHESES A VALIDER (SleepLog.fatigue_level/stress_level sont "libres
cote app", sans convention fixee dans le modele) :
    - fatigue_level : 1 = tres peu fatigue (bien), 5 = tres fatigue
      (mal). Si ton app utilise l'echelle inverse, inverser
      _fatigue_score() (une seule ligne a changer).
    - stress_level n'est PAS utilise dans le score : la formule
      officielle du cahier des charges ne le liste pas. Disponible pour
      affiner plus tard si tu veux l'integrer.
    - "repos" est approxime par le nombre de jours SANS seance loguee
      sur les 7 derniers jours (rest_days = 7 - sessions_last_7j, borne
      a [0,7]) : simple, mais suppose au plus une seance par jour.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RecoveryLevel, SleepQuality
from app.models.recovery import SleepLog
from app.services.training_service import get_primary_sport, get_recent_training_load

# ============================================================
# POIDS DU SCORE (configurables, doivent totaliser 1.0)
# ============================================================

RECOVERY_WEIGHTS = {
    "sleep": 0.40,
    "fatigue": 0.25,
    "training_load": 0.20,
    "rest": 0.15,
}

NEUTRAL_SUBSCORE = 50.0  # sur 100, utilise quand une donnee manque

TARGET_SLEEP_MINUTES = 480  # 8h, base raisonnable et ajustable

QUALITY_POINTS: dict[SleepQuality, float] = {
    SleepQuality.POOR: 25.0,
    SleepQuality.FAIR: 50.0,
    SleepQuality.GOOD: 75.0,
    SleepQuality.EXCELLENT: 100.0,
}

DEFAULT_EXPECTED_FREQUENCY_PER_WEEK = 3  # si aucun UserSport.frequency_per_week

# Classification -> RecoveryLevel (module Sport, partie 10), teste dans
# l'ordre decroissant : le premier seuil atteint ou depasse l'emporte.
RECOVERY_LEVEL_THRESHOLDS: list[tuple[int, RecoveryLevel]] = [
    (80, RecoveryLevel.NORMAL),
    (60, RecoveryLevel.MODERATE),
    (40, RecoveryLevel.REDUCE),
    (0, RecoveryLevel.REST_NEEDED),
]


# ============================================================
# LECTURE DU SOMMEIL
# ============================================================

def get_latest_sleep_log(
    db: Session, user_id: uuid.UUID, before: Optional[date] = None
) -> Optional[SleepLog]:
    """Le SleepLog le plus recent de l'utilisateur (a la date `before`
    incluse si fournie, sinon le plus recent tout court)."""

    query = select(SleepLog).where(SleepLog.user_id == user_id)
    if before is not None:
        query = query.where(SleepLog.sleep_date <= before)
    query = query.order_by(SleepLog.sleep_date.desc()).limit(1)

    return db.execute(query).scalars().first()


# ============================================================
# SOUS-SCORES (0-100)
# ============================================================

def _sleep_score(sleep_log: Optional[SleepLog]) -> float:
    if sleep_log is None:
        return NEUTRAL_SUBSCORE

    duration_score = None
    if sleep_log.duration_minutes is not None:
        duration_score = min(100.0, (sleep_log.duration_minutes / TARGET_SLEEP_MINUTES) * 100)

    quality_score = QUALITY_POINTS.get(sleep_log.quality) if sleep_log.quality else None

    scores = [s for s in (duration_score, quality_score) if s is not None]
    return sum(scores) / len(scores) if scores else NEUTRAL_SUBSCORE


def _fatigue_score(sleep_log: Optional[SleepLog]) -> float:
    """1 = tres peu fatigue -> 100, 5 = tres fatigue -> 0 (voir
    HYPOTHESES en tete de fichier)."""

    if sleep_log is None or sleep_log.fatigue_level is None:
        return NEUTRAL_SUBSCORE
    level = max(1, min(5, sleep_log.fatigue_level))
    return (5 - level) / 4 * 100


def _training_load_score(
    db: Session, user_id: uuid.UUID, expected_frequency: Optional[int]
) -> tuple[float, dict]:
    """
    Plus la charge recente (frequence + intensite ressentie sur 7
    jours) est haute par rapport a l'habitude de l'utilisateur, plus ce
    sous-score baisse -- la seule composante du Recovery Score qui
    vient du module Sport lui-meme, les 3 autres venant du sommeil.
    """

    load = get_recent_training_load(db, user_id, days=7)
    frequency = expected_frequency or DEFAULT_EXPECTED_FREQUENCY_PER_WEEK

    ratio = load["total_sessions"] / frequency if frequency else 0
    score = 100 - min(100.0, ratio * 50)

    if load["average_rpe"] is not None:
        score -= max(0.0, load["average_rpe"] - 6) * 10

    return max(0.0, min(100.0, score)), load


def _rest_score(load: dict) -> float:
    """Approxime le repos par le nombre de jours sans seance sur les 7
    derniers jours (hypothese : au plus une seance loguee par jour)."""

    sessions = load["total_sessions"]
    rest_days = max(0, min(7, 7 - sessions))
    return (rest_days / 7) * 100


# ============================================================
# CLASSIFICATION
# ============================================================

def _classify(score: float) -> RecoveryLevel:
    for threshold, level in RECOVERY_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RecoveryLevel.REST_NEEDED


# ============================================================
# RECOVERY SCORE GLOBAL
# ============================================================

def compute_recovery_score(
    db: Session, user_id: uuid.UUID, on_date: Optional[date] = None
) -> dict:
    """
    Recovery Score complet (module Sport, partie 10). Le champ
    `recovery_fraction` (0-1) est ce qu'il faut passer tel quel au
    parametre recovery_score de recommend_workout() (etape 6) et
    suggest_exercise_progression() (etape 7 -- via une extension future
    si besoin, actuellement suggest_exercise_progression() ne prend pas
    encore ce parametre car il n'etait pas dans le cahier des charges
    de l'etape 7).

    Fonctionne meme sans aucune donnee de sommeil/entrainement : les
    sous-scores manquants retombent sur NEUTRAL_SUBSCORE, jamais
    d'erreur (meme regle que tout le module Sport).
    """

    on_date = on_date or date.today()

    sleep_log = get_latest_sleep_log(db, user_id, before=on_date)

    primary = get_primary_sport(db, user_id)
    expected_frequency = primary.frequency_per_week if primary else None

    sleep = _sleep_score(sleep_log)
    fatigue = _fatigue_score(sleep_log)
    training_load, load_summary = _training_load_score(db, user_id, expected_frequency)
    rest = _rest_score(load_summary)

    breakdown = {
        "sleep": round(sleep, 1),
        "fatigue": round(fatigue, 1),
        "training_load": round(training_load, 1),
        "rest": round(rest, 1),
    }

    total = sum(breakdown[key] * weight for key, weight in RECOVERY_WEIGHTS.items())
    total = round(max(0.0, min(100.0, total)), 1)

    return {
        "score": total,
        "level": _classify(total),
        "recovery_fraction": round(total / 100, 3),
        "breakdown": breakdown,
        "sleep_log_found": sleep_log is not None,
        "training_load_summary": load_summary,
    }
