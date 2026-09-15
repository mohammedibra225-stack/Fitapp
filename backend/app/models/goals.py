from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import GoalCategory

if TYPE_CHECKING:
    from app.models.sport import Sport


class Goal(UUIDPKMixin, TimestampMixin, Base):
    """Objectif sportif ou global, extensible et traduisible."""

    __tablename__ = "goals"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[GoalCategory] = mapped_column(
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    translations: Mapped[List["GoalTranslation"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    sport_goals: Mapped[List["SportGoalMatrix"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Goal slug={self.slug!r}>"


class GoalTranslation(UUIDPKMixin, Base):
    __tablename__ = "goal_translations"
    __table_args__ = (
        UniqueConstraint("goal_id", "language_code", name="uq_goal_translation"),
    )

    goal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    goal: Mapped["Goal"] = relationship(back_populates="translations")


class SportGoalMatrix(UUIDPKMixin, TimestampMixin, Base):
    """Matrice de pertinence sport x objectif. Donnee de reference pour la generation."""

    __tablename__ = "sport_goal_matrix"
    __table_args__ = (
        UniqueConstraint("sport_id", "goal_id", name="uq_sport_goal_matrix"),
    )

    sport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="CASCADE"),
        index=True,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        index=True,
    )
    relevance_score: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.0,
    )
    priority: Mapped[int] = mapped_column(default=0)
    is_primary: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    sport: Mapped["Sport"] = relationship(back_populates="sport_goals")
    goal: Mapped["Goal"] = relationship(back_populates="sport_goals")

    def __repr__(self) -> str:
        return f"<SportGoalMatrix sport_id={self.sport_id} goal_id={self.goal_id}>"
