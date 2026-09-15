"""
Vérifie si un utilisateur a, dans son inventaire, de quoi cuisiner
une recette donnée (compare RecipeIngredient <-> InventoryItem).

Limite assumée pour cette première version : la conversion d'unités
ne gère que g/kg (masse), ml/l (volume), et piece (via
food.unit_weight_g, comme dans meal_calculator.convert_to_grams).
Pour tbsp/tsp/cup/serving, il n'existe pas de table de conversion
dans le projet : la comparaison se fait uniquement si l'unité de
l'ingrédient et celle du stock sont strictement identiques. Sinon
le statut "unit_not_comparable" est renvoyé au lieu d'un faux
"missing".
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MeasurementUnit
from app.models.food import Food
from app.models.inventory import Inventory, InventoryItem
from app.models.recipe import Recipe, RecipeIngredient


def _normalize(quantity: Decimal, unit: MeasurementUnit, food: Food) -> tuple[str, Decimal]:
    """Ramene (quantite, unite) vers une unite de base comparable.

    Retourne (bucket, valeur) :
        bucket "mass_g"    -> valeur en grammes
        bucket "volume_ml" -> valeur en ml
        bucket "piece"     -> valeur en nombre de pieces
                               (utilise seulement si food.unit_weight_g est vide)
        bucket "unit:xxx"  -> pas de conversion possible, valeur brute
                               dans son unite d'origine (tbsp/tsp/cup/serving)
    """

    if unit == MeasurementUnit.G:
        return "mass_g", quantity
    if unit == MeasurementUnit.KG:
        return "mass_g", quantity * Decimal("1000")
    if unit == MeasurementUnit.ML:
        return "volume_ml", quantity
    if unit == MeasurementUnit.L:
        return "volume_ml", quantity * Decimal("1000")
    if unit == MeasurementUnit.PIECE:
        if food.unit_weight_g is not None:
            return "mass_g", quantity * Decimal(str(food.unit_weight_g))
        return "piece", quantity

    # tbsp / tsp / cup / serving : pas de table de conversion disponible
    return f"unit:{unit.value}", quantity


def check_recipe_availability(db: Session, recipe: Recipe, user_id: UUID) -> dict:
    """
    Compare les ingredients de `recipe` au stock (tous contenants
    confondus : frigo + congelateur + placard) de `user_id`.
    """

    # --------------------------------------------------------
    # Stock de l'utilisateur, regroupe par food_id + bucket
    # --------------------------------------------------------

    inventory_items = db.execute(
        select(InventoryItem)
        .join(Inventory, Inventory.id == InventoryItem.inventory_id)
        .where(Inventory.user_id == user_id)
    ).scalars().all()

    stock: dict[tuple, Decimal] = {}
    for item in inventory_items:
        bucket, value = _normalize(Decimal(str(item.quantity)), item.unit, item.food)
        key = (item.food_id, bucket)
        stock[key] = stock.get(key, Decimal("0")) + value

    # --------------------------------------------------------
    # Comparaison ingredient par ingredient
    # --------------------------------------------------------

    results = []
    can_cook = True

    for ingredient in recipe.ingredients:
        needed_bucket, needed_value = _normalize(
            Decimal(str(ingredient.quantity)), ingredient.unit, ingredient.food
        )
        key = (ingredient.food_id, needed_bucket)
        available_value = stock.get(key)

        has_any_stock_for_food = any(
            food_id == ingredient.food_id for (food_id, _bucket) in stock.keys()
        )

        if available_value is None:
            status = "unit_not_comparable" if has_any_stock_for_food else "missing"
            available_value = Decimal("0")
        elif available_value >= needed_value:
            status = "ok"
        else:
            status = "insufficient"

        if status != "ok":
            can_cook = False

        results.append(
            {
                "food_id": str(ingredient.food_id),
                "food_slug": ingredient.food.slug,
                "needed_quantity": float(ingredient.quantity),
                "needed_unit": ingredient.unit.value,
                "available_quantity": float(available_value),
                "status": status,
            }
        )

    return {
        "can_cook": can_cook,
        "ingredients": results,
    }
