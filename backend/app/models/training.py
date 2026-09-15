"""
Entrainement : catalogue d'exercices + programmes/seances PLANIFIES
(regle 15).

Le LOG reel des seances effectuees vit dans training_log.py (regle 16)
-> separation planification / historique, comme pour meal_plan vs meal.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, Date, Enum, ForeignKey, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import DifficultyLevel, TrainingType

if TYPE_CHECKING:
    from app.models.sport import Sport
    from app.models.user import User


class Exercise(UUIDPKMixin, TimestampMixin, Base):
    """Catalogue global d'exercices (pompes, squat, course a pied...)."""

    __tablename__ = "exercises"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    sport_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Groupe musculaire / categorie principale (ex: "legs", "cardio")
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    muscle_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    equipment: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Types d'entrainement couverts par cet exercice (module Sport, partie 2).
    # Un exercice peut relever de plusieurs types a la fois
    # (ex: squat lourd -> STRENGTH + POWER).
    # values_callable oblige : sans cela SQLAlchemy envoie le *name*
    # Python ('STRENGTH') alors que le type Postgres ne connait que les
    # *values* ('strength'), meme convention que Food.halal_status.
    training_types: Mapped[Optional[List[TrainingType]]] = mapped_column(
        ARRAY(
            Enum(
                TrainingType,
                name="training_type",
                values_callable=lambda e: [m.value for m in e],
            )
        ),
        nullable=True,
    )
    difficulty: Mapped[Optional[DifficultyLevel]] = mapped_column(
        Enum(
            DifficultyLevel,
            name="exercise_difficulty",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    translations: Mapped[List["ExerciseTranslation"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )
    sport: Mapped[Optional["Sport"]] = relationship()

    def __repr__(self) -> str:
        return f"<Exercise slug={self.slug!r}>"


class ExerciseTranslation(UUIDPKMixin, Base):
    __tablename__ = "exercise_translations"
    __table_args__ = (
        UniqueConstraint(
            "exercise_id", "language_code", name="uq_exercise_translation"
        ),
    )

    exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    exercise: Mapped["Exercise"] = relationship(back_populates="translations")


class TrainingProgram(UUIDPKMixin, TimestampMixin, Base):
    """
    Programme d'entrainement (ex: "Prise de masse 12 semaines"),
    conteneur de plusieurs Workout planifies.
    """

    __tablename__ = "training_programs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sport_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="training_programs")
    workouts: Mapped[List["Workout"]] = relationship(back_populates="training_program")


class Workout(UUIDPKMixin, TimestampMixin, Base):
    """Une seance PLANIFIEE (template), rattachee ou non a un programme."""

    __tablename__ = "workouts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    training_program_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("training_programs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sport_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # --- Ajouts module Sport, partie 4 : metadonnees de la seance ---
    training_type: Mapped[Optional[TrainingType]] = mapped_column(
        Enum(
            TrainingType,
            name="workout_training_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    difficulty: Mapped[Optional[DifficultyLevel]] = mapped_column(
        Enum(
            DifficultyLevel,
            name="workout_difficulty",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    # Duree prevue en minutes (echauffement + exercices + retour au calme).
    planned_duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    # Intensite ciblee pour l'ensemble de la seance, echelle RPE 1-10
    # (module Sport, partie 8). Nullable : pas toujours definie a l'avance.
    target_rpe: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    # Estimation, jamais garantie a 100% (depend du poids/de l'effort reel).
    estimated_calories_kcal: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="workouts")
    training_program: Mapped[Optional["TrainingProgram"]] = relationship(
        back_populates="workouts"
    )
    sport: Mapped[Optional["Sport"]] = relationship()
    exercises: Mapped[List["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.display_order",
    )


class WorkoutExercise(UUIDPKMixin, Base):
    __tablename__ = "workout_exercises"

    workout_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
    sets: Mapped[List["WorkoutSet"]] = relationship(
        back_populates="workout_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.set_number",
    )


class WorkoutSet(UUIDPKMixin, Base):
    """Une serie PLANIFIEE (objectif), ex: "4 x 8 reps a 60kg"."""

    __tablename__ = "workout_sets"

    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_exercises.id", ondelete="CASCADE"),
        index=True,
    )
    set_number: Mapped[int] = mapped_column(SmallInteger)

    target_reps: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    target_weight_kg: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    target_duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    target_distance_m: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    rest_seconds: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    # Intensite ciblee pour cette serie precise (module Sport, partie 8).
    target_rpe: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)

    workout_exercise: Mapped["WorkoutExercise"] = relationship(back_populates="sets")
