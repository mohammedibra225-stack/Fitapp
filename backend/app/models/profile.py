from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ActivityLevel, BodyMetricType, GoalType, Sex, UnitSystem


if TYPE_CHECKING:
    from app.models.user import User


class Profile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    age: Mapped[Optional[int]] = mapped_column(nullable=True)

    sex: Mapped[Optional[Sex]] = mapped_column(
        Enum(Sex, name="sex"),
        nullable=True,
    )

    height_cm: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )

    current_weight_kg: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    activity_level: Mapped[Optional[ActivityLevel]] = mapped_column(
        Enum(ActivityLevel, name="activity_level"),
        nullable=True,
    )

    primary_goal: Mapped[Optional[GoalType]] = mapped_column(
        Enum(GoalType, name="goal_type"),
        nullable=True,
    )

    unit_system: Mapped[UnitSystem] = mapped_column(
        Enum(UnitSystem, name="unit_system"),
        default=UnitSystem.METRIC,
    )

    dietary_preferences: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    allergies: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    food_budget_per_week: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    # Contrainte obligatoire pour le moteur de recommandation de recettes
    # (regle 6/7) : distincte de dietary_preferences (texte libre) car elle
    # doit pouvoir exclure strictement des recettes/aliments non halal.
    halal_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    user: Mapped["User"] = relationship(
        back_populates="profile",
    )


class BodyMeasurement(UUIDPKMixin, Base):
    __tablename__ = "body_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    metric_type: Mapped[BodyMetricType] = mapped_column(
        Enum(BodyMetricType, name="body_metric_type"),
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Numeric(6, 2),
    )

    unit: Mapped[str] = mapped_column(
        String(10),
    )

    recorded_at: Mapped[date] = mapped_column(
        Date,
        index=True,
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="body_measurements",
    )