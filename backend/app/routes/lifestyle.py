"""
Routes du module Lifestyle / Healthy Lifestyle (module Sport, parties
11 a 14, 19), pour les utilisateurs non-sportifs ou en complement du
sport. Aucune logique metier ici : tout est delegue a
app/services/lifestyle_service.py.

Coherent avec le reste des routes Sport (app/routes/sport.py) : meme
convention ensure_user_exists, meme absence de prefixe /api/v1 (aligne
sur nutrition.py / hydration.py deja en place).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import ActivityDataSource, LifestyleGoal
from app.models.lifestyle import DailyActivityLog, LifestyleProfile
from app.models.user import User
from app.services.lifestyle_service import (
    compute_daily_lifestyle_score,
    get_daily_lifestyle_summary,
)

router = APIRouter(prefix="/lifestyle", tags=["lifestyle"])


def ensure_user_exists(user_id: UUID, db: Session) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")


def _lifestyle_profile_to_dict(profile: LifestyleProfile) -> dict:
    return {
        "id": str(profile.id),
        "lifestyle_goal": profile.lifestyle_goal.value if profile.lifestyle_goal else None,
        "daily_steps_target": profile.daily_steps_target,
        "sleep_target_minutes": profile.sleep_target_minutes,
        "hydration_target_ml": profile.hydration_target_ml,
        "wants_activity_suggestions": profile.wants_activity_suggestions,
    }


# ============================================================
# PROFIL LIFESTYLE (partie 11)
# ============================================================

class LifestyleProfileUpsert(BaseModel):
    lifestyle_goal: Optional[LifestyleGoal] = None
    daily_steps_target: Optional[int] = Field(default=None, ge=0)
    sleep_target_minutes: Optional[int] = Field(default=None, ge=0)
    hydration_target_ml: Optional[int] = Field(default=None, ge=0)
    wants_activity_suggestions: bool = True


@router.post("/profile/{user_id}", status_code=201)
def upsert_lifestyle_profile(user_id: UUID, payload: LifestyleProfileUpsert, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)

    profile = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user_id)
    ).scalar_one_or_none()

    if profile is None:
        profile = LifestyleProfile(user_id=user_id)
        db.add(profile)

    profile.lifestyle_goal = payload.lifestyle_goal
    profile.daily_steps_target = payload.daily_steps_target
    profile.sleep_target_minutes = payload.sleep_target_minutes
    profile.hydration_target_ml = payload.hydration_target_ml
    profile.wants_activity_suggestions = payload.wants_activity_suggestions

    db.commit()
    db.refresh(profile)
    return _lifestyle_profile_to_dict(profile)


@router.get("/profile/{user_id}")
def get_lifestyle_profile(user_id: UUID, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    profile = db.execute(
        select(LifestyleProfile).where(LifestyleProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        # Jamais une erreur : un utilisateur sans LifestyleProfile est un
        # etat valide (partie 11), pas un profil manquant a corriger.
        return None
    return _lifestyle_profile_to_dict(profile)


# ============================================================
# ACTIVITE QUOTIDIENNE (partie 12)
# ============================================================

class DailyActivityLogUpsert(BaseModel):
    log_date: Optional[date] = None
    steps: Optional[int] = Field(default=None, ge=0)
    walking_duration_minutes: Optional[int] = Field(default=None, ge=0)
    distance_m: Optional[float] = Field(default=None, ge=0)
    active_minutes: Optional[int] = Field(default=None, ge=0)
    source: ActivityDataSource = ActivityDataSource.MANUAL


def _activity_log_to_dict(log: DailyActivityLog) -> dict:
    return {
        "id": str(log.id),
        "log_date": log.log_date.isoformat(),
        "steps": log.steps,
        "walking_duration_minutes": log.walking_duration_minutes,
        "distance_m": float(log.distance_m) if log.distance_m is not None else None,
        "active_minutes": log.active_minutes,
        "source": log.source.value,
    }


@router.post("/activity/{user_id}", status_code=201)
def upsert_daily_activity(user_id: UUID, payload: DailyActivityLogUpsert, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    log_date = payload.log_date or date.today()

    log = db.execute(
        select(DailyActivityLog).where(
            DailyActivityLog.user_id == user_id, DailyActivityLog.log_date == log_date
        )
    ).scalar_one_or_none()

    if log is None:
        log = DailyActivityLog(user_id=user_id, log_date=log_date)
        db.add(log)

    log.steps = payload.steps
    log.walking_duration_minutes = payload.walking_duration_minutes
    log.distance_m = Decimal(str(payload.distance_m)) if payload.distance_m is not None else None
    log.active_minutes = payload.active_minutes
    log.source = payload.source

    db.commit()
    db.refresh(log)
    return _activity_log_to_dict(log)


@router.get("/activity/{user_id}")
def list_daily_activity(
    user_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    ensure_user_exists(user_id, db)
    query = select(DailyActivityLog).where(DailyActivityLog.user_id == user_id)
    if start_date:
        query = query.where(DailyActivityLog.log_date >= start_date)
    if end_date:
        query = query.where(DailyActivityLog.log_date <= end_date)
    logs = db.execute(query.order_by(DailyActivityLog.log_date.desc())).scalars().all()
    return [_activity_log_to_dict(log) for log in logs]


# ============================================================
# AUJOURD'HUI (activite quotidienne + suggestions, partie 14)
# ============================================================

@router.get("/today/{user_id}")
def get_lifestyle_today(user_id: UUID, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    return get_daily_lifestyle_summary(db, user_id)


# ============================================================
# DAILY HEALTH SCORE (partie 13)
# ============================================================

@router.get("/score/{user_id}")
def get_lifestyle_score(user_id: UUID, on_date: Optional[date] = None, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    return compute_daily_lifestyle_score(db, user_id, on_date=on_date)
