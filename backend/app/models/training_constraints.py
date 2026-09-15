from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class TrainingConstraint(UUIDPKMixin, TimestampMixin, Base):
    """Contrainte d'entraînement pour un utilisateur ou un profil."""

    __tablename__ = "training_constraints"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(40), index=True)
    constraint_type: Mapped[str] = mapped_column(String(60), index=True)
    value: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="training_constraints")

    def __repr__(self) -> str:
        return f"<TrainingConstraint type={self.constraint_type!r} active={self.active}>"
