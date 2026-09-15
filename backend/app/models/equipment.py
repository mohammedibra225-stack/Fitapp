from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.sport import Sport


class Equipment(UUIDPKMixin, TimestampMixin, Base):
    """Catalogue d'équipements utilisables dans les sports et exercices."""

    __tablename__ = "equipment"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True, default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    translations: Mapped[List["EquipmentTranslation"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
    )
    sport_equipment: Mapped[List["SportEquipment"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Equipment slug={self.slug!r}>"


class EquipmentTranslation(UUIDPKMixin, Base):
    __tablename__ = "equipment_translations"
    __table_args__ = (
        UniqueConstraint("equipment_id", "language_code", name="uq_equipment_translation"),
    )

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    equipment: Mapped["Equipment"] = relationship(back_populates="translations")


class SportEquipment(UUIDPKMixin, TimestampMixin, Base):
    """Relation sport -> équipement avec priorité et statut requis/optionnel."""

    __tablename__ = "sport_equipment"
    __table_args__ = (
        UniqueConstraint("sport_id", "equipment_id", name="uq_sport_equipment"),
    )

    sport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="CASCADE"),
        index=True,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        index=True,
    )
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(default=0)
    notes: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    sport: Mapped["Sport"] = relationship(back_populates="sport_equipment")
    equipment: Mapped["Equipment"] = relationship(back_populates="sport_equipment")


class Environment(UUIDPKMixin, TimestampMixin, Base):
    """Environnement de pratique (home, gym, outdoor, pool, etc.)."""

    __tablename__ = "environments"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True, default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    translations: Mapped[List["EnvironmentTranslation"]] = relationship(
        back_populates="environment",
        cascade="all, delete-orphan",
    )
    sport_environments: Mapped[List["SportEnvironment"]] = relationship(
        back_populates="environment",
        cascade="all, delete-orphan",
    )


class EnvironmentTranslation(UUIDPKMixin, Base):
    __tablename__ = "environment_translations"
    __table_args__ = (
        UniqueConstraint("environment_id", "language_code", name="uq_environment_translation"),
    )

    environment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    environment: Mapped["Environment"] = relationship(back_populates="translations")


class SportEnvironment(UUIDPKMixin, TimestampMixin, Base):
    """Relation sport -> environnement supporté."""

    __tablename__ = "sport_environment"
    __table_args__ = (
        UniqueConstraint("sport_id", "environment_id", name="uq_sport_environment"),
    )

    sport_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="CASCADE"),
        index=True,
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        index=True,
    )
    supported: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(default=0)
    notes: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    sport: Mapped["Sport"] = relationship(back_populates="sport_environments")
    environment: Mapped["Environment"] = relationship(back_populates="sport_environments")
