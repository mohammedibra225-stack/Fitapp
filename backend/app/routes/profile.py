"""
Route de consultation/edition du profil complet (regle : toutes les infos
collectees a l'onboarding doivent rester modifiables ensuite).

GET   /profile/{user_id}  -> tout ce qu'il faut pour pre-remplir l'ecran
                              Profil (identite + Profile + preferences
                              alimentaires/budget).
PATCH /profile/{user_id}  -> mise a jour partielle (mêmes cles que
                              OnboardingPayload, plus diet/allergies/budget).

Reutilise ACTIVITY_MAP / GOAL_MAP d'app.routes.onboarding pour ne pas
dupliquer la correspondance ui-key <-> enum (source unique de verite).
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import BodyMetricType, Sex
from app.models.profile import BodyMeasurement, Profile
from app.models.user import User
from app.routes.onboarding import ACTIVITY_MAP, GOAL_MAP

router = APIRouter(prefix="/profile", tags=["profile"])


# --- Reverse maps (regle : source unique de verite = onboarding.py) ---
# GoalType.GENERAL_HEALTH a deux cles ui possibles ("eat-healthier" et
# "healthy-lifestyle") ; on ne peut pas savoir laquelle a ete choisie a
# l'origine, donc on retient la premiere rencontree comme representant
# canonique pour le formulaire d'edition.
ACTIVITY_MAP_REVERSE = {value: key for key, value in ACTIVITY_MAP.items()}
GOAL_MAP_REVERSE: dict = {}
for _key, _value in GOAL_MAP.items():
    GOAL_MAP_REVERSE.setdefault(_value, _key)

# Regimes geres par ProfileScreen.js (profile.diet_*) : stockes tels quels
# dans Profile.dietary_preferences (le recommender fait un simple "in"
# sur cette chaine, donc aucune conversion supplementaire n'est necessaire).
KNOWN_DIETS = {"none", "vegetarian", "vegan", "pescatarian", "halal", "keto"}


class ProfileUpdatePayload(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    language: Optional[str] = Field(default=None, max_length=5)
    gender: Optional[str] = None  # "male" | "female"
    weight: Optional[float] = None
    weightUnit: str = "kg"
    height: Optional[float] = None
    heightUnit: str = "cm"
    age: Optional[int] = None
    activity: Optional[str] = None
    goals: Optional[List[str]] = None
    diet: Optional[str] = None
    allergies: Optional[List[str]] = None
    budget_per_week: Optional[float] = None


@router.get("/{user_id}/measurements")
def get_body_measurements(
    user_id: UUID,
    metric_type: BodyMetricType = BodyMetricType.WEIGHT,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Historique d'une mesure corporelle (poids par defaut), utilise par
    la page Progression pour tracer une courbe reelle (regle 2 : ne
    jamais se contenter de la valeur "actuelle"). Trie du plus ancien
    au plus recent, pret a etre affiche tel quel dans un graphique."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    query = select(BodyMeasurement).where(
        BodyMeasurement.user_id == user_id,
        BodyMeasurement.metric_type == metric_type,
    )
    if start_date:
        query = query.where(BodyMeasurement.recorded_at >= start_date)
    if end_date:
        query = query.where(BodyMeasurement.recorded_at <= end_date)
    measurements = db.execute(
        query.order_by(BodyMeasurement.recorded_at.asc())
    ).scalars().all()

    return [
        {
            "id": str(m.id),
            "metric_type": m.metric_type.value,
            "value": float(m.value),
            "unit": m.unit,
            "recorded_at": m.recorded_at.isoformat(),
        }
        for m in measurements
    ]


@router.get("/{user_id}")
def get_profile(user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    allergies = (
        [item for item in (profile.allergies or "").split(",") if item]
        if profile
        else []
    )
    diet = (profile.dietary_preferences if profile else None) or "none"

    return {
        "user_id": str(user.id),
        "name": user.username,
        "language": user.preferred_language,
        "gender": profile.sex.value if profile and profile.sex else None,
        "weight": float(profile.current_weight_kg) if profile and profile.current_weight_kg else None,
        "height": float(profile.height_cm) if profile and profile.height_cm else None,
        "age": profile.age if profile else None,
        "activity": ACTIVITY_MAP_REVERSE.get(profile.activity_level) if profile and profile.activity_level else None,
        "goals": [GOAL_MAP_REVERSE[profile.primary_goal]] if profile and profile.primary_goal in GOAL_MAP_REVERSE else [],
        "diet": diet,
        "allergies": allergies,
        "budget_per_week": float(profile.food_budget_per_week) if profile and profile.food_budget_per_week else None,
        "halal_required": bool(profile.halal_required) if profile else False,
    }


@router.patch("/{user_id}")
def update_profile(
    user_id: UUID,
    payload: ProfileUpdatePayload,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profil introuvable (onboarding non termine).",
        )

    values = payload.model_dump(exclude_unset=True)

    # --- Identite (User) ---
    if "name" in values and values["name"] and values["name"] != user.username:
        existing = db.execute(
            select(User).where(User.username == values["name"])
        ).scalar_one_or_none()
        if existing is not None and existing.id != user.id:
            raise HTTPException(
                status_code=409,
                detail=f"Le nom '{values['name']}' est deja pris. Choisis-en un autre.",
            )
        user.username = values["name"]

    if values.get("language"):
        user.preferred_language = values["language"]

    # --- Sexe ---
    if values.get("gender") in (Sex.MALE, Sex.FEMALE):
        profile.sex = Sex(values["gender"])

    # --- Age ---
    if values.get("age") is not None:
        profile.age = values["age"]

    # --- Poids / taille : converties en unites de reference, ET
    # historisees (regle 2 : jamais uniquement la valeur "actuelle") ---
    today = date.today()

    if values.get("weight") is not None:
        weight_kg = (
            values["weight"] * 0.453592
            if payload.weightUnit == "lb"
            else values["weight"]
        )
        weight_kg = round(weight_kg, 2)
        if profile.current_weight_kg != weight_kg:
            profile.current_weight_kg = weight_kg
            db.add(
                BodyMeasurement(
                    user_id=user.id,
                    metric_type=BodyMetricType.WEIGHT,
                    value=weight_kg,
                    unit="kg",
                    recorded_at=today,
                )
            )

    if values.get("height") is not None:
        height_cm = (
            values["height"] * 2.54
            if payload.heightUnit == "in"
            else values["height"]
        )
        height_cm = round(height_cm, 1)
        if profile.height_cm != height_cm:
            profile.height_cm = height_cm
            db.add(
                BodyMeasurement(
                    user_id=user.id,
                    metric_type=BodyMetricType.HEIGHT,
                    value=height_cm,
                    unit="cm",
                    recorded_at=today,
                )
            )

    # --- Activite ---
    if values.get("activity") in ACTIVITY_MAP:
        profile.activity_level = ACTIVITY_MAP[values["activity"]]

    # --- Objectif principal (le premier choisi, comme a l'onboarding) ---
    if values.get("goals"):
        first_goal = values["goals"][0]
        if first_goal in GOAL_MAP:
            profile.primary_goal = GOAL_MAP[first_goal]

    # --- Regime / halal (regle 6/7 : halal_required pilote les
    # contraintes obligatoires du moteur de recommandation) ---
    if values.get("diet") in KNOWN_DIETS:
        diet = values["diet"]
        profile.dietary_preferences = None if diet == "none" else diet
        profile.halal_required = diet == "halal"

    # --- Allergies (liste -> texte stocke, regle : jamais de champ
    # libre non structure pour une contrainte de securite alimentaire) ---
    if values.get("allergies") is not None:
        profile.allergies = ",".join(values["allergies"]) or None

    # --- Budget hebdomadaire (regle 4/10) ---
    if values.get("budget_per_week") is not None:
        profile.food_budget_per_week = values["budget_per_week"]

    db.commit()
    db.refresh(profile)
    db.refresh(user)

    return get_profile(user_id, db)
