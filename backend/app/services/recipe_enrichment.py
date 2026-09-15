"""
Calcule, pour une Recipe deja importee (ingredients mappes vers Food),
sa nutrition (etape 7), son cout (etape 8) et son statut halal (etape 9).

Reutilise integralement les moteurs existants :
    - app.services.meal_calculator.calculate_food_nutrition (nutrition)
    - app.services.food_price.calculate_food_cost (cout)

Ne recalcule rien depuis zero : ce module orchestre, il ne remplace pas
les calculateurs deja testes (regle 28).

Regle d'or reprise de tout le projet (regle 4/8/10) : mieux vaut un
resultat PARTIAL/UNKNOWN honnete qu'un total complet mais invente.
Comme app.services.recipe_availability, ce module ne devine JAMAIS de
conversion pour tbsp/tsp/cup/serving (aucune table de conversion fiable
dans le projet) : ces ingredients sont simplement exclus du calcul et
font basculer le statut en PARTIAL (ou UNKNOWN si rien n'a pu etre
calcule), jamais ignores silencieusement.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.enums import HalalStatus, MeasurementUnit, RecipeCostStatus, RecipeNutritionStatus
from app.models.food import Food, FoodPrice
from app.models.recipe import Recipe, RecipeIngredient
from app.services.food_price import calculate_food_cost
from app.services.meal_calculator import calculate_food_nutrition

# Unites pour lesquelles aucune conversion en grammes/ml n'existe dans
# le projet (voir recipe_availability.py) : on ne devine jamais une
# densite ("1 cup de farine" != "1 cup d'eau").
_UNCONVERTIBLE_UNITS = {MeasurementUnit.TBSP, MeasurementUnit.TSP, MeasurementUnit.CUP, MeasurementUnit.SERVING}


def _ingredient_is_convertible(ingredient: RecipeIngredient) -> bool:
    if ingredient.unit in _UNCONVERTIBLE_UNITS:
        return False
    if ingredient.unit == MeasurementUnit.PIECE and ingredient.food.unit_weight_g is None:
        return False
    return True


# ============================================================
# ETAPE 7 : NUTRITION
# ============================================================

NUTRITION_FIELDS = (
    "calories_kcal", "protein_g", "carbs_g", "fat_g",
    "fiber_g", "sugar_g", "sodium_mg",
)


def compute_recipe_nutrition(recipe: Recipe) -> dict:
    """Calcule les totaux nutritionnels PAR PORTION d'une recette a
    partir de ses RecipeIngredient (regle 6). Ne fait pas de requete DB
    (recipe.ingredients doit deja etre charge avec food)."""

    totals: dict[str, Decimal] = {field: Decimal("0") for field in NUTRITION_FIELDS}
    total_grams = Decimal("0")

    contributing = 0
    skipped: list[dict] = []

    for ingredient in recipe.ingredients:
        if not _ingredient_is_convertible(ingredient):
            skipped.append({
                "food_slug": ingredient.food.slug,
                "reason": f"unite non convertible ({ingredient.unit.value})",
            })
            continue

        result = calculate_food_nutrition(
            food=ingredient.food,
            quantity=ingredient.quantity,
            unit=ingredient.unit.value,
        )
        for field in NUTRITION_FIELDS:
            totals[field] += result[field]
        total_grams += result["grams"]
        contributing += 1

    has_unmapped = len(recipe.unmapped_ingredients) > 0
    has_skipped = len(skipped) > 0

    if contributing == 0:
        status = RecipeNutritionStatus.UNKNOWN
    elif has_unmapped or has_skipped:
        status = RecipeNutritionStatus.PARTIAL
    else:
        status = RecipeNutritionStatus.COMPLETE

    servings = recipe.servings or 1

    per_serving = {
        field: (totals[field] / servings) if contributing else None
        for field in NUTRITION_FIELDS
    }

    return {
        "status": status,
        "per_serving": per_serving,
        "total_grams": total_grams,
        "contributing_ingredients": contributing,
        "skipped_ingredients": skipped,
        "unmapped_ingredients_count": len(recipe.unmapped_ingredients),
    }


def apply_recipe_nutrition(recipe: Recipe, nutrition: dict) -> None:
    """Ecrit le resultat de compute_recipe_nutrition sur la Recipe.
    Ne commit pas (convention du projet : a l'appelant de commit)."""

    recipe.nutrition_status = nutrition["status"]
    for field in NUTRITION_FIELDS:
        value = nutrition["per_serving"][field]
        setattr(recipe, field, float(value) if value is not None else None)


# ============================================================
# ETAPE 8 : COUT (Open Prices / Food Price, en DZD uniquement)
# ============================================================

def _latest_dzd_price(food: Food) -> Optional[FoodPrice]:
    """Meme logique que open_prices.get_latest_known_price (le prix actif
    le plus recent), mais ne considere que les prix explicitement en DZD
    (regle 9/11) : un prix stocke dans une autre devise n'est PAS
    converti (aucun taux de change fiable dans le projet), on prefere le
    traiter comme inconnu plutot que de deviner une conversion."""

    dzd_prices = [fp for fp in food.prices if fp.is_active and fp.currency == "DZD"]
    if not dzd_prices:
        return None
    return max(dzd_prices, key=lambda fp: fp.valid_from or date.min)


def compute_recipe_cost(recipe: Recipe) -> dict:
    """Calcule le cout PAR PORTION d'une recette a partir des derniers
    prix DZD actifs connus pour chaque Food (regle 8). Ne fait pas de
    requete DB (recipe.ingredients doit deja etre charge avec food et
    food.prices)."""

    total_cost = Decimal("0")
    contributing = 0
    missing: list[dict] = []

    for ingredient in recipe.ingredients:
        food_price = _latest_dzd_price(ingredient.food)
        if food_price is None:
            missing.append({"food_slug": ingredient.food.slug, "reason": "price_unknown"})
            continue

        try:
            cost = calculate_food_cost(
                food=ingredient.food,
                food_price=food_price,
                quantity=ingredient.quantity,
                unit=ingredient.unit.value,
            )
        except ValueError as exc:
            # Unite non convertible pour le prix (tbsp/tsp/cup/serving,
            # ou piece sans unit_weight_g) : jamais invente (regle 8).
            missing.append({"food_slug": ingredient.food.slug, "reason": str(exc)})
            continue

        total_cost += cost
        contributing += 1

    has_unmapped = len(recipe.unmapped_ingredients) > 0
    has_missing = len(missing) > 0

    if contributing == 0:
        status = RecipeCostStatus.UNKNOWN
    elif has_unmapped or has_missing:
        status = RecipeCostStatus.PARTIAL
    else:
        status = RecipeCostStatus.KNOWN

    servings = recipe.servings or 1
    cost_per_serving = (total_cost / servings) if contributing else None

    return {
        "status": status,
        "cost_per_serving_da": cost_per_serving,
        "contributing_ingredients": contributing,
        "missing_ingredients": missing,
        "unmapped_ingredients_count": len(recipe.unmapped_ingredients),
    }


def apply_recipe_cost(recipe: Recipe, cost: dict) -> None:
    recipe.cost_status = cost["status"]
    value = cost["cost_per_serving_da"]
    recipe.cost_per_serving_da = float(value) if value is not None else None


# ============================================================
# ETAPE 9 : HALAL
# ============================================================

def compute_recipe_halal_status(recipe: Recipe) -> HalalStatus:
    """Determine le statut halal d'une recette a partir du halal_status
    de chacun de ses Food (regle 10). Un seul ingredient explicitement
    NOT_HALAL exclut definitivement la recette, meme si d'autres
    ingredients sont unmapped. Sinon, tout ingredient unmapped ou de
    statut UNKNOWN fait retomber le resultat a UNKNOWN : on ne
    pretend jamais qu'une recette est halal par defaut."""

    statuses = {ingredient.food.halal_status for ingredient in recipe.ingredients}

    if HalalStatus.NOT_HALAL in statuses:
        return HalalStatus.NOT_HALAL

    if recipe.unmapped_ingredients or HalalStatus.UNKNOWN in statuses or not statuses:
        return HalalStatus.UNKNOWN

    return HalalStatus.HALAL


def apply_recipe_halal_status(recipe: Recipe, halal_status: HalalStatus) -> None:
    recipe.halal_status = halal_status
    # is_halal (bool historique, deja utilise par recipe_recommender et
    # seed_recipes) reste en synchro avec le nouveau champ a 3 valeurs.
    recipe.is_halal = halal_status == HalalStatus.HALAL


# ============================================================
# POINT D'ENTREE : les 3 a la fois
# ============================================================

def enrich_recipe(recipe: Recipe) -> dict:
    """Calcule et applique nutrition + cout + halal sur `recipe`. Ne
    commit pas (a l'appelant, comme le reste du projet). recipe doit
    deja avoir ingredients/unmapped_ingredients/food/food.prices charges
    (voir scripts/enrich_recipes.py pour le chargement optimise)."""

    nutrition = compute_recipe_nutrition(recipe)
    apply_recipe_nutrition(recipe, nutrition)

    cost = compute_recipe_cost(recipe)
    apply_recipe_cost(recipe, cost)

    halal_status = compute_recipe_halal_status(recipe)
    apply_recipe_halal_status(recipe, halal_status)

    return {
        "nutrition": nutrition,
        "cost": cost,
        "halal_status": halal_status,
    }
