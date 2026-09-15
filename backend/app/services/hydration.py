"""
Calcul de l'objectif d'hydratation quotidien.

Formule volontairement simple (comme pour les calories/macros) :

    objectif = poids_kg * 33 ml  +  bonus selon le niveau d'activité

33 ml/kg est la valeur médiane généralement citée (30-35 ml/kg).
Le bonus compense la transpiration liée à l'activité physique.
"""

from app.models.enums import ActivityLevel


ML_PER_KG = 33

ACTIVITY_WATER_BONUS_ML: dict[ActivityLevel, int] = {
    ActivityLevel.SEDENTARY: 0,
    ActivityLevel.LIGHT: 250,
    ActivityLevel.MODERATE: 500,
    ActivityLevel.ACTIVE: 750,
    ActivityLevel.VERY_ACTIVE: 1000,
}


def calculate_water_goal_ml(
    weight_kg: float,
    activity_level: ActivityLevel,
) -> int:
    """Retourne l'objectif d'hydratation quotidien en ml, arrondi à l'entier."""

    bonus = ACTIVITY_WATER_BONUS_ML.get(activity_level)

    if bonus is None:
        raise ValueError(f"Unsupported activity level: {activity_level}")

    goal_ml = weight_kg * ML_PER_KG + bonus

    return round(goal_ml)
