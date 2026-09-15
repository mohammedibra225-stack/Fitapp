from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class TrainingPreference(UUIDPKMixin, TimestampMixin, Base):
    """Préférences de génération d'entraînement pour un utilisateur."""

    __tablename__ = "training_preferences"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    preferred_days: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    preferred_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_training_types: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    disliked_exercises: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preferred_sports: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="training_preferences")

    def __repr__(self) -> str:
        return f"<TrainingPreference user_id={self.user_id}>"
