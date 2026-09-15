"""
Sports pratiques par les utilisateurs (regle 4).

- `sports` / `sport_translations` : liste ouverte de sports (extensible
  sans migration : on insere une ligne, pas une nouvelle colonne/enum).
- `user_sports` : table d'association many-to-many (un utilisateur peut
  pratiquer plusieurs sports, avec un niveau/frequence/statut principal
  propres a chaque association).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, Boolean, Enum, ForeignKey, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import SportGoal, SportLevel

if TYPE_CHECKING:
    from app.models.equipment import SportEnvironment, SportEquipment
    from app.models.goals import SportGoalMatrix
    from app.models.user import User


class Sport(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sports"

    # Slug stable independant de la langue, utilise par le code
    # (ex: icones, regles metier specifiques a un sport).
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    translations: Mapped[List["SportTranslation"]] = relationship(
        back_populates="sport", cascade="all, delete-orphan"
    )
    user_sports: Mapped[List["UserSport"]] = relationship(back_populates="sport")
    sport_goals: Mapped[List["SportGoalMatrix"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
    )
    sport_equipment: Mapped[List["SportEquipment"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
    )
    sport_environments: Mapped[List["SportEnvironment"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Sport slug={self.slug!r}>"


class SportTranslation(UUIDPKMixin, Base):
    __tablename__ = "sport_translations"
    __table_args__ = (
        UniqueConstraint("sport_id", "language_code", name="uq_sport_translation"),
    )

    sport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sports.id", ondelete="CASCADE"), index=True
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(100))

    sport: Mapped["Sport"] = relationship(back_populates="translations")


class UserSport(Base):
    """
    Association many-to-many User <-> Sport, avec metadonnees propres
    a chaque pratique (regle 4 : niveau, frequence, sport principal).
    """

    __tablename__ = "user_sports"
    __table_args__ = (
        UniqueConstraint("user_id", "sport_id", name="uq_user_sport"),
        Index("ix_user_sports_user_primary", "user_id", "is_primary"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sports.id", ondelete="CASCADE"), index=True
    )

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[Optional[SportLevel]] = mapped_column(
        Enum(SportLevel, name="sport_level"), nullable=True
    )
    goal: Mapped[Optional[SportGoal]] = mapped_column(
        Enum(SportGoal, name="sport_goal"), nullable=True
    )
    # Nombre de sessions par semaine, approximatif
    frequency_per_week: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )
    preferred_duration_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )
    preferred_training_days: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(SmallInteger), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="sports")
    sport: Mapped["Sport"] = relationship(back_populates="user_sports")

    def __repr__(self) -> str:
        return f"<UserSport user_id={self.user_id} sport_id={self.sport_id}>"
