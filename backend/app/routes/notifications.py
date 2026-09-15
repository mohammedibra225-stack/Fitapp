from datetime import datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import NotificationType
from app.models.notification import NotificationLog, NotificationSetting
from app.models.user import User
from app.services.notifications import create_due_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationSettingCreate(BaseModel):
    notification_type: NotificationType
    scheduled_time: time | None = None
    days_of_week: list[int] = Field(default_factory=lambda: list(range(7)))
    title: str | None = Field(default=None, max_length=150)
    body: str | None = None
    is_enabled: bool = True
    language_code: str = Field(default="fr", min_length=2, max_length=5)

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, days: list[int]) -> list[int]:
        if len(set(days)) != len(days) or any(day < 0 or day > 6 for day in days):
            raise ValueError("days_of_week doit contenir des jours uniques de 0 a 6.")
        return sorted(days)


class NotificationSettingOut(NotificationSettingCreate):
    id: UUID
    user_id: UUID
    created_at: object
    updated_at: object

    model_config = {"from_attributes": True}


class NotificationLogOut(BaseModel):
    id: UUID
    user_id: UUID
    notification_setting_id: UUID | None
    notification_type: NotificationType
    title: str
    body: str | None
    language_code: str
    is_read: bool
    sent_at: object

    model_config = {"from_attributes": True}


class NotificationLogCreate(BaseModel):
    notification_type: NotificationType
    title: str = Field(min_length=1, max_length=150)
    body: str | None = None
    language_code: str = Field(default="fr", min_length=2, max_length=5)
    notification_setting_id: UUID | None = None


@router.get("/types")
def list_notification_types() -> list[str]:
    return [notification_type.value for notification_type in NotificationType]


@router.post("/process-due", response_model=list[NotificationLogOut])
def process_due_notifications(
    at: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Generate today's due logs; a scheduler can call this endpoint later."""
    return create_due_notifications(db, at)


@router.get("/settings/{user_id}", response_model=list[NotificationSettingOut])
def list_settings(user_id: UUID, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    return db.execute(
        select(NotificationSetting)
        .where(NotificationSetting.user_id == user_id)
        .order_by(NotificationSetting.scheduled_time, NotificationSetting.created_at)
    ).scalars().all()


@router.post("/settings/{user_id}", response_model=NotificationSettingOut, status_code=201)
def create_setting(user_id: UUID, payload: NotificationSettingCreate, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    setting = NotificationSetting(user_id=user_id, **payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.patch("/settings/{setting_id}", response_model=NotificationSettingOut)
def update_setting(setting_id: UUID, payload: NotificationSettingCreate, db: Session = Depends(get_db)):
    setting = db.get(NotificationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Reglage de notification introuvable.")
    for field, value in payload.model_dump().items():
        setattr(setting, field, value)
    db.commit()
    db.refresh(setting)
    return setting


@router.delete("/settings/{setting_id}", status_code=204)
def delete_setting(setting_id: UUID, db: Session = Depends(get_db)):
    setting = db.get(NotificationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Reglage de notification introuvable.")
    db.delete(setting)
    db.commit()


@router.post("/logs/{user_id}", response_model=NotificationLogOut, status_code=201)
def create_log(user_id: UUID, payload: NotificationLogCreate, db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    if payload.notification_setting_id:
        setting = db.get(NotificationSetting, payload.notification_setting_id)
        if setting is None or setting.user_id != user_id:
            raise HTTPException(status_code=404, detail="Reglage de notification introuvable.")
    log = NotificationLog(user_id=user_id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/logs/{user_id}", response_model=list[NotificationLogOut])
def list_logs(user_id: UUID, unread_only: bool = False, limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    ensure_user_exists(user_id, db)
    query = select(NotificationLog).where(NotificationLog.user_id == user_id)
    if unread_only:
        query = query.where(NotificationLog.is_read.is_(False))
    return db.execute(query.order_by(NotificationLog.sent_at.desc()).limit(limit)).scalars().all()


@router.patch("/logs/{log_id}/read", response_model=NotificationLogOut)
def mark_log_read(log_id: UUID, db: Session = Depends(get_db)):
    log = db.get(NotificationLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Notification introuvable.")
    log.is_read = True
    db.commit()
    db.refresh(log)
    return log


def ensure_user_exists(user_id: UUID, db: Session) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")