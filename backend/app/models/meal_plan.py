

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, JSON, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import GoalType, MealType, MeasurementUnit

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.recipe import Recipe
    from app.models.user import User


class MealPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "meal_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    goal: Mapped[Optional[GoalType]] = mapped_column(
        Enum(GoalType, name="meal_plan_goal_type"), nullable=True
    )

    target_calories_kcal: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    target_protein_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    target_carbs_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    target_fat_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="meal_plans")
    days: Mapped[List["MealPlanDay"]] = relationship(
        back_populates="meal_plan",
        cascade="all, delete-orphan",
        order_by="MealPlanDay.day_number",
    )

    def __repr__(self) -> str:
        return f"<MealPlan id={self.id} name={self.name!r}>"


class MealPlanDay(UUIDPKMixin, Base):
    __tablename__ = "meal_plan_days"
    __table_args__ = (
        Index("ix_meal_plan_days_plan_number", "meal_plan_id", "day_number"),
    )

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        index=True,
    )
    # 1 = premier jour du plan, 2 = deuxieme jour, etc.
    day_number: Mapped[int] = mapped_column(SmallInteger)
    # Libelle optionnel ("Monday", "Jour de repos"...)
    label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    meal_plan: Mapped["MealPlan"] = relationship(back_populates="days")
    meals: Mapped[List["MealPlanMeal"]] = relationship(
        back_populates="meal_plan_day", cascade="all, delete-orphan"
    )


class MealPlanMeal(UUIDPKMixin, Base):
    __tablename__ = "meal_plan_meals"

    meal_plan_day_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_plan_days.id", ondelete="CASCADE"),
        index=True,
    )
    meal_type: Mapped[MealType] = mapped_column(
        Enum(MealType, name="meal_plan_meal_type")
    )

    # Cibles de ce repas, obtenues en repartissant les cibles quotidiennes
    # du MealPlan selon le type de repas (regle : repartition des repas).
    # Restent NULL tant qu'aucune repartition n'a ete generee.
    target_calories_kcal: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    target_protein_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    target_carbs_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    target_fat_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    spoonacular_recipe_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spoonacular_recipe_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    meal_plan_day: Mapped["MealPlanDay"] = relationship(back_populates="meals")
    items: Mapped[List["MealPlanMealItem"]] = relationship(
        back_populates="meal_plan_meal", cascade="all, delete-orphan"
    )


class MealPlanMealItem(UUIDPKMixin, Base):
    """Aliment ou recette prevu pour un MealPlanMeal donne."""

    __tablename__ = "meal_plan_meal_items"

    meal_plan_meal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_plan_meals.id", ondelete="CASCADE"),
        index=True,
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
        Enum(MeasurementUnit, name="meal_plan_measurement_unit")
    )

    meal_plan_meal: Mapped["MealPlanMeal"] = relationship(back_populates="items")
    food: Mapped[Optional["Food"]] = relationship()
    recipe: Mapped[Optional["Recipe"]] = relationship()
