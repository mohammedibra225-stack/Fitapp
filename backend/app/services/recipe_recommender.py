
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.profile import Profile
from app.models.recipe import Recipe
from app.services.recipe_availability import check_recipe_availability


# ============================================================
# CONTRAINTES OBLIGATOIRES (appliquees AVANT tout scoring)
# ============================================================

def _hard_filter_ok(recipe: Recipe, profile: Profile) -> bool:
    """Renvoie False si la recette viole une contrainte obligatoire."""

    # Halal obligatoire (regle 3/7) : seule la donnee reelle compte.
    if profile.halal_required and not recipe.is_halal:
        return False

    preferences = (profile.dietary_preferences or "").lower()
    if "vegan" in preferences and not recipe.is_vegan:
        return False
    if "vegetarian" in preferences and not (recipe.is_vegetarian or recipe.is_vegan):
        return False

    return True


# ============================================================
# COMPOSANTES DE SCORE (chacune entre 0 et 1)
# ============================================================

def _nutrition_match(recipe: Recipe, meal_calories_target: Optional[float],
                     protein_target: Optional[float]) -> float:
    """Proximite des calories/proteines de la recette (par portion)
    avec les cibles du profil. 1.0 = pile sur la cible."""
    score = 0.0
    parts = 0

    if meal_calories_target and recipe.calories_kcal:
        recipe_cal = float(recipe.calories_kcal)
        if recipe_cal > 0:
            ratio = recipe_cal / float(meal_calories_target)
            # 1.0 si ratio dans [0.8, 1.2], decroit au-dela.
            deviation = abs(ratio - 1.0)
            score += max(0.0, 1.0 - deviation)
            parts += 1

    if protein_target and recipe.protein_g:
        recipe_protein = float(recipe.protein_g)
        if recipe_protein > 0:
            ratio = recipe_protein / float(protein_target)
            deviation = abs(ratio - 1.0)
            score += max(0.0, 1.0 - deviation)
            parts += 1

    return score / parts if parts else 0.5  # neutre si donnees insuffisantes


def _goal_match(recipe: Recipe, profile: Profile) -> float:
    """Bonus selon la coherence avec l'objectif sportif (regle 7)."""
    goal = profile.primary_goal.value if profile.primary_goal else "general_health"
    protein = float(recipe.protein_g or 0)
    calories = float(recipe.calories_kcal or 0)

    if goal == "muscle_gain":
        # Proteines elevees privilégiees.
        return min(protein / 40.0, 1.0) if protein > 0 else 0.3
    if goal == "weight_loss":
        # Calories moderees + proteines suffisantes.
        if calories <= 0:
            return 0.3
        cal_score = 1.0 if calories <= 500 else max(0.0, 1.0 - (calories - 500) / 500)
        protein_score = min(protein / 25.0, 1.0) if protein > 0 else 0.2
        return (cal_score + protein_score) / 2
    if goal in ("performance", "endurance"):
        # Glucides pour l'energie + proteines.
        carbs = float(recipe.carbs_g or 0)
        return min((carbs / 60.0 + protein / 30.0) / 2, 1.0) if (carbs or protein) else 0.3

    # general_health / maintien : recette equilibree.
    return 0.7


def _budget_match(recipe: Recipe, profile: Profile) -> float:
    """Compare le niveau de cout estime au budget hebdo (regle 4/10).
    estimated_cost_level : 1 = economique, 2 = moyen, 3 = cher."""
    budget = float(profile.food_budget_per_week or 0)
    if budget <= 0:
        return 0.5
    # Repere de budget hebdo (7 jours x 3 repas principaux).
    per_meal = budget / 21.0
    # Priorite au cout reel par portion lorsqu'il est connu. Cela evite
    # qu'une recette chere soit selectionnee uniquement parce qu'elle porte
    # un niveau de cout approximatif.
    if recipe.cost_per_serving_da is not None:
        cost = float(recipe.cost_per_serving_da)
        if cost <= per_meal:
            return 1.0
        if cost <= per_meal * 1.25:
            return 0.6
        return 0.15
    level = recipe.estimated_cost_level
    if level is None:
        return 0.5  # inconnu : neutre, ni favorise ni penalise
    if per_meal < 200:       # budget faible -> favorise le niveau 1
        target_level = 1
    elif per_meal < 500:     # budget moyen -> niveau 1-2
        target_level = 2
    else:                    # budget eleve -> peu de contrainte
        return 1.0

    if level == target_level:
        return 1.0
    if abs(level - target_level) == 1:
        return 0.6
    return 0.2


def _meal_time_match(recipe: Recipe, meal_type: Optional[str],
                     recipe_meal_types: set[str]) -> float:
    """Compatibilite avec le moment de la journee (regle 7, point 5).
    recipe_meal_types est un ensemble de types calcule par l'appelant
    (ex: {'breakfast'} pour un porridge, {'lunch', 'dinner'} pour un plat)."""
    if not meal_type or not recipe_meal_types:
        return 0.5  # inconnu : neutre
    return 1.0 if meal_type in recipe_meal_types else 0.3


def _inventory_match(db: Session, recipe: Recipe, user_id: UUID) -> tuple[float, dict]:
    """Part d'ingredients deja en stock (regle 12). Retourne
    (score, detail_disponibilite) pour affichage dans l'app."""
    availability = check_recipe_availability(db, recipe, user_id)
    ingredients = availability.get("ingredients") or []
    if not ingredients:
        return 0.5, availability

    ok_count = sum(1 for item in ingredients if item["status"] == "ok")
    ratio = ok_count / len(ingredients)
    # Recompense forte : une recette 100% cuisinable remonte en tete.
    return (1.0 if ratio == 1.0 else ratio * 0.8), availability


# ============================================================
# CATEGORISATION PAR MOMENT DE LA JOURNEE
# ============================================================

# Mots-cles dans le slug : approche simple, extensible plus tard
# via un champ dedie si besoin (pas de nouvelle migration pour l'instant).
BREAKFAST_KEYWORDS = ("porridge", "oat", "pancake", "smoothie", "oeuf", "egg",
                      "crepe", "yaourt", "yogurt", "banane-bread", "avoine")
DESSERT_SNACK_KEYWORDS = ("bar", "ball", "smoothie", "salade-fruit", "cookie",
                          "shake", "collation")


def guess_meal_types(recipe: Recipe) -> set[str]:
    slug = (recipe.slug or "").lower()
    types: set[str] = {"lunch", "dinner"}
    if recipe.meal_type:
        types.add(recipe.meal_type.value)
    if any(keyword in slug for keyword in BREAKFAST_KEYWORDS):
        types.add("breakfast")
    if any(keyword in slug for keyword in DESSERT_SNACK_KEYWORDS):
        types.add("snack")
    return types


# ============================================================
# POINT D'ENTREE PRINCIPAL
# ============================================================

def recommend_recipes(
    db: Session,
    user_id: UUID,
    meal_type: Optional[str] = None,
    meal_calories_target: Optional[float] = None,
    protein_target: Optional[float] = None,
    limit: int = 20,
    include_inventory: bool = True,
) -> list[dict]:
    """Renvoie les recettes locales compatibles avec le profil, triees
    par score decroissant. Contraintes obligatoires appliquees d'abord
    (regle 9), puis scoring. Aucun appel externe (regle 5/16)."""

    profile = db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        return []

    recipes = db.execute(
        select(Recipe)
        .options(selectinload(Recipe.translations))
        .order_by(Recipe.slug)
    ).scalars().unique().all()

    scored: list[dict] = []
    for recipe in recipes:
        # --- Etape 1 : contraintes obligatoires (exclusions) ---
        if not _hard_filter_ok(recipe, profile):
            continue

        # --- Etape 2 : scoring ---
        if include_inventory:
            inventory_score, availability = _inventory_match(db, recipe, user_id)
        else:
            inventory_score, availability = 0.5, {"can_cook": None, "ingredients": []}
        components = {
            "nutrition": _nutrition_match(recipe, meal_calories_target, protein_target),
            "goal": _goal_match(recipe, profile),
            "budget": _budget_match(recipe, profile),
            "meal_time": _meal_time_match(recipe, meal_type, guess_meal_types(recipe)),
            "inventory": inventory_score,
        }
        total = sum(components.values())

        scored.append({
            "recipe": recipe,
            "score": round(total / len(components), 3),
            "score_components": {key: round(value, 3) for key, value in components.items()},
            "availability": availability,
        })

    scored.sort(key=lambda entry: entry["score"], reverse=True)
    return scored[:limit]
