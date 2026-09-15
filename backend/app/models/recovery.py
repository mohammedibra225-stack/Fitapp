"""Suivi de la recuperation : sommeil, fatigue, stress (regle 19)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import SleepQuality

if TYPE_CHECKING:
    from app.models.user import User


class SleepLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sleep_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "sleep_date", name="uq_sleep_log_user_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sleep_date: Mapped[date] = mapped_column(Date, index=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    quality: Mapped[Optional[SleepQuality]] = mapped_column(
        Enum(SleepQuality, name="sleep_quality"), nullable=True
    )
    # Echelles simples 1-5, laissees libres cote app
    fatigue_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    stress_level: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sleep_logs")

    def __repr__(self) -> str:
        return f"<SleepLog user_id={self.user_id} date={self.sleep_date}>"
