"""Suivi de l'hydratation (regle 10)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class WaterLog(UUIDPKMixin, Base):
    __tablename__ = "water_logs"
    __table_args__ = (Index("ix_water_logs_user_date", "user_id", "logged_on"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quantity_ml: Mapped[int] = mapped_column(SmallInteger)
    logged_on: Mapped[date] = mapped_column(Date, index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="water_logs")

    def __repr__(self) -> str:
        return f"<WaterLog user_id={self.user_id} qty={self.quantity_ml}ml>"
