

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import (
    DifficultyLevel,
    HalalStatus,
    IngredientMatchStatus,
    MeasurementUnit,
    MealType,
    RecipeCostStatus,
    RecipeDataSource,
    RecipeNutritionStatus,
    VideoPlatform,
)

if TYPE_CHECKING:
    from app.models.food import Food


class Recipe(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "recipes"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)

    prep_time_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )
    cook_time_minutes: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )
    difficulty: Mapped[Optional[DifficultyLevel]] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), nullable=True
    )
    servings: Mapped[int] = mapped_column(SmallInteger, default=1)

    # Totaux nutritionnels PAR PORTION (denormalise depuis les
    # ingredients, recalcule quand la recette est modifiee).
    calories_kcal: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fiber_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    sugar_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)

    # Fiabilite du calcul ci-dessus (regle 6/26 : ne jamais presenter
    # un total partiel comme s'il etait complet). Calcule/rafraichi par
    # app.services.recipe_enrichment, jamais devine a l'import.
    nutrition_status: Mapped[RecipeNutritionStatus] = mapped_column(
        Enum(RecipeNutritionStatus, name="recipe_nutrition_status", values_callable=lambda e: [m.value for m in e]),
        default=RecipeNutritionStatus.UNKNOWN,
        server_default=RecipeNutritionStatus.UNKNOWN.value,
    )

    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Champs de filtrage pour la recommandation (regle 13) ---
    estimated_cost_level: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )  # 1 = economique ... 3 = cher

    # Cout reel calcule depuis Food/FoodPrice (regle 8), distinct de
    # estimated_cost_level (qui reste un niveau grossier 1-3 manuel).
    # Jamais 0 DA pour representer un prix inconnu : voir cost_status.
    cost_per_serving_da: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    cost_status: Mapped[RecipeCostStatus] = mapped_column(
        Enum(RecipeCostStatus, name="recipe_cost_status", values_callable=lambda e: [m.value for m in e]),
        default=RecipeCostStatus.UNKNOWN,
        server_default=RecipeCostStatus.UNKNOWN.value,
    )

    is_vegetarian: Mapped[bool] = mapped_column(default=False)
    is_vegan: Mapped[bool] = mapped_column(default=False)
    is_halal: Mapped[bool] = mapped_column(default=False)
    is_gluten_free: Mapped[bool] = mapped_column(default=False)

    # Statut halal reel a 3 valeurs (regle 10), source de verite pour
    # le filtrage. is_halal (bool) reste tenu en synchro (is_halal =
    # halal_status == HALAL) pour ne pas casser le code existant qui
    # le lit deja (recipe_recommender, seed_recipes).
    halal_status: Mapped[HalalStatus] = mapped_column(
        Enum(HalalStatus, name="recipe_halal_status", values_callable=lambda e: [m.value for m in e]),
        default=HalalStatus.UNKNOWN,
        server_default=HalalStatus.UNKNOWN.value,
    )

    cuisine: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    meal_type: Mapped[Optional[MealType]] = mapped_column(
        Enum(MealType, name="recipe_meal_type", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )

    # --- Tracabilite d'import (regle 20/21 : deduplication, ne pas
    # importer deux fois la meme recette externe) ---
    source: Mapped[RecipeDataSource] = mapped_column(
        Enum(RecipeDataSource, name="recipe_data_source", values_callable=lambda e: [m.value for m in e]),
        default=RecipeDataSource.MANUAL,
        server_default=RecipeDataSource.MANUAL.value,
    )
    source_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Relations ---
    translations: Mapped[List["RecipeTranslation"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    unmapped_ingredients: Mapped[List["UnmappedRecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    steps: Mapped[List["RecipeStep"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeStep.step_number",
    )
    videos: Mapped[List["RecipeVideo"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Recipe slug={self.slug!r}>"


class RecipeTranslation(UUIDPKMixin, Base):
    __tablename__ = "recipe_translations"
    __table_args__ = (
        UniqueConstraint("recipe_id", "language_code", name="uq_recipe_translation"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="translations")


class RecipeIngredient(UUIDPKMixin, Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        index=True,
    )
    food_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("foods.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(7, 2))
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit, name="recipe_ingredient_unit")
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    food: Mapped["Food"] = relationship()


class RecipeStep(UUIDPKMixin, Base):
    __tablename__ = "recipe_steps"
    __table_args__ = (
        UniqueConstraint("recipe_id", "step_number", name="uq_recipe_step_number"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        index=True,
    )
    step_number: Mapped[int] = mapped_column(SmallInteger)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="steps")
    translations: Mapped[List["RecipeStepTranslation"]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )


class RecipeStepTranslation(UUIDPKMixin, Base):
    __tablename__ = "recipe_step_translations"
    __table_args__ = (
        UniqueConstraint(
            "recipe_step_id", "language_code", name="uq_recipe_step_translation"
        ),
    )

    recipe_step_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipe_steps.id", ondelete="CASCADE"),
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(5), index=True)
    instruction: Mapped[str] = mapped_column(Text)

    step: Mapped["RecipeStep"] = relationship(back_populates="translations")


class UnmappedRecipeIngredient(UUIDPKMixin, TimestampMixin, Base):
    """Ingredient d'une recette importee qui n'a pas pu etre rapproche
    avec confiance d'un Food existant (regle 4 : mieux vaut 'unmapped'
    qu'une mauvaise association). Ne bloque pas l'import de la recette.
    """

    __tablename__ = "unmapped_recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        index=True,
    )
    raw_text: Mapped[str] = mapped_column(String(300))
    raw_quantity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[IngredientMatchStatus] = mapped_column(
        Enum(IngredientMatchStatus, name="ingredient_match_status", values_callable=lambda e: [m.value for m in e]),
        default=IngredientMatchStatus.UNMAPPED,
        server_default=IngredientMatchStatus.UNMAPPED.value,
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="unmapped_ingredients")

    def __repr__(self) -> str:
        return f"<UnmappedRecipeIngredient raw_text={self.raw_text!r}>"


class RecipeVideo(UUIDPKMixin, Base):
    __tablename__ = "recipe_videos"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        index=True,
    )
    url: Mapped[str] = mapped_column(String(500))
    platform: Mapped[VideoPlatform] = mapped_column(
        Enum(VideoPlatform, name="video_platform")
    )
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    language_code: Mapped[str] = mapped_column(String(5))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="videos")
