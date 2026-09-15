

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.ai import Conversation
    from app.models.audit import AuditLog
    from app.models.food import FoodPlan  # noqa: F401 (reserve)
    from app.models.hydration import WaterLog
    from app.models.inventory import Inventory
    from app.models.lifestyle import DailyActivityLog, LifestyleProfile
    from app.models.meal import Meal
    from app.models.meal_plan import MealPlan
    from app.models.notification import NotificationLog, NotificationSetting
    from app.models.profile import BodyMeasurement, Profile
    from app.models.recovery import SleepLog
    from app.models.sport import UserSport
    from app.models.training import TrainingProgram, Workout
    from app.models.training_constraints import TrainingConstraint
    from app.models.training_log import PersonalRecord, WorkoutLog
    from app.models.training_preferences import TrainingPreference


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Langue preferee : doit correspondre a un code de
    # app.i18n.languages.SUPPORTED_LANGUAGES ("fr", "en", "es", "ar").
    # Pas de FK vers une table "languages" car les langues sont definies
    # dans le code (source de verite unique), pas en base (regle 25).
    preferred_language: Mapped[str] = mapped_column(String(5), default="fr")

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Prevu pour un compte cloud futur (regle 1) ---
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    auth_provider: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )  # ex: "google", "apple", "email"
    external_auth_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # --- Relations ---
    profile: Mapped[Optional["Profile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    lifestyle_profile: Mapped[Optional["LifestyleProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    daily_activity_logs: Mapped[List["DailyActivityLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    body_measurements: Mapped[List["BodyMeasurement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sports: Mapped[List["UserSport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    meals: Mapped[List["Meal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    meal_plans: Mapped[List["MealPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    water_logs: Mapped[List["WaterLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    inventories: Mapped[List["Inventory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    training_programs: Mapped[List["TrainingProgram"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    workouts: Mapped[List["Workout"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    workout_logs: Mapped[List["WorkoutLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    personal_records: Mapped[List["PersonalRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sleep_logs: Mapped[List["SleepLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    training_constraints: Mapped[List["TrainingConstraint"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    training_preferences: Mapped[List["TrainingPreference"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_settings: Mapped[List["NotificationSetting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_logs: Mapped[List["NotificationLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
