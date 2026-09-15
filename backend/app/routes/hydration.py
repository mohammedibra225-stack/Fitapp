"""
Suivi de l'hydratation.

Le modele WaterLog existe deja (app/models/hydration.py, deja en base
via la migration initiale). Ce fichier ajoute les routes qui
manquaient encore :

    POST /hydration/log/{user_id}      -> enregistrer une prise d'eau
    GET  /hydration/{user_id}/today    -> total du jour + objectif
    GET  /hydration/{user_id}/history  -> historique sur N jours
    GET  /hydration/{user_id}/goal     -> objectif seul (depuis le profil)
"""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hydration import WaterLog
from app.models.profile import Profile
from app.models.user import User
from app.services.hydration import calculate_water_goal_ml

router = APIRouter(prefix="/hydration", tags=["hydration"])


# ============================================================
# SCHEMAS
# ============================================================

class WaterLogCreate(BaseModel):
    quantity_ml: int = Field(..., gt=0, le=5000)
    # Optionnel : si absent, on prend l'heure actuelle.
    logged_at: datetime | None = None


class WaterLogOut(BaseModel):
    id: UUID
    quantity_ml: int
    logged_on: date
    logged_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# ENREGISTRER UNE PRISE D'EAU
# ============================================================

@router.post("/log/{user_id}", response_model=WaterLogOut, status_code=201)
def log_water(user_id: UUID, payload: WaterLogCreate, db: Session = Depends(get_db)):

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    logged_at = payload.logged_at or datetime.now(timezone.utc)

    log = WaterLog(
        user_id=user_id,
        quantity_ml=payload.quantity_ml,
        logged_on=logged_at.date(),
        logged_at=logged_at,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return log


# ============================================================
# TOTAL DU JOUR + OBJECTIF
# ============================================================

@router.get("/{user_id}/today")
def get_today_hydration(user_id: UUID, db: Session = Depends(get_db)):

    today = date.today()

    total_ml = db.execute(
        select(func.coalesce(func.sum(WaterLog.quantity_ml), 0)).where(
            WaterLog.user_id == user_id,
            WaterLog.logged_on == today,
        )
    ).scalar_one()

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    goal_ml = None
    if profile and profile.current_weight_kg and profile.activity_level:
        goal_ml = calculate_water_goal_ml(
            weight_kg=float(profile.current_weight_kg),
            activity_level=profile.activity_level,
        )

    result = {
        "user_id": str(user_id),
        "date": today.isoformat(),
        "total_ml": int(total_ml),
        "goal_ml": goal_ml,
    }

    if goal_ml:
        result["remaining_ml"] = max(0, goal_ml - int(total_ml))
        result["progress_percent"] = round(min(int(total_ml) / goal_ml * 100, 100), 1)

    return result


# ============================================================
# HISTORIQUE SUR N JOURS
# ============================================================

@router.get("/{user_id}/history")
def get_hydration_history(
    user_id: UUID,
    days: int = 7,
    db: Session = Depends(get_db),
):

    if days < 1 or days > 90:
        raise HTTPException(
            status_code=400,
            detail="Le parametre 'days' doit etre entre 1 et 90.",
        )

    start_date = date.today() - timedelta(days=days - 1)

    rows = db.execute(
        select(WaterLog.logged_on, func.sum(WaterLog.quantity_ml))
        .where(
            WaterLog.user_id == user_id,
            WaterLog.logged_on >= start_date,
        )
        .group_by(WaterLog.logged_on)
    ).all()

    totals_by_day = {logged_on.isoformat(): int(total) for logged_on, total in rows}

    history = []
    for i in range(days):
        current_day = start_date + timedelta(days=i)
        history.append(
            {
                "date": current_day.isoformat(),
                "total_ml": totals_by_day.get(current_day.isoformat(), 0),
            }
        )

    return {
        "user_id": str(user_id),
        "days": days,
        "history": history,
    }


# ============================================================
# OBJECTIF SEUL (DEPUIS LE PROFIL)
# ============================================================

@router.get("/{user_id}/goal")
def get_hydration_goal(user_id: UUID, db: Session = Depends(get_db)):

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    required_fields = {
        "current_weight_kg": profile.current_weight_kg,
        "activity_level": profile.activity_level,
    }
    missing_fields = [f for f, v in required_fields.items() if v is None]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={"message": "Incomplete profile", "missing_fields": missing_fields},
        )

    goal_ml = calculate_water_goal_ml(
        weight_kg=float(profile.current_weight_kg),
        activity_level=profile.activity_level,
    )

    return {"user_id": str(user_id), "goal_ml": goal_ml}
