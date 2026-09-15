
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import FoodDataSource, HalalStatus


class Food(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "foods"

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    is_liquid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    calories_kcal: Mapped[float] = mapped_column(
        Numeric(6, 2),
    )

    protein_g: Mapped[float] = mapped_column(
        Numeric(6, 2),
        default=0,
    )

    carbs_g: Mapped[float] = mapped_column(
        Numeric(6, 2),
        default=0,
    )

    fat_g: Mapped[float] = mapped_column(
        Numeric(6, 2),
        default=0,
    )

    fiber_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    sugar_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    sodium_mg: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )

    saturated_fat_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    default_unit: Mapped[str] = mapped_column(
        String(10),
        default="g",
    )
    unit_weight_g: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )

    # --- Enrichissement / import externe (Open Food Facts) ---
    brand: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    halal_status: Mapped[HalalStatus] = mapped_column(
        Enum(
            HalalStatus,
            name="halal_status",
            # La migration cree le type Postgres avec les *values*
            # ('halal', 'not_halal', 'unknown'). Sans values_callable,
            # SQLAlchemy attend les *names* ('HALAL', ...) et la lecture
            # d'une ligne existante leve:
            # LookupError: 'unknown' is not among the defined enum values.
            values_callable=lambda e: [m.value for m in e],
        ),
        default=HalalStatus.UNKNOWN,
        server_default=HalalStatus.UNKNOWN.value,
    )

    # D'ou vient cet aliment : saisie manuelle ou import Open Food Facts.
    source: Mapped[FoodDataSource] = mapped_column(
        Enum(
            FoodDataSource,
            name="food_data_source",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=FoodDataSource.MANUAL,
        server_default=FoodDataSource.MANUAL.value,
    )

    # Identifiant chez la source externe (ex: code produit Open Food Facts).
    # Distinct du barcode : certaines sources n'utilisent pas de code-barres.
    source_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    barcode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
    )

    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    translations: Mapped[List["FoodTranslation"]] = relationship(
        back_populates="food",
        cascade="all, delete-orphan",
    )

    prices: Mapped[List["FoodPrice"]] = relationship(
        back_populates="food",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Food slug={self.slug!r}>"


class FoodTranslation(UUIDPKMixin, Base):
    __tablename__ = "food_translations"

    __table_args__ = (
        UniqueConstraint(
            "food_id",
            "language_code",
            name="uq_food_translation",
        ),
    )

    food_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "foods.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    language_code: Mapped[str] = mapped_column(
        String(5),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
    )

    food: Mapped["Food"] = relationship(
        back_populates="translations",
    )

    def __repr__(self) -> str:
        return (
            f"<FoodTranslation "
            f"food_id={self.food_id} "
            f"lang={self.language_code}>"
        )


class FoodPrice(UUIDPKMixin, TimestampMixin, Base):


    __tablename__ = "food_prices"

    food_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "foods.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    price_da: Mapped[float] = mapped_column(
        Numeric(10, 2),
    )

    quantity: Mapped[float] = mapped_column(
        Numeric(10, 3),
    )

    unit: Mapped[str] = mapped_column(
        String(10),
    )

    valid_from: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # --- Enrichissement / import externe (Open Prices) ---
    # price_da reste le prix de reference (regle 11 : DZD par defaut) ;
    # currency permet de savoir si un prix importe est deja en DZD ou non.
    currency: Mapped[str] = mapped_column(
        String(3),
        default="DZD",
        server_default="DZD",
    )

    source: Mapped[FoodDataSource] = mapped_column(
        Enum(
            FoodDataSource,
            name="food_price_data_source",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=FoodDataSource.MANUAL,
        server_default=FoodDataSource.MANUAL.value,
    )

    source_id: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    store_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    location: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    food: Mapped["Food"] = relationship(
        back_populates="prices",
    )

    def __repr__(self) -> str:
        return (
            f"<FoodPrice "
            f"food_id={self.food_id} "
            f"price_da={self.price_da} "
            f"quantity={self.quantity} "
            f"unit={self.unit!r}>"
        )

