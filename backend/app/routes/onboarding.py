"""
Route de completion de l'onboarding (regles 1, 2, 4, 5).

POST /onboarding recoit en un seul appel tout ce que collecte
OnboardingScreen.js cote app, et cree en base :

  - le User (username + langue preferee)
  - le Profile (age, sexe, taille, poids, niveau d'activite, objectif)
  - deux BodyMeasurement (poids + taille) pour demarrer l'historique
    de progression (regle 2 : ne jamais se contenter du poids "actuel")
  - un UserSport si un sport principal a ete choisi (le Sport est
    cree a la volee s'il n'existe pas encore -> catalogue auto-extensible)

C'est volontairement un seul endpoint "gros grain" car l'onboarding
est un flux unique cote app ; le detail (PATCH profil, ajout de sports
secondaires...) viendra avec les ecrans dedies plus tard.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import (
    ActivityLevel,
    BodyMetricType,
    GoalType,
    NotificationType,
    Sex,
    SportLevel,
)
from app.models.notification import NotificationLog
from app.models.profile import BodyMeasurement, Profile
from app.models.sport import Sport, SportTranslation, UserSport
from app.models.user import User

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# --- Correspondances entre les ids utilises dans OnboardingScreen.js ---
# et les enums stricts de la base (regle 24 : listes fermees en enum).
# Si l'app ajoute une nouvelle valeur cote front, il faut l'ajouter ici.

ACTIVITY_MAP: dict[str, ActivityLevel] = {
    "sedentary": ActivityLevel.SEDENTARY,
    "light": ActivityLevel.LIGHT,
    "active": ActivityLevel.MODERATE,
    "very-active": ActivityLevel.ACTIVE,
    "athlete": ActivityLevel.VERY_ACTIVE,
}

GOAL_MAP: dict[str, GoalType] = {
    "eat-healthier": GoalType.GENERAL_HEALTH,
    "build-muscle": GoalType.MUSCLE_GAIN,
    "lose-fat": GoalType.WEIGHT_LOSS,
    "maintain-weight": GoalType.MAINTENANCE,
    "improve-performance": GoalType.PERFORMANCE,
    "healthy-lifestyle": GoalType.GENERAL_HEALTH,
}

# Table de correspondance slug onboarding (choix affiches a l'utilisateur,
# forme dans OnboardingScreen.js) -> slug CANONIQUE du catalogue seede par
# seed_sports.py. Sans cette normalisation, le Sport cree portait le slug
# brut de l'onboarding ("weight", "combat", "running", "cycling",
# "swimming") qui ne correspondait a AUCUN exercice du catalogue ni a
# aucune ponderation de training_recommender.py / training_programs.py
# (qui raisonnent tous avec les slugs canoniques "musculation",
# "arts_martiaux", "course", "cyclisme", "natation", "football") --
# bug corrige ici. "combat" est mappe vers "arts_martiaux" (regroupe
# tous les sports de combat sous ce slug unique, plutot que "boxe").
ONBOARDING_SPORT_SLUG_MAP: dict[str, str] = {
    "weight": "musculation",
    "combat": "arts_martiaux",
    "running": "course",
    "cycling": "cyclisme",
    "swimming": "natation",
    "football": "football",
}

# slug canonique -> traductions (fr/en/es/ar), utilise seulement a la
# creation du sport s'il n'existe pas encore en base (ex: seed_sports.py
# pas encore execute).
SPORT_LABELS: dict[str, dict[str, str]] = {
    "football": {"fr": "Football", "en": "Football", "es": "Fútbol", "ar": "كرة القدم"},
    "musculation": {
        "fr": "Musculation",
        "en": "Weightlifting",
        "es": "Musculación",
        "ar": "رفع الأثقال",
    },
    "course": {"fr": "Course à pied", "en": "Running", "es": "Running", "ar": "الجري"},
    "cyclisme": {"fr": "Cyclisme", "en": "Cycling", "es": "Ciclismo", "ar": "ركوب الدراجات"},
    "arts_martiaux": {
        "fr": "Sports de combat",
        "en": "Combat sports",
        "es": "Deportes de combate",
        "ar": "الرياضات القتالية",
    },
    "natation": {"fr": "Natation", "en": "Swimming", "es": "Natación", "ar": "السباحة"},
    "other": {"fr": "Autre", "en": "Other", "es": "Otro", "ar": "أخرى"},
}


class OnboardingPayload(BaseModel):
    """Reprend exactement la forme de `data` dans OnboardingScreen.js."""

    language: str = Field(default="fr", max_length=5)
    gender: Optional[str] = None  # "male" | "female"
    name: str = Field(min_length=1, max_length=50)
    weight: float
    weightUnit: str = "kg"  # "kg" | "lb"
    height: float
    heightUnit: str = "cm"  # "cm" | "in"
    age: int
    activity: Optional[str] = None
    sport: Optional[str] = None
    goals: List[str] = Field(default_factory=list)


class OnboardingResult(BaseModel):
    user_id: UUID
    username: str


def _get_or_create_sport(db: Session, sport_key: str) -> Sport:
    """Recupere un sport par son slug, ou le cree avec ses traductions."""
    sport = db.execute(
        select(Sport).where(Sport.slug == sport_key)
    ).scalar_one_or_none()
    if sport is not None:
        return sport

    labels = SPORT_LABELS.get(sport_key, {"fr": sport_key.capitalize()})
    sport = Sport(slug=sport_key)
    db.add(sport)
    db.flush()  # attribue l'id avant de creer les traductions liees

    for lang_code, name in labels.items():
        db.add(SportTranslation(sport_id=sport.id, language_code=lang_code, name=name))

    return sport


@router.post("", response_model=OnboardingResult, status_code=201)
def complete_onboarding(payload: OnboardingPayload, db: Session = Depends(get_db)):
    existing = db.execute(
        select(User).where(User.username == payload.name)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Le nom '{payload.name}' est deja pris. Choisis-en un autre.",
        )

    # --- Conversion vers les unites de reference (kg / cm) ---
    weight_kg = payload.weight * 0.453592 if payload.weightUnit == "lb" else payload.weight
    height_cm = payload.height * 2.54 if payload.heightUnit == "in" else payload.height

    # --- User ---
    user = User(username=payload.name, preferred_language=payload.language)
    db.add(user)
    db.flush()

    # --- Profile ---
    sex = Sex(payload.gender) if payload.gender in (Sex.MALE, Sex.FEMALE) else None
    activity_level = ACTIVITY_MAP.get(payload.activity) if payload.activity else None
    primary_goal = GOAL_MAP.get(payload.goals[0]) if payload.goals else None

    profile = Profile(
        user_id=user.id,
        age=payload.age,
        sex=sex,
        height_cm=round(height_cm, 1),
        current_weight_kg=round(weight_kg, 2),
        activity_level=activity_level,
        primary_goal=primary_goal,
    )
    db.add(profile)

    # --- Historique (regle 2 : jamais uniquement le poids actuel) ---
    today = date.today()
    db.add(
        BodyMeasurement(
            user_id=user.id,
            metric_type=BodyMetricType.WEIGHT,
            value=round(weight_kg, 2),
            unit="kg",
            recorded_at=today,
        )
    )
    db.add(
        BodyMeasurement(
            user_id=user.id,
            metric_type=BodyMetricType.HEIGHT,
            value=round(height_cm, 1),
            unit="cm",
            recorded_at=today,
        )
    )

    # --- Sport principal (regle 4) ---
    # Le sport est facultatif pour une personne sédentaire. On ignore aussi
    # toute valeur envoyée par un ancien client afin de garder cette règle
    # côté backend, indépendamment de l'interface utilisée.
    sport_key = None if payload.activity == "sedentary" else payload.sport
    if sport_key and sport_key != "other":
        sport_key = ONBOARDING_SPORT_SLUG_MAP.get(sport_key, sport_key)
        sport = _get_or_create_sport(db, sport_key)
        db.add(
            UserSport(
                user_id=user.id,
                sport_id=sport.id,
                is_primary=True,
                level=SportLevel.BEGINNER,
            )
        )

    db.add(
        NotificationLog(
            user_id=user.id,
            notification_type=NotificationType.GENERAL,
            title="Bienvenue dans Fitapp",
            body="Votre suivi nutritionnel est prêt à commencer.",
            language_code=payload.language,
        )
    )

    db.commit()
    db.refresh(user)
    # On construit la reponse explicitement : le User expose son PK sous
    # le nom `id`, pas `user_id` (from_attributes ne peut pas deviner).
    return OnboardingResult(user_id=user.id, username=user.username)
