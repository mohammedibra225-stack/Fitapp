"""
Algorithme de progression (module Sport, partie 9).

S'appuie sur l'historique REEL des seances (training_log.py) pour
suggerer, exercice par exercice, l'ajustement a appliquer la prochaine
fois : charge pour les exercices "a charge" (musculation), duree/
distance pour les autres (course, velo, natation, ou tout futur sport
d'endurance -- meme logique, extensible sans modification, regle
partie 9 : "Le systeme doit etre extensible aux autres sports").

Reutilise is_load_based() de training_recommender.py pour ne pas
dupliquer la distinction charge/duree deja etablie a l'etape 6.

Convention RPE (module Sport, partie 8) :
    RPE <= 7            -> gere facilement -> petite augmentation
    RPE == 8 (ou 7-9)   -> effort cible atteint -> conserver
    RPE >= 9            -> tres difficile -> conserver ou reduire, jamais augmenter
    Echec repete (RPE >= 9 sur les 2 dernieres seances) -> reduire

LIMITE ASSUMEE : WorkoutLogSet enregistre ce qui a ete REELLEMENT fait
(reps, charge, duree, distance, RPE), pas d'objectif cible ni de flag
"reussi/echec" explicite (contrairement a l'ExerciseLog.completed du
cahier des charges, absent du modele actuel). "Reussi" est donc deduit
du RPE ressenti sur la derniere seance, pas d'une comparaison a un
objectif -- a affiner si target_reps/target_duration sont un jour aussi
loggues cote WorkoutLogSet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.training import Exercise
from app.models.training_log import WorkoutLog, WorkoutLogExercise, WorkoutLogSet
from app.services.training_recommender import is_load_based

# ============================================================
# PARAMETRES DE PROGRESSION (configurables)
# ============================================================

# Charge : on augmente du plus grand des deux (mini absolu ou % de la
# charge actuelle), pour rester pertinent aussi bien a 20kg qu'a 150kg.
LOAD_INCREMENT_KG = Decimal("2.5")
LOAD_INCREMENT_RATIO = Decimal("0.025")
LOAD_DECREMENT_RATIO = Decimal("0.05")

# Duree/distance (endurance) : ajustement en pourcentage de la derniere
# seance loguee.
ENDURANCE_INCREMENT_RATIO = 0.05
ENDURANCE_DECREMENT_RATIO = 0.10

REPEATED_FAILURE_RPE_THRESHOLD = Decimal("9")
REPEATED_FAILURE_SESSION_COUNT = 2

DEFAULT_HISTORY_SESSIONS = 5


# ============================================================
# HISTORIQUE PAR EXERCICE
# ============================================================

def get_exercise_session_history(
    db: Session, user_id: uuid.UUID, exercise_id: uuid.UUID, limit: int = DEFAULT_HISTORY_SESSIONS
) -> list[WorkoutLogExercise]:
    """
    Les `limit` dernieres occurrences loguees de cet exercice pour cet
    utilisateur, de la plus recente a la plus ancienne.
    """

    return (
        db.execute(
            select(WorkoutLogExercise)
            .join(WorkoutLog, WorkoutLogExercise.workout_log_id == WorkoutLog.id)
            .options(selectinload(WorkoutLogExercise.sets))
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLogExercise.exercise_id == exercise_id,
            )
            .order_by(WorkoutLog.performed_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def get_last_workout_log(db: Session, user_id: uuid.UUID) -> Optional[WorkoutLog]:
    """La toute derniere seance loguee de l'utilisateur, toutes seances
    confondues (utilise pour proposer une progression sans devoir
    connaitre les exercise_id a l'avance)."""

    return (
        db.execute(
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercises))
            .where(WorkoutLog.user_id == user_id)
            .order_by(WorkoutLog.performed_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


# ============================================================
# LECTURE DU RPE / DETECTION D'ECHEC REPETE
# ============================================================

def _session_average_rpe(session: WorkoutLogExercise) -> Optional[Decimal]:
    values = [s.rpe for s in session.sets if s.rpe is not None]
    if not values:
        return None
    return sum((Decimal(str(v)) for v in values), Decimal("0")) / len(values)


def _is_repeated_failure(history: list[WorkoutLogExercise]) -> bool:
    """
    Echec repete (module Sport, partie 9) : les
    REPEATED_FAILURE_SESSION_COUNT dernieres seances ont toutes un RPE
    moyen au maximum (>= 9) -- signe qu'il faut reduire plutot
    qu'insister sur la charge/duree actuelle.
    """

    recent = history[:REPEATED_FAILURE_SESSION_COUNT]
    if len(recent) < REPEATED_FAILURE_SESSION_COUNT:
        return False
    averages = [_session_average_rpe(s) for s in recent]
    return all(avg is not None and avg >= REPEATED_FAILURE_RPE_THRESHOLD for avg in averages)


def _progression_tier(avg_rpe: Optional[Decimal]) -> str:
    """
    'increase'           -> RPE <= 7
    'maintain'            -> 7 < RPE < 9 (couvre RPE = 8)
    'maintain_or_reduce'  -> RPE >= 9
    'insufficient_data'   -> pas de RPE loggue sur la derniere seance
    """

    if avg_rpe is None:
        return "insufficient_data"
    if avg_rpe <= 7:
        return "increase"
    if avg_rpe < 9:
        return "maintain"
    return "maintain_or_reduce"


# ============================================================
# SUGGESTION DE PROGRESSION, PAR EXERCICE
# ============================================================

def _last_working_set(session: WorkoutLogExercise) -> Optional[WorkoutLogSet]:
    """La derniere serie loguee de la seance (la plus representative de
    l'effort final, ex: le dernier top-set)."""

    return session.sets[-1] if session.sets else None


def _load_targets(session: WorkoutLogExercise, action: str) -> dict:
    working_set = _last_working_set(session)
    last_weight = working_set.weight_kg if working_set else None
    last_reps = working_set.reps if working_set else None

    next_weight = last_weight
    if action == "increase" and last_weight is not None:
        last_weight_dec = Decimal(str(last_weight))
        increment = max(LOAD_INCREMENT_KG, last_weight_dec * LOAD_INCREMENT_RATIO)
        next_weight = round(last_weight_dec + increment, 2)
    elif action == "reduce" and last_weight is not None:
        next_weight = round(Decimal(str(last_weight)) * (1 - LOAD_DECREMENT_RATIO), 2)

    return {
        "metric": "load",
        "last_weight_kg": float(last_weight) if last_weight is not None else None,
        "last_reps": last_reps,
        "next_target_weight_kg": float(next_weight) if next_weight is not None else None,
    }


def _endurance_targets(session: WorkoutLogExercise, action: str) -> dict:
    working_set = _last_working_set(session)
    last_duration = working_set.duration_seconds if working_set else None
    last_distance = float(working_set.distance_m) if working_set and working_set.distance_m is not None else None

    ratio = None
    if action == "increase":
        ratio = 1 + ENDURANCE_INCREMENT_RATIO
    elif action == "reduce":
        ratio = 1 - ENDURANCE_DECREMENT_RATIO

    next_duration = round(last_duration * ratio) if (last_duration is not None and ratio is not None) else last_duration
    next_distance = round(last_distance * ratio, 1) if (last_distance is not None and ratio is not None) else last_distance

    average_speed_mps = (
        round(last_distance / last_duration, 3) if last_duration and last_distance else None
    )

    return {
        "metric": "duration_distance",
        "last_duration_seconds": last_duration,
        "last_distance_m": last_distance,
        "average_speed_mps": average_speed_mps,
        "next_target_duration_seconds": next_duration,
        "next_target_distance_m": next_distance,
    }


def suggest_exercise_progression(
    db: Session,
    user_id: uuid.UUID,
    exercise_id: uuid.UUID,
    sessions: int = DEFAULT_HISTORY_SESSIONS,
) -> dict:
    """
    Suggestion de progression pour UN exercice (module Sport, partie 9),
    basee sur son historique reel. Fonctionne pour tout sport : charge
    pour les exercices "a charge" (musculation), duree/distance pour les
    autres (course, velo, natation...) -- meme logique de tiers RPE dans
    les deux cas, seule la nature de la cible change.
    """

    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise ValueError(f"Exercice introuvable : {exercise_id}")

    history = get_exercise_session_history(db, user_id, exercise_id, limit=sessions)

    if not history:
        return {
            "exercise_id": exercise_id,
            "exercise_slug": exercise.slug,
            "status": "no_history",
            "action": "maintain",
            "reason": "Aucune seance loguee pour cet exercice -- pas assez de donnees pour progresser.",
        }

    last_session = history[0]
    avg_rpe = _session_average_rpe(last_session)
    tier = _progression_tier(avg_rpe)
    repeated_failure = _is_repeated_failure(history)

    if repeated_failure:
        action = "reduce"
        reason = (
            f"RPE >= 9 sur les {REPEATED_FAILURE_SESSION_COUNT} dernieres seances : "
            "echec repete, on reduit plutot que d'insister."
        )
    elif tier == "increase":
        action = "increase"
        reason = f"Derniere seance geree facilement (RPE moyen {avg_rpe}), on augmente legerement."
    elif tier == "maintain":
        action = "maintain"
        reason = f"Effort cible atteint (RPE moyen {avg_rpe}), on conserve la charge/duree actuelle."
    elif tier == "maintain_or_reduce":
        action = "maintain"  # prudence : jamais d'augmentation sur une seance tres difficile
        reason = f"Seance tres difficile (RPE moyen {avg_rpe}) mais pas encore repetee : on ne progresse pas cette fois."
    else:
        action = "maintain"
        reason = "Aucun RPE loggue sur la derniere seance -- on conserve par prudence."

    suggestion = {
        "exercise_id": exercise_id,
        "exercise_slug": exercise.slug,
        "status": "ok",
        "sessions_considered": len(history),
        "last_average_rpe": float(avg_rpe) if avg_rpe is not None else None,
        "action": action,
        "reason": reason,
    }

    if is_load_based(exercise):
        suggestion.update(_load_targets(last_session, action))
    else:
        suggestion.update(_endurance_targets(last_session, action))

    return suggestion


def suggest_progression_for_last_workout(db: Session, user_id: uuid.UUID) -> list[dict]:
    """
    Une suggestion de progression pour chaque exercice de la toute
    derniere seance loguee de l'utilisateur -- pratique pour preparer
    "la prochaine fois" sans devoir connaitre les exercise_id a
    l'avance. Retourne une liste vide si l'utilisateur n'a encore rien
    logue (jamais d'erreur, meme regle que le reste du module Sport).
    """

    last_log = get_last_workout_log(db, user_id)
    if last_log is None:
        return []

    exercise_ids = {we.exercise_id for we in last_log.exercises}
    return [suggest_exercise_progression(db, user_id, exercise_id) for exercise_id in exercise_ids]
