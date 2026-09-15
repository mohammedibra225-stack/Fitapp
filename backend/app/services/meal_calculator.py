
from decimal import Decimal, ROUND_HALF_UP

from app.models.food import Food, FoodPrice
from app.services.food_price import calculate_food_cost


# ============================================================
# UTILITAIRES
# ============================================================

def decimal(value) -> Decimal:
    """Convertit une valeur en Decimal."""
    return Decimal(str(value))


def round_decimal(value: Decimal) -> Decimal:
    """Arrondit à 2 décimales."""
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# CONVERSION DES UNITÉS EN GRAMMES
# ============================================================

def convert_to_grams(
    food: Food,
    quantity: float | Decimal,
    unit: str,
) -> Decimal:
    """
    Convertit une quantité en grammes.

    Unités supportées :

        g
        kg
        ml
        l
        piece
        unit
        pcs

    Pour une pièce, le poids est récupéré depuis :

        food.unit_weight_g

    Exemple :

        3 œufs
        unit_weight_g = 50

        => 150 g
    """

    quantity = decimal(quantity)

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à 0."
        )

    unit = unit.strip().lower()

    # --------------------------------------------------------
    # Grammes
    # --------------------------------------------------------

    if unit == "g":
        return quantity

    # --------------------------------------------------------
    # Kilogrammes
    # --------------------------------------------------------

    if unit == "kg":
        return quantity * Decimal("1000")

    # --------------------------------------------------------
    # Millilitres
    #
    # Pour les liquides, les données nutritionnelles sont
    # considérées comme exprimées pour 100 ml.
    # --------------------------------------------------------

    if unit == "ml":
        return quantity

    # --------------------------------------------------------
    # Litres
    # --------------------------------------------------------

    if unit == "l":
        return quantity * Decimal("1000")

    # --------------------------------------------------------
    # Pièces
    # --------------------------------------------------------

    if unit in ("piece", "unit", "pcs"):

        if food.unit_weight_g is None:
            raise ValueError(
                f"L'aliment '{food.slug}' ne possède pas "
                "de poids unitaire (unit_weight_g). "
                "Impossible de calculer par pièce."
            )

        unit_weight = decimal(food.unit_weight_g)

        if unit_weight <= 0:
            raise ValueError(
                f"Le poids unitaire de '{food.slug}' "
                "doit être supérieur à 0."
            )

        return quantity * unit_weight

    raise ValueError(
        f"Unité nutritionnelle non supportée : {unit}"
    )


# ============================================================
# CALCUL NUTRITIONNEL D'UN ALIMENT
# ============================================================

def calculate_food_nutrition(
    food: Food,
    quantity: float | Decimal,
    unit: str,
) -> dict:
    """
    Calcule les valeurs nutritionnelles d'une quantité donnée.

    Les valeurs nutritionnelles sont exprimées pour 100 g
    (ou 100 ml pour les liquides).

    Exemples :

        Riz :
            360 kcal / 100 g

        150 g :
            540 kcal

    Exemple avec une pièce :

        Œuf :
            unit_weight_g = 50 g

        3 œufs :
            150 g
    """

    quantity = decimal(quantity)

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à 0."
        )

    unit = unit.strip().lower()

    grams = convert_to_grams(
        food=food,
        quantity=quantity,
        unit=unit,
    )

    # --------------------------------------------------------
    # Facteur par rapport aux valeurs pour 100 g / 100 ml
    # --------------------------------------------------------

    factor = grams / Decimal("100")

    return {
        "quantity": quantity,
        "unit": unit,
        "grams": round_decimal(grams),

        "calories_kcal": round_decimal(
            decimal(food.calories_kcal) * factor
        ),

        "protein_g": round_decimal(
            decimal(food.protein_g) * factor
        ),

        "carbs_g": round_decimal(
            decimal(food.carbs_g) * factor
        ),

        "fat_g": round_decimal(
            decimal(food.fat_g) * factor
        ),

        "fiber_g": (
            round_decimal(
                decimal(food.fiber_g) * factor
            )
            if food.fiber_g is not None
            else Decimal("0.00")
        ),

        "sugar_g": (
            round_decimal(
                decimal(food.sugar_g) * factor
            )
            if food.sugar_g is not None
            else Decimal("0.00")
        ),

        "sodium_mg": (
            round_decimal(
                decimal(food.sodium_mg) * factor
            )
            if food.sodium_mg is not None
            else Decimal("0.00")
        ),

        "saturated_fat_g": (
            round_decimal(
                decimal(food.saturated_fat_g) * factor
            )
            if food.saturated_fat_g is not None
            else Decimal("0.00")
        ),
    }


# ============================================================
# CALCUL NUTRITION + PRIX D'UN ALIMENT
# ============================================================

def calculate_food_item(
    food: Food,
    food_price: FoodPrice,
    quantity: float | Decimal,
    unit: str,
) -> dict:

    nutrition = calculate_food_nutrition(
        food=food,
        quantity=quantity,
        unit=unit,
    )

    cost = calculate_food_cost(
        food=food,
        food_price=food_price,
        quantity=quantity,
        unit=unit,
    )

    return {
        "food_id": str(food.id),
        "slug": food.slug,

        "quantity": float(quantity),
        "unit": unit.strip().lower(),

        "grams": nutrition["grams"],

        "calories_kcal": nutrition["calories_kcal"],
        "protein_g": nutrition["protein_g"],
        "carbs_g": nutrition["carbs_g"],
        "fat_g": nutrition["fat_g"],
        "fiber_g": nutrition["fiber_g"],
        "sugar_g": nutrition["sugar_g"],
        "sodium_mg": nutrition["sodium_mg"],
        "saturated_fat_g": nutrition["saturated_fat_g"],

        "cost_da": cost,
    }


# ============================================================
# CALCUL D'UN REPAS
# ============================================================

def calculate_meal(items: list[dict]) -> dict:
    """
    Calcule le total nutritionnel et financier d'un repas.

    Chaque élément de `items` doit contenir :

        {
            "food": Food,
            "food_price": FoodPrice,
            "quantity": 150,
            "unit": "g"
        }

    Exemple :

        calculate_meal([
            {
                "food": riz,
                "food_price": prix_riz,
                "quantity": 150,
                "unit": "g"
            },
            {
                "food": oeuf,
                "food_price": prix_oeuf,
                "quantity": 3,
                "unit": "piece"
            }
        ])
    """

    if not items:
        raise ValueError(
            "Le repas doit contenir au moins un aliment."
        )

    total_calories = Decimal("0")
    total_protein = Decimal("0")
    total_carbs = Decimal("0")
    total_fat = Decimal("0")
    total_fiber = Decimal("0")
    total_sugar = Decimal("0")
    total_sodium = Decimal("0")
    total_saturated_fat = Decimal("0")
    total_cost = Decimal("0")
    total_grams = Decimal("0")

    calculated_items = []

    for item in items:

        food = item["food"]
        food_price = item["food_price"]
        quantity = item["quantity"]
        unit = item["unit"]

        result = calculate_food_item(
            food=food,
            food_price=food_price,
            quantity=quantity,
            unit=unit,
        )

        calculated_items.append(result)

        total_grams += result["grams"]

        total_calories += result["calories_kcal"]
        total_protein += result["protein_g"]
        total_carbs += result["carbs_g"]
        total_fat += result["fat_g"]
        total_fiber += result["fiber_g"]
        total_sugar += result["sugar_g"]
        total_sodium += result["sodium_mg"]
        total_saturated_fat += result["saturated_fat_g"]
        total_cost += result["cost_da"]

    return {
        "items": calculated_items,

        "totals": {
            "total_grams": round_decimal(total_grams),

            "calories_kcal": round_decimal(
                total_calories
            ),

            "protein_g": round_decimal(
                total_protein
            ),

            "carbs_g": round_decimal(
                total_carbs
            ),

            "fat_g": round_decimal(
                total_fat
            ),

            "fiber_g": round_decimal(
                total_fiber
            ),

            "sugar_g": round_decimal(
                total_sugar
            ),

            "sodium_mg": round_decimal(
                total_sodium
            ),

            "saturated_fat_g": round_decimal(
                total_saturated_fat
            ),

            "cost_da": round_decimal(
                total_cost
            ),
        },
    }


# ============================================================
# VERIFICATION DU BUDGET
# ============================================================

def check_weekly_budget(
    meal_costs: list[float | Decimal],
    weekly_budget_da: float | Decimal,
) -> dict:
    """
    Vérifie si une liste de coûts de repas respecte
    le budget hebdomadaire.

    Exemple :

        7 jours de repas
        budget = 5000 DA

    retourne :

        {
            "total_cost_da": ...,
            "budget_da": 5000,
            "remaining_da": ...,
            "within_budget": True/False
        }
    """

    budget = decimal(weekly_budget_da)

    if budget < 0:
        raise ValueError(
            "Le budget ne peut pas être négatif."
        )

    total = sum(
        (decimal(cost) for cost in meal_costs),
        Decimal("0"),
    )

    remaining = budget - total

    return {
        "total_cost_da": round_decimal(total),

        "budget_da": round_decimal(
            budget
        ),

        "remaining_da": round_decimal(
            remaining
        ),

        "within_budget": total <= budget,

        "over_budget_da": (
            round_decimal(abs(remaining))
            if remaining < 0
            else Decimal("0.00")
        ),
    }

