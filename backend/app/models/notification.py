"""Notifications (regle 22)."""

from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import NotificationType

if TYPE_CHECKING:
    from app.models.user import User


class NotificationSetting(UUIDPKMixin, TimestampMixin, Base):
    """Configuration d'un rappel recurrent (heure, jours, contenu, langue)."""

    __tablename__ = "notification_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type")
    )
    scheduled_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    days_of_week: Mapped[list[int]] = mapped_column(
        JSON, default=lambda: [0, 1, 2, 3, 4, 5, 6]
    )
    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    language_code: Mapped[str] = mapped_column(String(5), default="fr")

    user: Mapped["User"] = relationship(back_populates="notification_settings")


class NotificationLog(UUIDPKMixin, Base):
    """Historique des notifications effectivement envoyees."""

    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    notification_setting_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_settings.id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_log_type")
    )
    title: Mapped[str] = mapped_column(String(150))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language_code: Mapped[str] = mapped_column(String(5), default="fr")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="notification_logs")
