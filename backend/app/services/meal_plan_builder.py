"""
Génération de la structure jours/repas d'un MealPlan.

Ce service ne choisit PAS encore d'aliments (ça viendra avec les
étapes Inventaire / Recettes). Il se contente de créer, pour chaque
jour du plan :

    MealPlanDay (jour 1, jour 2, ...)
        -> MealPlanMeal (breakfast, lunch, dinner, snack)
            -> target_calories_kcal / target_protein_g / ... (remplis)

en répartissant les cibles quotidiennes du MealPlan (déjà calculées
par app.services.nutrition.calculate_calories) selon un pourcentage
par type de repas.

Les MealPlanMealItem (aliments réels) restent vides pour l'instant :
ils seront remplis à l'étape "Recettes" / "Inventaire" plus tard.
"""

from app.models.enums import MealType
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanMeal


# ============================================================
# RÉPARTITION PAR DÉFAUT DES CALORIES ENTRE LES REPAS
# ============================================================
# Ces pourcentages sont volontairement simples pour l'instant.
# Ils pourront devenir personnalisables (ex: préférence utilisateur
# "pas de petit-déjeuner", "5 repas/jour"...) dans une étape future.

MEAL_DISTRIBUTION: dict[MealType, float] = {
    MealType.BREAKFAST: 0.25,
    MealType.LUNCH: 0.35,
    MealType.DINNER: 0.30,
    MealType.SNACK: 0.10,
}


def _split_target(daily_value: float, percentage: float) -> float:
    """Applique un pourcentage à une valeur quotidienne et arrondit à 2 décimales."""
    return round(float(daily_value) * percentage, 2)


def build_meal_plan_days(meal_plan: MealPlan, num_days: int = 7) -> list[MealPlanDay]:
    """
    Construit (sans les committer) les MealPlanDay + MealPlanMeal
    d'un MealPlan, à partir de ses cibles quotidiennes déjà définies
    (meal_plan.target_calories_kcal, target_protein_g, ...).

    Ne fait AUCUN db.add / db.commit : c'est à l'appelant (la route)
    de les ajouter à la session, pour rester cohérent avec le style
    déjà utilisé dans app/routes/nutrition.py.

    Retourne la liste des MealPlanDay créés (chacun a déjà sa liste
    `meals` remplie via la relation SQLAlchemy).
    """

    if meal_plan.target_calories_kcal is None:
        raise ValueError(
            "Le MealPlan n'a pas de cibles caloriques definies "
            "(target_calories_kcal est vide)."
        )

    daily_calories = float(meal_plan.target_calories_kcal)
    daily_protein = float(meal_plan.target_protein_g or 0)
    daily_carbs = float(meal_plan.target_carbs_g or 0)
    daily_fat = float(meal_plan.target_fat_g or 0)

    days: list[MealPlanDay] = []

    for day_number in range(1, num_days + 1):
        day = MealPlanDay(
            meal_plan_id=meal_plan.id,
            day_number=day_number,
        )

        for meal_type, percentage in MEAL_DISTRIBUTION.items():
            meal = MealPlanMeal(
                meal_type=meal_type,
                target_calories_kcal=_split_target(daily_calories, percentage),
                target_protein_g=_split_target(daily_protein, percentage),
                target_carbs_g=_split_target(daily_carbs, percentage),
                target_fat_g=_split_target(daily_fat, percentage),
            )
            day.meals.append(meal)

        days.append(day)

    return days
