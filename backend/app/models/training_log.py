"""
Historique reel des seances effectuees + records personnels
(regles 16 et 17).

Separe de training.py (planification) : WorkoutLog est ce qui s'est
VRAIMENT passe, avec un lien optionnel vers le Workout planifie dont
il decoule (`based_on_workout_id`), pour comparer prevu vs realise.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, SmallInteger, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import RecordType

if TYPE_CHECKING:
    from app.models.sport import Sport
    from app.models.training import Exercise, Workout
    from app.models.user import User


class WorkoutLog(UUIDPKMixin, TimestampMixin, Base):
    """Une seance reellement effectuee (regle 16)."""

    __tablename__ = "workout_logs"
    __table_args__ = (
        Index("ix_workout_logs_user_performed", "user_id", "performed_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    based_on_workout_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workouts.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    overall_rpe: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    calories_burned: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="workout_logs")
    based_on_workout: Mapped[Optional["Workout"]] = relationship()
    exercises: Mapped[List["WorkoutLogExercise"]] = relationship(
        back_populates="workout_log", cascade="all, delete-orphan"
    )


class WorkoutLogExercise(UUIDPKMixin, Base):
    __tablename__ = "workout_log_exercises"

    workout_log_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_logs.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    workout_log: Mapped["WorkoutLog"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
    sets: Mapped[List["WorkoutLogSet"]] = relationship(
        back_populates="workout_log_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutLogSet.set_number",
    )


class WorkoutLogSet(UUIDPKMixin, Base):
    """Une serie REELLEMENT effectuee (regle 16 : poids, reps, duree, RPE...)."""

    __tablename__ = "workout_log_sets"

    workout_log_exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_log_exercises.id", ondelete="CASCADE"),
        index=True,
    )
    set_number: Mapped[int] = mapped_column(SmallInteger)

    reps: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    distance_m: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    rest_seconds: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    # Rate of Perceived Exertion, echelle 1-10
    rpe: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workout_log_exercise: Mapped["WorkoutLogExercise"] = relationship(
        back_populates="sets"
    )


class PersonalRecord(UUIDPKMixin, Base):
    """
    Records personnels (regle 17), fonctionne pour tout sport : un PR
    peut etre lie a un exercice (muscu) OU a un sport (ex: meilleur
    temps 10km en course), jamais les deux.
    """

    __tablename__ = "personal_records"
    __table_args__ = (
        Index("ix_personal_records_user_type", "user_id", "record_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="SET NULL"),
        nullable=True,
    )
    sport_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="SET NULL"),
        nullable=True,
    )

    record_type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, name="record_type")
    )
    value: Mapped[float] = mapped_column(Numeric(9, 2))
    unit: Mapped[str] = mapped_column(Text)  # "kg", "s", "m", "reps"...
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # Lien optionnel vers la serie loguee qui a produit ce record
    source_set_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_log_sets.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="personal_records")
    exercise: Mapped[Optional["Exercise"]] = relationship()
    sport: Mapped[Optional["Sport"]] = relationship()

    def __repr__(self) -> str:
        return f"<PersonalRecord user_id={self.user_id} type={self.record_type} value={self.value}>"
