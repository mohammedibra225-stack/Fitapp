import random
from datetime import date, timedelta
from typing import Optional
from urllib.parse import quote_plus
from app.models.enums import ActivityLevel, GoalType, MeasurementUnit, MealType, Sex
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.models.food import Food, FoodPrice
from app.models.profile import Profile
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanMeal, MealPlanMealItem
from app.models.recipe import Recipe
from app.services.meal_calculator import calculate_meal
from app.services.meal_plan_builder import build_meal_plan_days
from app.services.nutrition import calculate_calories

from app.services.recipe_recommender import recommend_recipes


router = APIRouter(
    prefix="/nutrition",
    tags=["nutrition"],
)


class MealItemRequest(BaseModel):
    food_slug: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)


class MealCalculateRequest(BaseModel):
    items: list[MealItemRequest] = Field(..., min_length=1)


class MealPlanMealUpdate(BaseModel):
    recipe_id: UUID | None = None
    target_calories_kcal: float | None = Field(default=None, gt=0)
    target_protein_g: float | None = Field(default=None, gt=0)
    target_carbs_g: float | None = Field(default=None, gt=0)
    target_fat_g: float | None = Field(default=None, gt=0)
    # [SPOONACULAR REMOVAL - STEP 1] champ remplacé par recipe_id (recette PostgreSQL).
    spoonacular_recipe_id: int | None = Field(default=None, gt=0)
    recipe_id: UUID | None = Field(default=None)


@router.post("/meal/calculate")
def calculate_meal_endpoint(
    request: MealCalculateRequest,
    db: Session = Depends(get_db),
):
    """
    Calcule les valeurs nutritionnelles et le coût
    d'un repas à partir des aliments présents en DB.
    """

    calculated_items = []

    for item in request.items:

        # ----------------------------------------------------
        # Recherche de l'aliment
        # ----------------------------------------------------

        food = (
            db.query(Food)
            .filter(Food.slug == item.food_slug)
            .first()
        )

        if food is None:
            raise HTTPException(
                status_code=404,
                detail=f"Aliment introuvable : {item.food_slug}",
            )

        # ----------------------------------------------------
        # Recherche du prix actif
        # ----------------------------------------------------

        food_price = (
            db.query(FoodPrice)
            .filter(
                FoodPrice.food_id == food.id,
                FoodPrice.is_active.is_(True),
            )
            .order_by(
                FoodPrice.valid_from.desc().nullslast(),
                FoodPrice.created_at.desc(),
            )
            .first()
        )

        if food_price is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Aucun prix actif trouvé pour "
                    f"{item.food_slug}"
                ),
            )

        calculated_items.append(
            {
                "food": food,
                "food_price": food_price,
                "quantity": item.quantity,
                "unit": item.unit,
            }
        )

    # --------------------------------------------------------
    # Calcul du repas
    # --------------------------------------------------------

    try:
        result = calculate_meal(calculated_items)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # Conversion Decimal -> float
    # Pour que FastAPI retourne du JSON propre.
    # --------------------------------------------------------

    for item in result["items"]:
        for key, value in item.items():
            if hasattr(value, "as_tuple"):
                item[key] = float(value)

    for key, value in result["totals"].items():
        if hasattr(value, "as_tuple"):
            result["totals"][key] = float(value)

    return result


# ============================================================
# CALCUL NUTRITIONNEL
# ============================================================

class NutritionCalculateRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    sex: Sex
    activity_level: ActivityLevel
    goal: GoalType


@router.post("/calculate")
def calculate_nutrition(data: NutritionCalculateRequest):

    try:
        result = calculate_calories(
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            age=data.age,
            sex=data.sex,
            activity_level=data.activity_level,
            goal=data.goal,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# ============================================================
# CALCUL AUTOMATIQUE DEPUIS LE PROFIL
# ============================================================

@router.get("/calculate/{user_id}")
def calculate_user_nutrition(
    user_id: UUID,
    db: Session = Depends(get_db),
):

    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    required_fields = {
        "age": profile.age,
        "sex": profile.sex,
        "height_cm": profile.height_cm,
        "current_weight_kg": profile.current_weight_kg,
        "activity_level": profile.activity_level,
        "primary_goal": profile.primary_goal,
    }

    missing_fields = [
        field
        for field, value in required_fields.items()
        if value is None
    ]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Incomplete profile",
                "missing_fields": missing_fields,
            },
        )

    try:

        result = calculate_calories(
            weight_kg=float(profile.current_weight_kg),
            height_cm=float(profile.height_cm),
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.primary_goal,
        )

        return {
            "user_id": str(user_id),
            **result,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/meal-plan/{user_id}")
def get_current_meal_plan(
    user_id: UUID,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    meal_plan = db.execute(
        select(MealPlan)
        .options(
            selectinload(MealPlan.days)
            .selectinload(MealPlanDay.meals)
            .selectinload(MealPlanMeal.items)
            .selectinload(MealPlanMealItem.recipe)
            .selectinload(Recipe.translations)
        )
        .where(MealPlan.user_id == user_id)
        .order_by(MealPlan.created_at.desc())
    ).scalars().first()
    if meal_plan is None:
        # Le frontend charge d'abord le plan en GET. Pour éviter un 404
        # transitoire au premier affichage, on crée automatiquement le plan
        # à partir du profil complet ; le POST reste disponible pour une
        # création explicite/régénération.
        return create_meal_plan(user_id, db, language=language)
    has_recipe = any(meal.items for day in meal_plan.days for meal in day.meals)
    if attach_local_recipes(db, meal_plan, replace_legacy=not has_recipe):
        db.commit()
        db.refresh(meal_plan)
    return meal_plan_to_response(meal_plan, _get_weekly_budget(db, meal_plan), language)


@router.patch("/meal-plan/{user_id}/meal/{meal_id}")
def update_meal_plan_meal(
    user_id: UUID,
    meal_id: UUID,
    payload: MealPlanMealUpdate,
    db: Session = Depends(get_db),
):
    meal = db.execute(
        select(MealPlanMeal)
        .join(MealPlanDay, MealPlanMeal.meal_plan_day_id == MealPlanDay.id)
        .join(MealPlan, MealPlanDay.meal_plan_id == MealPlan.id)
        .where(MealPlanMeal.id == meal_id, MealPlan.user_id == user_id)
    ).scalar_one_or_none()
    if meal is None:
        raise HTTPException(status_code=404, detail="Repas du plan introuvable.")
    values = payload.model_dump(exclude_unset=True)
    # [SPOONACULAR REMOVAL - STEP 1] On accepte encore spoonacular_recipe_id (legacy)
    # mais il est ignoré : seule recipe_id (PostgreSQL) est honorée.
    values.pop("spoonacular_recipe_id", None)
    recipe_id = values.pop("recipe_id", None)
    if recipe_id is not None:
        recipe = db.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recette introuvable.")
        for item in list(meal.items):
            db.delete(item)
        meal.items.append(
            MealPlanMealItem(
                recipe_id=recipe.id,
                quantity=1,
                unit=MeasurementUnit.SERVING,
            )
        )
    # [SPOONACULAR REMOVAL - STEP 1] Bloc spoonacular désactivé.
    # if spoonacular_recipe_id is not None:
    #     recipe_data = get_spoonacular_recipe(spoonacular_recipe_id)
    #     for item in list(meal.items):
    #         db.delete(item)
    #     meal.spoonacular_recipe_id = spoonacular_recipe_id
    #     meal.spoonacular_recipe_data = recipe_data
    for field, value in values.items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return {
        "id": str(meal.id),
        "meal_type": meal.meal_type.value,
        "target_calories_kcal": float(meal.target_calories_kcal),
        "target_protein_g": float(meal.target_protein_g),
        "target_carbs_g": float(meal.target_carbs_g),
        "target_fat_g": float(meal.target_fat_g),
    }


@router.delete("/meal-plan/{user_id}/meal/{meal_id}/recipe", status_code=204)
def remove_meal_plan_recipe(
    user_id: UUID,
    meal_id: UUID,
    db: Session = Depends(get_db),
):
    meal = db.execute(
        select(MealPlanMeal)
        .join(MealPlanDay, MealPlanMeal.meal_plan_day_id == MealPlanDay.id)
        .join(MealPlan, MealPlanDay.meal_plan_id == MealPlan.id)
        .options(selectinload(MealPlanMeal.items))
        .where(MealPlanMeal.id == meal_id, MealPlan.user_id == user_id)
    ).scalar_one_or_none()
    if meal is None:
        raise HTTPException(status_code=404, detail="Repas du plan introuvable.")
    # [SPOONACULAR REMOVAL - STEP 1] Reset spoonacular legacy (sans effet si null).
    meal.spoonacular_recipe_id = None
    meal.spoonacular_recipe_data = None
    if meal.items:
        db.delete(meal.items[0])
    else:
        raise HTTPException(status_code=404, detail="Aucune recette dans ce repas.")
    db.commit()


# ============================================================
# CREATION AUTOMATIQUE DU PLAN NUTRITIONNEL
# ============================================================

@router.delete("/meal-plan/{user_id}", status_code=204)
def delete_current_meal_plan(user_id: UUID, db: Session = Depends(get_db)):
    meal_plan = db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user_id)
        .order_by(MealPlan.created_at.desc())
    ).scalars().first()
    if meal_plan is None:
        raise HTTPException(status_code=404, detail="Aucun plan alimentaire trouvé.")
    db.delete(meal_plan)
    db.commit()


@router.post("/meal-plan/{user_id}")
def create_meal_plan(
    user_id: UUID,
    db: Session = Depends(get_db),
    language: str = "fr",
):

    # --------------------------------------------------------
    # 1. Récupérer le profil
    # --------------------------------------------------------

    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    # --------------------------------------------------------
    # 2. Vérifier que le profil est complet
    # --------------------------------------------------------

    required_fields = {
        "age": profile.age,
        "sex": profile.sex,
        "height_cm": profile.height_cm,
        "current_weight_kg": profile.current_weight_kg,
        "activity_level": profile.activity_level,
        "primary_goal": profile.primary_goal,
    }

    missing_fields = [
        field
        for field, value in required_fields.items()
        if value is None
    ]

    if missing_fields:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Incomplete profile",
                "missing_fields": missing_fields,
            },
        )

    # --------------------------------------------------------
    # 3. Calculer calories et macros
    # --------------------------------------------------------

    try:

        nutrition = calculate_calories(
            weight_kg=float(profile.current_weight_kg),
            height_cm=float(profile.height_cm),
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.primary_goal,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    # --------------------------------------------------------
    # 4. Dates du plan
    # --------------------------------------------------------

    start_date = date.today()
    end_date = start_date + timedelta(days=6)

    # --------------------------------------------------------
    # 5. Créer le MealPlan
    # --------------------------------------------------------

    meal_plan = MealPlan(

        user_id=user_id,

        name="Plan nutritionnel personnalisé",

        goal=profile.primary_goal,

        target_calories_kcal=nutrition["daily_calories"],

        target_protein_g=nutrition["protein_g"],

        target_carbs_g=nutrition["carbs_g"],

        target_fat_g=nutrition["fat_g"],

        start_date=start_date,

        end_date=end_date,
    )

    db.add(meal_plan)
    db.flush()  # attribue meal_plan.id avant de creer les jours/repas

    # --------------------------------------------------------
    # 5bis. Répartir les cibles quotidiennes sur les jours/repas
    # --------------------------------------------------------

    days = build_meal_plan_days(meal_plan)
    db.add_all(days)
    db.flush()
    attach_local_recipes(db, meal_plan)

    db.commit()

    db.refresh(meal_plan)

    # --------------------------------------------------------
    # 6. Retourner le plan créé
    # --------------------------------------------------------

    return meal_plan_to_response(meal_plan, float(profile.food_budget_per_week or 0), language)


def meal_plan_to_response(
    meal_plan: MealPlan,
    weekly_budget_da: float = 0.0,
    language: str = "fr",
) -> dict:
    return {
        "meal_plan": {
            "id": str(meal_plan.id),
            "user_id": str(meal_plan.user_id),
            "name": meal_plan.name,
            "goal": meal_plan.goal.value if meal_plan.goal else None,
            "target_calories_kcal": float(meal_plan.target_calories_kcal),
            "target_protein_g": float(meal_plan.target_protein_g),
            "target_carbs_g": float(meal_plan.target_carbs_g),
            "target_fat_g": float(meal_plan.target_fat_g),
            "start_date": meal_plan.start_date.isoformat() if meal_plan.start_date else None,
            "end_date": meal_plan.end_date.isoformat() if meal_plan.end_date else None,
        },
        "budget": compute_meal_plan_budget_summary(meal_plan, weekly_budget_da),
        "days": [
            {
                "id": str(day.id),
                "day_number": day.day_number,
                "label": day.label,
                "meals": [
                    {
                        "id": str(meal.id),
                        "meal_type": meal.meal_type.value,
                        "target_calories_kcal": float(meal.target_calories_kcal),
                        "target_protein_g": float(meal.target_protein_g),
                        "target_carbs_g": float(meal.target_carbs_g),
                        "target_fat_g": float(meal.target_fat_g),
                        "recipe": meal.spoonacular_recipe_data
                        or (recipe_to_response(meal.items[0].recipe, language)
                            if meal.items and meal.items[0].recipe else None),
                    }
                    for meal in day.meals
                ],
            }
            for day in meal_plan.days
        ],
    }


def recipe_to_response(recipe: Recipe, language: str = "fr") -> dict:
    # Fallback : langue demandee -> anglais -> francais -> premiere disponible.
    by_language = {item.language_code: item for item in recipe.translations}
    translation = (
        by_language.get(language)
        or by_language.get("en")
        or by_language.get("fr")
        or (recipe.translations[0] if recipe.translations else None)
    )
    return {
        "id": str(recipe.id),
        "slug": recipe.slug,
        "name": translation.name if translation else recipe.slug,
        "description": translation.description if translation else None,
        "youtube_search_url": f"https://www.youtube.com/results?search_query={quote_plus((translation.name if translation else recipe.slug).strip())}",
        "calories_kcal": float(recipe.calories_kcal or 0),
        "protein_g": float(recipe.protein_g or 0),
        "carbs_g": float(recipe.carbs_g or 0),
        "fat_g": float(recipe.fat_g or 0),
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "image_url": recipe.image_url,
    }


# [SPOONACULAR REMOVAL - STEP 1] Moteur local PostgreSQL remplace Spoonacular.
def attach_local_recipes(
    db: Session,
    meal_plan: MealPlan,
    replace_legacy: bool = False,
) -> bool:
    """Attache des recettes locales provenant de la base PostgreSQL."""
    return attach_default_recipes(db, meal_plan)


# Tolerance appliquee a l'allocation restante par repas : evite d'exclure
# une recette au score bien meilleur pour un depassement mineur (25%).
BUDGET_TOLERANCE_FACTOR = 1.25

# Nombre de candidats (parmi les mieux scores/dans le budget) parmi lesquels
# on tire au hasard, pour varier les plans generes sans sacrifier la
# pertinence (regle : plus de 200 recettes disponibles, il faut les faire
# tourner au lieu de toujours proposer les memes).
RECIPE_VARIETY_POOL_SIZE = 6


def _get_weekly_budget(db: Session, meal_plan: MealPlan) -> float:
    """Budget hebdo actuel du profil (regle 4/10). Toujours relu depuis
    Profile plutot que stocke sur le MealPlan : si l'utilisateur change son
    budget, un plan deja genere doit refleter le nouveau chiffre a la
    prochaine regeneration/consultation."""
    profile = db.execute(
        select(Profile).where(Profile.user_id == meal_plan.user_id)
    ).scalar_one_or_none()
    if profile is None or profile.food_budget_per_week is None:
        return 0.0
    return float(profile.food_budget_per_week)


def _pick_budget_aware_candidate(
    candidates: list[dict],
    used_recipe_ids: set,
    per_meal_allowance: Optional[float],
) -> Optional[dict]:
    """Choisit, parmi les candidats deja tries par score decroissant, un
    bon candidat qui reste sous l'enveloppe budgetaire du repas courant.

    Ordre de preference (jamais d'invention de prix, regle 8) :
    1. Cout par portion CONNU et <= allowance*1.25
    2. Cout INCONNU (neutre, ni favorise ni exclu)
    3. Le moins cher parmi ceux dont le cout est CONNU mais depasse
       l'enveloppe (repli qui tire le plan vers le budget plutot que de
       l'ignorer completement quand tout est cher)

    Variete : plus de 200 recettes existent en base, mais un score
    deterministe renverrait toujours les 28 memes recettes (7 jours x 4
    repas) a chaque regeneration. On tire donc au hasard parmi les
    meilleurs candidats de chaque groupe (au lieu de toujours le tout
    premier) pour varier les plans sans sacrifier la pertinence.
    """
    available = [c for c in candidates if c["recipe"].id not in used_recipe_ids]
    if not available:
        return None
    if per_meal_allowance is None:
        return random.choice(available[:RECIPE_VARIETY_POOL_SIZE])

    within_budget, unknown_cost, over_budget = [], [], []
    for candidate in available:
        cost = candidate["recipe"].cost_per_serving_da
        if cost is None:
            unknown_cost.append(candidate)
        elif float(cost) <= per_meal_allowance * BUDGET_TOLERANCE_FACTOR:
            within_budget.append(candidate)
        else:
            over_budget.append(candidate)

    if within_budget:
        return random.choice(within_budget[:RECIPE_VARIETY_POOL_SIZE])
    if unknown_cost:
        return random.choice(unknown_cost[:RECIPE_VARIETY_POOL_SIZE])
    # Repli sur le moins cher : ici on reste deterministe, l'objectif est
    # de proteger le budget plutot que de varier.
    return min(over_budget, key=lambda c: float(c["recipe"].cost_per_serving_da))


def attach_default_recipes(db: Session, meal_plan: MealPlan) -> bool:
    """Compatibility fallback for legacy plans when Spoonacular has no data.

    Lie le plan au budget hebdomadaire (regle 4/10) : les repas sont
    remplis dans l'ordre, en repartissant le budget restant sur les repas
    restants a chaque etape (allocation gloutonne), pour que le cout total
    de la semaine reste proche du budget plutot que de ne le traiter que
    comme une simple preference de score parmi d'autres.
    """
    changed = False
    used_recipe_ids = set()
    recommendations_by_type = {}

    weekly_budget = _get_weekly_budget(db, meal_plan)
    pending_meals = [
        meal for day in meal_plan.days for meal in day.meals if not meal.items
    ]
    remaining_budget = weekly_budget
    remaining_meals = len(pending_meals)

    for meal in pending_meals:
        meal_type = meal.meal_type.value
        if meal_type not in recommendations_by_type:
            recommendations_by_type[meal_type] = recommend_recipes(
                db,
                meal_plan.user_id,
                meal_type=meal_type,
                meal_calories_target=float(meal.target_calories_kcal or 0) or None,
                protein_target=float(meal.target_protein_g or 0) or None,
                # Un large pool permet de choisir une recette differente
                # chaque jour, au lieu de recycler les 20 premiers scores.
                limit=100,
                include_inventory=False,
            )
        candidates = recommendations_by_type[meal_type]

        per_meal_allowance = (
            (remaining_budget / remaining_meals)
            if weekly_budget > 0 and remaining_meals > 0
            else None
        )
        candidate = _pick_budget_aware_candidate(candidates, used_recipe_ids, per_meal_allowance)
        remaining_meals -= 1
        if candidate is None:
            continue
        recipe = candidate["recipe"]
        used_recipe_ids.add(recipe.id)
        meal.items.append(
            MealPlanMealItem(
                recipe_id=recipe.id,
                quantity=1,
                unit=MeasurementUnit.SERVING,
            )
        )
        changed = True

        if per_meal_allowance is not None:
            # Cout reel deduit du budget restant s'il est connu, sinon sa
            # "part equitable" (per_meal_allowance) pour que les repas
            # suivants ne soient pas faussement avantages/desavantages.
            spent = (
                float(recipe.cost_per_serving_da)
                if recipe.cost_per_serving_da is not None
                else per_meal_allowance
            )
            remaining_budget -= spent

    return changed


def compute_meal_plan_budget_summary(meal_plan: MealPlan, weekly_budget_da: float) -> dict:
    """Recap budgetaire du plan (regle 8 : jamais de total invente). Si au
    moins un repas a un cout inconnu, le total est signale comme un
    plancher ("partial") plutot que presente comme le cout reel complet."""
    total_known_cost = 0.0
    meals_with_recipe = 0
    meals_with_known_cost = 0

    for day in meal_plan.days:
        for meal in day.meals:
            if not meal.items or meal.items[0].recipe is None:
                continue
            meals_with_recipe += 1
            cost = meal.items[0].recipe.cost_per_serving_da
            if cost is not None:
                meals_with_known_cost += 1
                total_known_cost += float(cost)

    if meals_with_recipe == 0:
        status = "unknown"
    elif meals_with_known_cost < meals_with_recipe:
        status = "partial"
    elif weekly_budget_da <= 0:
        status = "no_budget_set"
    elif total_known_cost <= weekly_budget_da:
        status = "within_budget"
    else:
        status = "over_budget"

    return {
        "weekly_budget_da": weekly_budget_da if weekly_budget_da > 0 else None,
        "estimated_cost_da": round(total_known_cost, 2),
        "is_estimate_partial": meals_with_known_cost < meals_with_recipe,
        "meals_with_recipe": meals_with_recipe,
        "meals_with_known_cost": meals_with_known_cost,
        "status": status,
    }