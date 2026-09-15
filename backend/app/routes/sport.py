"""
Routes du module Sport (module Sport, partie 19), adaptees aux
conventions deja en place dans le projet (chaque domaine a son propre
router avec son propre prefixe, monte tel quel dans main.py -- pas de
prefixe /api/v1 global, seul foods.router en beneficie aujourd'hui).

Reutilise integralement les services des etapes precedentes, aucune
logique metier n'est dupliquee ici :
    - app/services/training_service.py       (etape 5)
    - app/services/training_recommender.py   (etape 6)
    - app/services/training_progression.py   (etape 7)
    - app/services/recovery_service.py       (etape 8)
    - app/services/sport_nutrition_bridge.py (etape 9)

Le Recovery Score (etape 8) est ici branche sur le moteur de
recommandation (etape 6) : recovery_service.compute_recovery_score()
etait deja concu pour ca (voir son docstring), il ne restait qu'a
faire l'appel cote route -- exactement ce que ce fichier fait.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session

from app.database.connection import get_db
from app.models.enums import GoalType, SportLevel, TrainingType
from app.models.profile import Profile
from app.models.sport import Sport, UserSport
from app.models.training import Exercise, Workout
from app.models.training_log import PersonalRecord, WorkoutLog, WorkoutLogExercise, WorkoutLogSet
from app.models.user import User
from app.services.recovery_service import compute_recovery_score
from app.services.sport_nutrition_bridge import DEFAULT_WEIGHT_KG, estimate_calories_from_effort
from app.services.training_progression import (
    suggest_exercise_progression,
    suggest_progression_for_last_workout,
)
from app.services.training_recommender import recommend_workout
from app.services.training_service import (
    get_recent_training_load,
    get_user_sports,
    list_exercises,
    set_user_sport,
)
from app.services.training_session_translations import translate_session_name
from app.services.weekly_scheduler import generate_weekly_program

router = APIRouter(tags=["sport"])


# ============================================================
# HELPERS
# ============================================================

def ensure_user_exists(user_id: UUID, db: Session) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")


def _translated_name(translations, language: str = "fr") -> str:
    match = next((t for t in translations if t.language_code == language), None)
    if match is not None:
        return match.name
    return translations[0].name if translations else ""


def _sport_to_dict(sport: Sport, language: str = "fr") -> dict:
    return {
        "id": str(sport.id),
        "slug": sport.slug,
        "name": _translated_name(sport.translations, language),
        "is_active": True,
    }


def _exercise_to_dict(exercise: Optional[Exercise], language: str = "fr") -> Optional[dict]:
    if exercise is None:
        return None
    return {
        "id": str(exercise.id),
        "slug": exercise.slug,
        "name": _translated_name(exercise.translations, language),
        "sport_id": str(exercise.sport_id) if exercise.sport_id else None,
        "sport_slug": exercise.sport.slug if exercise.sport else None,
        "category": exercise.category,
        "equipment": exercise.equipment,
        "training_types": [t.value for t in (exercise.training_types or [])],
        "difficulty": exercise.difficulty.value if exercise.difficulty else None,
        "is_active": exercise.is_active,
    }


def _serialize_recommendation(recommendation: dict, language: str = "fr") -> dict:
    """Convertit les objets Exercise ORM imbriques dans le dict retourne
    par recommend_workout() en dicts JSON-serialisables."""

    def _bookend(entry: dict) -> dict:
        return {**entry, "exercise": _exercise_to_dict(entry.get("exercise"), language)}

    return {
        **recommendation,
        "session_name": translate_session_name(recommendation.get("session_name"), language),
        "goal": recommendation["goal"].value if recommendation.get("goal") else None,
        "training_type": recommendation["training_type"].value if recommendation.get("training_type") else None,
        "difficulty": recommendation["difficulty"].value if recommendation.get("difficulty") else None,
        "level": recommendation["level"].value if recommendation.get("level") else None,
        "warmup": _bookend(recommendation["warmup"]),
        "cooldown": _bookend(recommendation["cooldown"]),
        "exercises": [
            {
                **item,
                "exercise": _exercise_to_dict(item["exercise"], language),
            }
            for item in recommendation["exercises"]
        ],
        "finisher": (
            {
                **recommendation["finisher"],
                "exercise": _exercise_to_dict(
                    recommendation["finisher"].get("exercise"), language
                ),
            }
            if recommendation.get("finisher")
            else None
        ),
    }


def _user_sport_to_dict(user_sport: UserSport, language: str = "fr") -> dict:
    return {
        "id": str(user_sport.id),
        "sport": _sport_to_dict(user_sport.sport, language) if user_sport.sport else None,
        "level": user_sport.level.value if user_sport.level else None,
        "frequency_per_week": user_sport.frequency_per_week,
        "is_primary": user_sport.is_primary,
    }


def _workout_log_to_dict(log: WorkoutLog) -> dict:
    return {
        "id": str(log.id),
        "based_on_workout_id": str(log.based_on_workout_id) if log.based_on_workout_id else None,
        "performed_at": log.performed_at.isoformat(),
        "duration_minutes": log.duration_minutes,
        "notes": log.notes,
        "exercises": [
            {
                "id": str(we.id),
                "exercise_id": str(we.exercise_id),
                "exercise_slug": we.exercise.slug if we.exercise else None,
                "sets": [
                    {
                        "set_number": s.set_number,
                        "reps": s.reps,
                        "weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
                        "duration_seconds": s.duration_seconds,
                        "distance_m": float(s.distance_m) if s.distance_m is not None else None,
                        "rest_seconds": s.rest_seconds,
                        "rpe": float(s.rpe) if s.rpe is not None else None,
                        "notes": s.notes,
                    }
                    for s in we.sets
                ],
            }
            for we in log.exercises
        ],
    }


def _fill_estimated_calories(db: Session, user_id: UUID, recommendation: dict) -> dict:
    """
    Previsualisation des calories d'une seance RECOMMANDEE (pas encore
    effectuee), en reutilisant la meme formule de secours que le pont
    nutrition/hydratation de l'etape 9 (sport_nutrition_bridge.py) --
    jamais une deuxieme formule inventee ici. Le poids du profil est
    utilise s'il existe, sinon DEFAULT_WEIGHT_KG (jamais bloquant).
    """

    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    weight_kg = (
        float(profile.current_weight_kg)
        if profile and profile.current_weight_kg is not None
        else DEFAULT_WEIGHT_KG
    )
    recommendation["estimated_calories_kcal"] = estimate_calories_from_effort(
        recommendation.get("planned_duration_minutes"), weight_kg, recommendation.get("target_rpe")
    )
    return recommendation


def _serialize_weekly_program(program: dict, language: str = "fr") -> dict:
    """Meme principe que _serialize_recommendation, applique a chaque
    jour d'entrainement de la semaine. Un jour de repos est deja
    JSON-serialisable tel quel (exercise_slug en texte, pas d'objet
    ORM Exercise) -- rien a convertir."""

    days = [
        {**day, "workout": _serialize_recommendation(day["workout"], language)}
        if day["day_type"] == "training"
        else day
        for day in program["days"]
    ]
    return {
        **program,
        "goal": program["goal"].value if program.get("goal") else None,
        "days": days,
    }


# ============================================================
# CATALOGUE DES SPORTS
# ============================================================

@router.get("/sports")
def list_sports(language: str = Query(default="fr"), db: Session = Depends(get_db)):
    sports = db.execute(
        select(Sport).options(selectinload(Sport.translations))
    ).scalars().all()
    return [_sport_to_dict(s, language) for s in sports]


@router.get("/sports/{sport_id}")
def get_sport(sport_id: UUID, language: str = Query(default="fr"), db: Session = Depends(get_db)):
    sport = db.execute(
        select(Sport)
        .options(selectinload(Sport.translations))
        .where(Sport.id == sport_id)
    ).scalar_one_or_none()
    if sport is None:
        raise HTTPException(status_code=404, detail="Sport introuvable.")
    return _sport_to_dict(sport, language)


# ============================================================
# PROFIL SPORTIF DE L'UTILISATEUR
# ============================================================

class SportProfileCreate(BaseModel):
    sport_slug: str = Field(min_length=1)
    level: Optional[SportLevel] = None
    frequency_per_week: Optional[int] = Field(default=None, ge=0, le=14)
    is_primary: bool = False


@router.post("/sports/profile/{user_id}", status_code=201)
def create_or_update_sport_profile(
    user_id: UUID, payload: SportProfileCreate, db: Session = Depends(get_db)
):
    ensure_user_exists(user_id, db)
    try:
        user_sport = set_user_sport(
            db,
            user_id,
            sport_slug=payload.sport_slug,
            level=payload.level,
            frequency_per_week=payload.frequency_per_week,
            is_primary=payload.is_primary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    db.refresh(user_sport)
    return _user_sport_to_dict(user_sport)


@router.get("/sports/profile/{user_id}")
def get_sport_profile(user_id: UUID, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    sports = get_user_sports(db, user_id)
    return [_user_sport_to_dict(s) for s in sports]


# ============================================================
# CATALOGUE D'EXERCICES
# ============================================================

@router.get("/exercises")
def get_exercises(
    sport_slug: Optional[str] = None,
    training_type: Optional[TrainingType] = None,
    language: str = Query(default="fr"),
    db: Session = Depends(get_db),
):
    exercises = list_exercises(db, sport_slug=sport_slug, training_type=training_type)
    return [_exercise_to_dict(e, language) for e in exercises]


@router.get("/exercises/{exercise_id}")
def get_exercise(exercise_id: UUID, language: str = Query(default="fr"), db: Session = Depends(get_db)):
    exercise = db.execute(
        select(Exercise)
        .options(selectinload(Exercise.translations), selectinload(Exercise.sport))
        .where(Exercise.id == exercise_id)
    ).scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercice introuvable.")
    return _exercise_to_dict(exercise, language)


# ============================================================
# RECOMMANDATION DE SEANCE (etapes 6 + 8 combinees)
# ============================================================

@router.get("/workouts/recommended/{user_id}")
def get_recommended_workout(
    user_id: UUID,
    goal: Optional[GoalType] = None,
    language: str = Query(default="fr"),
    db: Session = Depends(get_db),
):
    ensure_user_exists(user_id, db)
    recovery = compute_recovery_score(db, user_id)
    recommendation = recommend_workout(
        db, user_id, goal=goal, recovery_score=recovery["recovery_fraction"]
    )
    recommendation = _fill_estimated_calories(db, user_id, recommendation)
    return {
        "recommendation": _serialize_recommendation(recommendation, language),
        "recovery": recovery,
    }


@router.get("/workouts/today/{user_id}")
def get_today_workout(
    user_id: UUID,
    goal: Optional[GoalType] = None,
    language: str = Query(default="fr"),
    db: Session = Depends(get_db),
):
    """
    Si une seance a deja ete loguee aujourd'hui, la retourne telle
    quelle (statut 'done'). Sinon, retourne la seance recommandee du
    jour (statut 'recommended'), sport ou non-sportif confondus (aucune
    seance loguee -> juste une recommandation, jamais d'erreur).
    """

    ensure_user_exists(user_id, db)
    today = date.today()

    todays_log = db.execute(
        select(WorkoutLog)
        .options(
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.sets),
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.exercise),
        )
        .where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.performed_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            WorkoutLog.performed_at <= datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc),
        )
        .order_by(WorkoutLog.performed_at.desc())
    ).scalars().first()

    if todays_log is not None:
        return {"status": "done", "workout_log": _workout_log_to_dict(todays_log)}

    recovery = compute_recovery_score(db, user_id, on_date=today)
    recommendation = recommend_workout(
        db, user_id, goal=goal, recovery_score=recovery["recovery_fraction"]
    )
    recommendation = _fill_estimated_calories(db, user_id, recommendation)
    return {
        "status": "recommended",
        "recommendation": _serialize_recommendation(recommendation, language),
        "recovery": recovery,
    }


# ============================================================
# SEANCES (WorkoutLog = WorkoutSession du cahier des charges)
# ============================================================

class WorkoutSetCreate(BaseModel):
    reps: Optional[int] = Field(default=None, ge=0)
    weight_kg: Optional[float] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    distance_m: Optional[float] = Field(default=None, ge=0)
    rest_seconds: Optional[int] = Field(default=None, ge=0)
    rpe: Optional[float] = Field(default=None, ge=0, le=10)
    notes: Optional[str] = None


class WorkoutLogExerciseCreate(BaseModel):
    exercise_slug: str = Field(min_length=1)
    sets: list[WorkoutSetCreate] = Field(default_factory=list)


class WorkoutSessionCreate(BaseModel):
    based_on_workout_id: Optional[UUID] = None
    performed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    exercises: list[WorkoutLogExerciseCreate] = Field(default_factory=list)


def _resolve_exercise_id(db: Session, slug: str) -> UUID:
    exercise = db.execute(select(Exercise).where(Exercise.slug == slug)).scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail=f"Exercice introuvable : {slug}")
    return exercise.id


@router.post("/workouts/sessions/{user_id}", status_code=201)
def create_workout_session(user_id: UUID, payload: WorkoutSessionCreate, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)

    if payload.based_on_workout_id is not None:
        planned = db.get(Workout, payload.based_on_workout_id)
        if planned is None:
            raise HTTPException(status_code=404, detail="Workout planifie introuvable.")

    log = WorkoutLog(
        user_id=user_id,
        based_on_workout_id=payload.based_on_workout_id,
        performed_at=payload.performed_at or datetime.now(timezone.utc),
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
    )
    db.add(log)
    db.flush()

    for order, exercise_payload in enumerate(payload.exercises):
        exercise_id = _resolve_exercise_id(db, exercise_payload.exercise_slug)
        we = WorkoutLogExercise(workout_log_id=log.id, exercise_id=exercise_id, display_order=order)
        db.add(we)
        db.flush()
        for set_number, set_payload in enumerate(exercise_payload.sets, start=1):
            db.add(
                WorkoutLogSet(
                    workout_log_exercise_id=we.id,
                    set_number=set_number,
                    reps=set_payload.reps,
                    weight_kg=Decimal(str(set_payload.weight_kg)) if set_payload.weight_kg is not None else None,
                    duration_seconds=set_payload.duration_seconds,
                    distance_m=Decimal(str(set_payload.distance_m)) if set_payload.distance_m is not None else None,
                    rest_seconds=set_payload.rest_seconds,
                    rpe=Decimal(str(set_payload.rpe)) if set_payload.rpe is not None else None,
                    notes=set_payload.notes,
                )
            )

    db.commit()

    log = db.execute(
        select(WorkoutLog)
        .options(
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.sets),
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.exercise),
        )
        .where(WorkoutLog.id == log.id)
    ).scalar_one()

    return _workout_log_to_dict(log)


@router.get("/workouts/sessions/{user_id}")
def list_workout_sessions(user_id: UUID, days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    results = db.execute(
        select(WorkoutLog)
        .options(
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.sets),
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.exercise),
        )
        .where(WorkoutLog.user_id == user_id, WorkoutLog.performed_at >= since)
        .order_by(WorkoutLog.performed_at.desc())
        .limit(200)
    ).scalars().all()
    return [_workout_log_to_dict(log) for log in results]


# ============================================================
# LOGS (ExerciseLog du cahier des charges : ajout incremental a une
# seance deja creee, exercice par exercice)
# ============================================================

class WorkoutLogAppend(BaseModel):
    workout_log_id: UUID
    exercise_slug: str = Field(min_length=1)
    sets: list[WorkoutSetCreate] = Field(default_factory=list)


@router.post("/workouts/logs/{user_id}", status_code=201)
def append_exercise_log(user_id: UUID, payload: WorkoutLogAppend, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)

    log = db.execute(
        select(WorkoutLog).where(WorkoutLog.id == payload.workout_log_id, WorkoutLog.user_id == user_id)
    ).scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail="Seance introuvable.")

    exercise_id = _resolve_exercise_id(db, payload.exercise_slug)

    next_order = len(log.exercises)
    we = WorkoutLogExercise(workout_log_id=log.id, exercise_id=exercise_id, display_order=next_order)
    db.add(we)
    db.flush()

    for set_number, set_payload in enumerate(payload.sets, start=1):
        db.add(
            WorkoutLogSet(
                workout_log_exercise_id=we.id,
                set_number=set_number,
                reps=set_payload.reps,
                weight_kg=Decimal(str(set_payload.weight_kg)) if set_payload.weight_kg is not None else None,
                duration_seconds=set_payload.duration_seconds,
                distance_m=Decimal(str(set_payload.distance_m)) if set_payload.distance_m is not None else None,
                rest_seconds=set_payload.rest_seconds,
                rpe=Decimal(str(set_payload.rpe)) if set_payload.rpe is not None else None,
                notes=set_payload.notes,
            )
        )

    db.commit()

    log = db.execute(
        select(WorkoutLog)
        .options(
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.sets),
            selectinload(WorkoutLog.exercises).selectinload(WorkoutLogExercise.exercise),
        )
        .where(WorkoutLog.id == log.id)
    ).scalar_one()

    return _workout_log_to_dict(log)


# ============================================================
# PROGRESSION (etape 7)
# ============================================================

@router.get("/progress/{user_id}")
def get_progress(user_id: UUID, exercise_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    """
    Sans exercise_id : suggestions de progression pour chaque exercice
    de la toute derniere seance (module Sport, partie 9), plus la
    charge d'entrainement recente (7/30 jours) et les records
    personnels. Avec exercise_id : suggestion cible pour cet exercice
    precis uniquement.
    """

    ensure_user_exists(user_id, db)

    if exercise_id is not None:
        try:
            return suggest_exercise_progression(db, user_id, exercise_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    suggestions = suggest_progression_for_last_workout(db, user_id)

    records = db.execute(
        select(PersonalRecord)
        .where(PersonalRecord.user_id == user_id)
        .order_by(PersonalRecord.achieved_at.desc())
        .limit(50)
    ).scalars().all()

    return {
        "progression_suggestions": suggestions,
        "training_load_7d": get_recent_training_load(db, user_id, days=7),
        "training_load_30d": get_recent_training_load(db, user_id, days=30),
        "personal_records": [
            {
                "id": str(r.id),
                "record_type": r.record_type.value,
                "value": float(r.value),
                "unit": r.unit,
                "achieved_at": r.achieved_at.isoformat(),
            }
            for r in records
        ],
    }


# ============================================================
# RECUPERATION (etape 8)
# ============================================================

@router.get("/recovery/{user_id}")
def get_recovery(user_id: UUID, on_date: Optional[date] = None, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    result = compute_recovery_score(db, user_id, on_date=on_date)
    return {**result, "level": result["level"].value}


# ============================================================
# PROGRAMME HEBDOMADAIRE (Weekly Scheduler + Program Validator)
# ============================================================

@router.get("/programs/weekly/{user_id}")
def get_weekly_program(
    user_id: UUID,
    goal: Optional[GoalType] = None,
    language: str = Query(default="fr"),
    db: Session = Depends(get_db),
):
    """
    Programme de 7 jours regenere dynamiquement (jamais stocke, module
    Sport partie 6) : alterne jours d'entrainement (issus de
    recommend_workout, etape 6) et jours de repos/recuperation active,
    avec detection de conflits (intensite/charge repetee) et
    validation post-generation (parties 15-17, 26, 31).
    """

    ensure_user_exists(user_id, db)
    program = generate_weekly_program(db, user_id, goal=goal)
    return _serialize_weekly_program(program, language)
