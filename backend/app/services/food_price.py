from decimal import Decimal, ROUND_HALF_UP

from app.models.food import Food, FoodPrice


# ============================================================
# CONVERSIONS D'UNITES
# ============================================================

WEIGHT_TO_GRAMS = {
    "g": Decimal("1"),
    "kg": Decimal("1000"),
}

LIQUID_TO_ML = {
    "ml": Decimal("1"),
    "l": Decimal("1000"),
}


# ============================================================
# NORMALISATION
# ============================================================

def normalize_unit(unit: str) -> str:
    if not unit:
        raise ValueError("L'unité est obligatoire.")

    unit = unit.strip().lower()

    aliases = {
        "gramme": "g",
        "grammes": "g",
        "gram": "g",
        "grams": "g",

        "kilogramme": "kg",
        "kilogrammes": "kg",
        "kilo": "kg",
        "kilos": "kg",

        "millilitre": "ml",
        "millilitres": "ml",
        "milliliter": "ml",
        "milliliters": "ml",

        "litre": "l",
        "litres": "l",
        "liter": "l",
        "liters": "l",

        "pièce": "piece",
        "pièces": "piece",
        "piece": "piece",
        "pieces": "piece",
        "unite": "piece",
        "unité": "piece",
        "unit": "piece",
        "units": "piece",
        "pcs": "piece",
    }

    return aliases.get(unit, unit)


# ============================================================
# CONVERSION VERS UNITE DE BASE
# ============================================================

def convert_to_base_quantity(
    quantity: Decimal,
    unit: str,
) -> tuple[Decimal, str]:

    unit = normalize_unit(unit)

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à 0."
        )

    if unit in WEIGHT_TO_GRAMS:
        return (
            quantity * WEIGHT_TO_GRAMS[unit],
            "g",
        )

    if unit in LIQUID_TO_ML:
        return (
            quantity * LIQUID_TO_ML[unit],
            "ml",
        )

    if unit == "piece":
        return quantity, "piece"

    raise ValueError(
        f"Unité non supportée pour le calcul de prix : {unit}"
    )


# ============================================================
# PRIX UNITAIRE
# ============================================================

def calculate_unit_price(
    food_price: FoodPrice,
) -> Decimal:

    price = Decimal(
        str(food_price.price_da)
    )

    quantity = Decimal(
        str(food_price.quantity)
    )

    unit = normalize_unit(
        food_price.unit
    )

    if quantity <= 0:
        raise ValueError(
            "La quantité du prix doit être supérieure à 0."
        )

    if price < 0:
        raise ValueError(
            "Le prix ne peut pas être négatif."
        )

    if unit in WEIGHT_TO_GRAMS:

        base_quantity = (
            quantity * WEIGHT_TO_GRAMS[unit]
        )

    elif unit in LIQUID_TO_ML:

        base_quantity = (
            quantity * LIQUID_TO_ML[unit]
        )

    elif unit == "piece":

        base_quantity = quantity

    else:

        raise ValueError(
            f"Unité de prix non supportée : {unit}"
        )

    return price / base_quantity


# ============================================================
# CALCUL DU COUT
# ============================================================

def calculate_food_cost(
    food: Food,
    food_price: FoodPrice,
    quantity: float | Decimal,
    unit: str,
) -> Decimal:

    quantity = Decimal(
        str(quantity)
    )

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à 0."
        )

    requested_unit = normalize_unit(unit)

    price_unit = normalize_unit(
        food_price.unit
    )

    requested_quantity, requested_base_unit = (
        convert_to_base_quantity(
            quantity,
            requested_unit,
        )
    )

    # --------------------------------------------------------
    # Déterminer l'unité de base du prix
    # --------------------------------------------------------

    if price_unit in WEIGHT_TO_GRAMS:

        price_base_unit = "g"

    elif price_unit in LIQUID_TO_ML:

        price_base_unit = "ml"

    elif price_unit == "piece":

        price_base_unit = "piece"

    else:

        raise ValueError(
            f"Unité de prix non supportée : {price_unit}"
        )

    # --------------------------------------------------------
    # PIECE -> POIDS
    # --------------------------------------------------------

    if (
        requested_base_unit == "piece"
        and price_base_unit == "g"
    ):

        if food is None:
            raise ValueError(
                "L'aliment est obligatoire pour convertir "
                "une pièce en poids."
            )

        if food.unit_weight_g is None:
            raise ValueError(
                f"L'aliment '{food.slug}' ne possède pas "
                "de poids par pièce."
            )

        unit_weight = Decimal(
            str(food.unit_weight_g)
        )

        if unit_weight <= 0:
            raise ValueError(
                f"Le poids par pièce de '{food.slug}' "
                "doit être supérieur à 0."
            )

        requested_quantity = (
            quantity * unit_weight
        )

        requested_base_unit = "g"

    # --------------------------------------------------------
    # PIECE -> PIECE
    # --------------------------------------------------------

    elif (
        requested_base_unit == "piece"
        and price_base_unit == "piece"
    ):

        requested_quantity = quantity

    # --------------------------------------------------------
    # UNITES INCOMPATIBLES
    # --------------------------------------------------------

    elif requested_base_unit != price_base_unit:

        raise ValueError(
            f"Unités incompatibles : "
            f"{unit} ne peut pas être comparé avec "
            f"{food_price.unit}."
        )

    # --------------------------------------------------------
    # PRIX UNITAIRE
    # --------------------------------------------------------

    unit_price = calculate_unit_price(
        food_price
    )

    # --------------------------------------------------------
    # COUT FINAL
    # --------------------------------------------------------

    cost = (
        requested_quantity * unit_price
    )

    return cost.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# FONCTION UTILITAIRE
# ============================================================

def calculate_food_cost_from_values(
    price_da: float,
    price_quantity: float,
    price_unit: str,
    quantity: float,
    quantity_unit: str,
) -> Decimal:

    class TemporaryFoodPrice:
        pass

    food_price = TemporaryFoodPrice()

    food_price.price_da = Decimal(
        str(price_da)
    )

    food_price.quantity = Decimal(
        str(price_quantity)
    )

    food_price.unit = price_unit

    return calculate_food_cost(
        food=None,
        food_price=food_price,
        quantity=quantity,
        unit=quantity_unit,
    )