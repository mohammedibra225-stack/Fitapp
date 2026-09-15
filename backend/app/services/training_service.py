"""
Fonctions de base du module Sport, reutilisees par les services de
recommandation (etape 6), de progression (etape 7) et de recuperation
(etape 8) : acces au profil sportif, historique des seances, calcul de
volume d'entrainement.

Convention : fonctions pures ou prenant une Session SQLAlchemy en
parametre (meme approche que app/services/meal_calculator.py), pas de
logique HTTP ici -- les routes (etape 10) appelleront ces fonctions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.goals import Goal, SportGoalMatrix
from app.models.sport import Sport, UserSport
from app.models.training import Exercise
from app.models.training_log import WorkoutLog, WorkoutLogExercise, WorkoutLogSet


# ============================================================
# PROFIL SPORTIF DE L'UTILISATEUR
# ============================================================

def get_user_sports(db: Session, user_id: uuid.UUID) -> list[UserSport]:
    """Tous les sports pratiques par l'utilisateur (module Sport, partie 1)."""

    return (
        db.execute(
            select(UserSport)
            .options(selectinload(UserSport.sport))
            .where(UserSport.user_id == user_id)
        )
        .scalars()
        .all()
    )


def get_primary_sport(db: Session, user_id: uuid.UUID) -> Optional[UserSport]:
    """
    Le sport principal de l'utilisateur, ou None si aucun sport n'est
    pratique (sport = none, module Sport, partie 11 : jamais une erreur).
    """

    return (
        db.execute(
            select(UserSport)
            .options(selectinload(UserSport.sport))
            .where(UserSport.user_id == user_id, UserSport.is_primary.is_(True))
        )
        .scalars()
        .first()
    )


def set_user_sport(
    db: Session,
    user_id: uuid.UUID,
    sport_slug: str,
    level=None,
    frequency_per_week: Optional[int] = None,
    is_primary: bool = False,
) -> UserSport:
    """
    Ajoute ou met a jour la pratique d'un sport pour l'utilisateur (upsert
    sur la contrainte unique user_id+sport_id). Si is_primary=True, retire
    le statut principal des autres sports de l'utilisateur (un seul sport
    principal a la fois, module Sport, partie 1).
    """

    sport = db.execute(select(Sport).where(Sport.slug == sport_slug)).scalars().first()
    if sport is None:
        raise ValueError(f"Sport inconnu : {sport_slug}")

    user_sport = (
        db.execute(
            select(UserSport).where(
                UserSport.user_id == user_id, UserSport.sport_id == sport.id
            )
        )
        .scalars()
        .first()
    )

    if user_sport is None:
        user_sport = UserSport(user_id=user_id, sport_id=sport.id)
        db.add(user_sport)

    user_sport.level = level
    user_sport.frequency_per_week = frequency_per_week

    if is_primary:
        db.execute(
            select(UserSport).where(
                UserSport.user_id == user_id, UserSport.sport_id != sport.id
            )
        )
        for other in get_user_sports(db, user_id):
            if other.sport_id != sport.id:
                other.is_primary = False
        user_sport.is_primary = True

    db.flush()
    return user_sport


def get_sport_goal_relevance(
    db: Session, sport_slug: Optional[str], goal_slug: Optional[str]
) -> Optional[float]:
    """
    Score de pertinence (0-1) d'un objectif pour un sport donne, lu dans
    SportGoalMatrix (module Sport, partie 3 : matrice sport x objectif,
    seedee via seed_sport_goals_equipment.py). Retourne None si le sport,
    l'objectif ou la combinaison n'existe pas dans la matrice -- jamais
    d'erreur, l'appelant se rabat alors sur le score par defaut (regle :
    Fitapp doit continuer a fonctionner avec les donnees deja presentes).
    """

    if not sport_slug or not goal_slug:
        return None

    row = db.execute(
        select(SportGoalMatrix.relevance_score)
        .join(Sport, SportGoalMatrix.sport_id == Sport.id)
        .join(Goal, SportGoalMatrix.goal_id == Goal.id)
        .where(Sport.slug == sport_slug, Goal.slug == goal_slug)
    ).scalar_one_or_none()

    return float(row) if row is not None else None


# ============================================================
# CATALOGUE D'EXERCICES
# ============================================================

def list_exercises(
    db: Session,
    sport_slug: Optional[str] = None,
    training_type=None,
    active_only: bool = True,
) -> list[Exercise]:
    """
    Catalogue d'exercices, filtrable par sport et/ou type d'entrainement.
    training_type peut etre une valeur de app.models.enums.TrainingType ;
    le filtre teste son appartenance au tableau Exercise.training_types.
    """

    query = select(Exercise).options(selectinload(Exercise.translations))

    if active_only:
        query = query.where(Exercise.is_active.is_(True))

    if sport_slug is not None:
        query = query.join(Sport, Exercise.sport_id == Sport.id).where(
            Sport.slug == sport_slug
        )

    if training_type is not None:
        query = query.where(Exercise.training_types.any(training_type))

    return db.execute(query).scalars().all()


def get_exercises_by_slugs(db: Session, slugs: list[str], active_only: bool = True) -> list[Exercise]:
    """Retrouve des exercices par slug en conservant l'ordre demande.
    Les slugs inconnus sont ignores (jamais d'erreur)."""
    if not slugs:
        return []
    query = select(Exercise).options(selectinload(Exercise.translations)).where(Exercise.slug.in_(slugs))
    if active_only:
        query = query.where(Exercise.is_active.is_(True))
    rows = db.execute(query).scalars().all()
    by_slug = {exercise.slug: exercise for exercise in rows}
    return [by_slug[slug] for slug in slugs if slug in by_slug]


# ============================================================
# HISTORIQUE DES SEANCES (charge d'entrainement recente)
# ============================================================

def get_recent_workout_logs(
    db: Session, user_id: uuid.UUID, days: int = 7
) -> list[WorkoutLog]:
    """Seances effectuees par l'utilisateur sur les `days` derniers jours."""

    since = datetime.now(timezone.utc) - timedelta(days=days)

    return (
        db.execute(
            select(WorkoutLog)
            .options(
                selectinload(WorkoutLog.exercises)
                .selectinload(WorkoutLogExercise.sets)
            )
            .where(WorkoutLog.user_id == user_id, WorkoutLog.performed_at >= since)
            .order_by(WorkoutLog.performed_at.desc())
        )
        .scalars()
        .all()
    )


def compute_set_volume(reps: Optional[int], weight_kg: Optional[Decimal]) -> Decimal:
    """
    Volume d'une serie = reps x charge. Retourne 0 si l'un des deux
    manque (ex: serie de cardio sans charge : distance/duree comptent
    ailleurs, pas dans le volume de musculation).
    """

    if reps is None or weight_kg is None:
        return Decimal("0")
    return Decimal(reps) * Decimal(weight_kg)


def compute_workout_log_volume(workout_log: WorkoutLog) -> Decimal:
    """Volume total (reps x charge, toutes series/exercices) d'une seance loguee."""

    total = Decimal("0")
    for exercise in workout_log.exercises:
        for workout_set in exercise.sets:
            total += compute_set_volume(workout_set.reps, workout_set.weight_kg)
    return total


def get_recent_training_load(db: Session, user_id: uuid.UUID, days: int = 7) -> dict:
    """
    Resume de la charge d'entrainement recente, utilise par le futur
    Recovery Score (etape 8) et le moteur de recommandation (etape 6).
    """

    logs = get_recent_workout_logs(db, user_id, days=days)

    total_sessions = len(logs)
    total_duration_minutes = sum(
        (log.duration_minutes or 0) for log in logs
    )
    total_volume = sum((compute_workout_log_volume(log) for log in logs), Decimal("0"))

    rpe_values = [
        float(workout_set.rpe)
        for log in logs
        for exercise in log.exercises
        for workout_set in exercise.sets
        if workout_set.rpe is not None
    ]
    average_rpe = round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "total_duration_minutes": total_duration_minutes,
        "total_volume_kg": float(total_volume),
        "average_rpe": average_rpe,
    }
