"""
Profil "mode de vie sain" pour les utilisateurs non-sportifs ou en plus
du sport (module Sport, parties 11 et 12).

Separe de `Profile` (qui reste le profil nutritionnel/anthropometrique
utilise par le moteur de calories) : `LifestyleProfile` porte les
objectifs et cibles specifiques au mode de vie (pas, sommeil, hydratation),
optionnels et jamais obligatoires pour utiliser Fitapp.

`DailyActivityLog` separe l'activite quotidienne (marche, pas, escaliers)
du sport structure (Workout/WorkoutLog) : l'absence de sport ne doit
jamais etre interpretee comme une absence d'activite.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ActivityDataSource, LifestyleGoal

if TYPE_CHECKING:
    from app.models.user import User


class LifestyleProfile(UUIDPKMixin, TimestampMixin, Base):
    """
    Preferences et cibles "mode de vie sain", independantes du sport.

    Un utilisateur sans aucune pratique sportive (sport = none) peut
    avoir un LifestyleProfile complet ; un utilisateur sportif peut
    aussi en avoir un en complement (ex: objectif sommeil).
    """

    __tablename__ = "lifestyle_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    # values_callable oblige, meme raison que Food.halal_status : le type
    # Postgres ne connait que les *values* ('eat_healthier', ...).
    lifestyle_goal: Mapped[Optional[LifestyleGoal]] = mapped_column(
        Enum(
            LifestyleGoal,
            name="lifestyle_goal",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )

    # Cibles facultatives : restent NULL tant que l'utilisateur ne les a
    # pas definies, sans jamais forcer une valeur par defaut arbitraire.
    daily_steps_target: Mapped[Optional[int]] = mapped_column(nullable=True)
    sleep_target_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    # Surcharge optionnelle de l'objectif d'hydratation calcule par
    # app.services.hydration ; NULL = on garde le calcul automatique.
    hydration_target_ml: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Active ou non les suggestions d'activites facultatives
    # (module Sport, partie 14 : marche 10 min, etirements...).
    wants_activity_suggestions: Mapped[bool] = mapped_column(default=True)

    user: Mapped["User"] = relationship(back_populates="lifestyle_profile")

    def __repr__(self) -> str:
        return f"<LifestyleProfile user_id={self.user_id}>"


class DailyActivityLog(UUIDPKMixin, TimestampMixin, Base):
    """
    Activite quotidienne "informelle" (marche, pas, deplacements),
    distincte du sport structure (module Sport, partie 12).
    """

    __tablename__ = "daily_activity_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_daily_activity_user_date"),
        Index("ix_daily_activity_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    log_date: Mapped[date] = mapped_column(Date, index=True)

    steps: Mapped[Optional[int]] = mapped_column(nullable=True)
    walking_duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    distance_m: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    active_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    source: Mapped[ActivityDataSource] = mapped_column(
        Enum(
            ActivityDataSource,
            name="activity_data_source",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ActivityDataSource.MANUAL,
    )

    user: Mapped["User"] = relationship(back_populates="daily_activity_logs")

    def __repr__(self) -> str:
        return f"<DailyActivityLog user_id={self.user_id} date={self.log_date}>"
