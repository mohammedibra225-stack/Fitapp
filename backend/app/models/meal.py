"""
Repas consommes par l'utilisateur (regle 8).

Un `Meal` est un repas reellement enregistre (log), compose de
plusieurs `MealItem` (aliments + quantite). Les calories/macros sont
calculees a l'insertion et stockees (denormalisation volontaire) pour
eviter de recalculer a chaque lecture d'historique.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import MealType, MeasurementUnit

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.recipe import Recipe
    from app.models.user import User


class Meal(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_date", "user_id", "consumed_on"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType, name="meal_type"))
    consumed_on: Mapped[date] = mapped_column(Date, index=True)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # Totaux denormalises (somme des meal_items), pour lecture rapide
    total_calories_kcal: Mapped[float] = mapped_column(Numeric(7, 2), default=0)
    total_protein_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    total_carbs_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    total_fat_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)

    # --- Relations ---
    user: Mapped["User"] = relationship(back_populates="meals")
    items: Mapped[List["MealItem"]] = relationship(
        back_populates="meal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Meal id={self.id} type={self.meal_type} date={self.consumed_on}>"


class MealItem(UUIDPKMixin, Base):
    """
    Un aliment (ou une recette) au sein d'un repas, avec sa quantite.
    Exactement une des deux FK (food_id / recipe_id) doit etre remplie.
    """

    __tablename__ = "meal_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meals.id", ondelete="CASCADE"), index=True
    )
    food_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("foods.id", ondelete="RESTRICT"), nullable=True
    )
    recipe_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=True,
    )

    quantity: Mapped[float] = mapped_column(Numeric(7, 2))
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit, name="measurement_unit")
    )

    # Calories/macros calculees pour CETTE quantite precise (pas pour
    # 100g) -> evite de reconvertir a chaque affichage de l'historique.
    calories_kcal: Mapped[float] = mapped_column(Numeric(7, 2))
    protein_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    carbs_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    fat_g: Mapped[float] = mapped_column(Numeric(6, 2), default=0)

    meal: Mapped["Meal"] = relationship(back_populates="items")
    food: Mapped[Optional["Food"]] = relationship()
    recipe: Mapped[Optional["Recipe"]] = relationship()

    def __repr__(self) -> str:
        return f"<MealItem meal_id={self.meal_id} qty={self.quantity}{self.unit}>"
