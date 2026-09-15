"""
Routes Recettes.

    GET /recipes                                -> liste (recherche, filtres, pagination)
    GET /recipes/recommend/{user_id}            -> recommandations personnalisees (scoring local)
    GET /recipes/by-ingredient                  -> recettes contenant un aliment donne
    GET /recipes/from-inventory/{user_id}       -> recettes realisables avec le stock utilisateur
    GET /recipes/pre-workout / /post-workout    -> filtre heuristique sur les macros (regle 12)
    GET /recipes/{recipe_id}                    -> detail complet (ingredients, etapes, videos)
    GET /recipes/{recipe_id}/can-cook/{user_id} -> comparaison avec l'inventaire

La creation de recettes via l'API viendra dans une prochaine sous-etape
(pour l'instant, seed_recipes.py et scripts/import_recipes.py servent a
inserer des recettes).
"""

from typing import Optional
from urllib.parse import quote_plus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.models.enums import RecipeNutritionStatus
from app.models.food import Food, FoodTranslation
from app.models.recipe import Recipe, RecipeIngredient, RecipeStep, RecipeTranslation
from app.models.profile import Profile
from app.models.user import User
from app.services.recipe_availability import check_recipe_availability
from app.services.recipe_recommender import recommend_recipes
from app.services.spoonacular import search_spoonacular_recipes

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/spoonacular/search")
def search_external_recipes(
    q: str = Query(..., min_length=2, max_length=100),
    diet: Optional[str] = Query(None, max_length=80),
    meal_type: Optional[str] = Query(None, max_length=40),
    offset: int = Query(0, ge=0, le=900),
    number: int = Query(20, ge=1, le=100),
):
    return search_spoonacular_recipes(q, offset, number, diet, meal_type)


# [SPOONACULAR REMOVAL - STEP 1] Route conservée pour compatibilité frontend,
# mais elle utilise désormais le moteur de recommandation local PostgreSQL.
@router.get("/spoonacular/recommend/{user_id}")
def recommend_recipes_for_user(
    user_id: UUID,
    meal_type: str = Query("lunch", max_length=30),
    budget_per_week: float | None = Query(None, gt=0),
    limit: int = Query(20, ge=1, le=100),
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil introuvable.")

    goal = profile.primary_goal.value if profile.primary_goal else "general_health"
    meal_calories_target = 700 if goal == "weight_loss" else 900

    results = recommend_recipes(
        db,
        user_id,
        meal_type=meal_type,
        meal_calories_target=meal_calories_target,
        limit=limit,
    )

    items = []
    for entry in results:
        recipe: Recipe = entry["recipe"]
        items.append({
            **_serialize_recipe_summary(recipe, language),
            "score": entry["score"],
            "score_components": entry["score_components"],
            "availability": entry["availability"],
        })

    return {
        "source": "local",
        "user_id": str(user_id),
        "personalization": {
            "goal": goal,
            "meal_type": meal_type,
            "meal_calories_target": meal_calories_target,
            "budget_per_week": budget_per_week or profile.food_budget_per_week,
            "budget_note": "Le budget est pris en compte par le scoring local (coût estimé des recettes PostgreSQL).",
        },
        "total": len(items),
        "items": items,
    }


# ============================================================
# RECOMMANDATIONS LOCALES (scoring sur recettes de la base)
# ============================================================

@router.get("/recommend/{user_id}")
def recommend_local_recipes(
    user_id: UUID,
    meal_type: Optional[str] = Query(None, max_length=30,
        description="breakfast | lunch | dinner | snack"),
    meal_calories_target: Optional[float] = Query(None, gt=0),
    protein_target: Optional[float] = Query(None, gt=0),
    limit: int = Query(20, ge=1, le=100),
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    """Recettes locales compatibles avec le profil, triees par score
    decroissant (contraintes obligatoires puis scoring)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    results = recommend_recipes(
        db,
        user_id,
        meal_type=meal_type,
        meal_calories_target=meal_calories_target,
        protein_target=protein_target,
        limit=limit,
    )

    items = []
    for entry in results:
        recipe: Recipe = entry["recipe"]
        items.append({
            **_serialize_recipe_summary(recipe, language),
            "score": entry["score"],
            "score_components": entry["score_components"],
            "availability": entry["availability"],
        })

    return {
        "user_id": str(user_id),
        "meal_type": meal_type,
        "meal_calories_target": meal_calories_target,
        "protein_target": protein_target,
        "total": len(items),
        "items": items,
    }


# ============================================================
# HELPERS DE SERIALISATION
# ============================================================

def _recipe_translation(recipe: Recipe, language: str) -> Optional[RecipeTranslation]:
    """Traduction dans la langue demandee, avec fallback propre si absente :
    langue demandee -> anglais (langue source de l'import Wikibooks) ->
    francais (langue par defaut du projet) -> n'importe quelle traduction
    disponible -> None (seul cas ou l'appelant retombe sur le slug)."""
    by_language = {t.language_code: t for t in recipe.translations}
    for candidate in (language, "en", "fr"):
        if candidate in by_language:
            return by_language[candidate]
    return next(iter(recipe.translations), None)


def _humanize_slug(slug: str) -> str:
    """Dernier recours d'affichage quand aucune traduction n'existe du
    tout : un slug lisible plutot que le slug brut avec tirets/underscores."""
    return slug.replace("-", " ").replace("_", " ").strip().capitalize()


def _food_translation(food: Food, language: str) -> Optional[FoodTranslation]:
    """Meme logique de fallback que _recipe_translation, pour les noms
    d'aliments dans le detail d'une recette."""
    by_language = {t.language_code: t for t in food.translations}
    for candidate in (language, "en", "fr"):
        if candidate in by_language:
            return by_language[candidate]
    return next(iter(food.translations), None)


def youtube_search_url(recipe_name: str) -> str:
    # Recherche YouTube par nom, sans inventer une video precise.
    return f"https://www.youtube.com/results?search_query={quote_plus(recipe_name.strip())}"


def _serialize_recipe_summary(recipe: Recipe, language: str) -> dict:
    translation = _recipe_translation(recipe, language)

    return {
        "id": str(recipe.id),
        "slug": recipe.slug,
        "name": translation.name if translation else _humanize_slug(recipe.slug),
        "description": translation.description if translation else None,
        "youtube_search_url": youtube_search_url(translation.name if translation else _humanize_slug(recipe.slug)),
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "difficulty": recipe.difficulty.value if recipe.difficulty else None,
        "servings": recipe.servings,
        "calories_kcal": float(recipe.calories_kcal) if recipe.calories_kcal is not None else None,
        "protein_g": float(recipe.protein_g) if recipe.protein_g is not None else None,
        "carbs_g": float(recipe.carbs_g) if recipe.carbs_g is not None else None,
        "fat_g": float(recipe.fat_g) if recipe.fat_g is not None else None,
        "fiber_g": float(recipe.fiber_g) if recipe.fiber_g is not None else None,
        "sugar_g": float(recipe.sugar_g) if recipe.sugar_g is not None else None,
        "sodium_mg": float(recipe.sodium_mg) if recipe.sodium_mg is not None else None,
        "nutrition_status": recipe.nutrition_status.value,
        "image_url": recipe.image_url,
        "estimated_cost_level": recipe.estimated_cost_level,
        "cost_per_serving_da": float(recipe.cost_per_serving_da) if recipe.cost_per_serving_da is not None else None,
        "cost_status": recipe.cost_status.value,
        "is_vegetarian": recipe.is_vegetarian,
        "is_vegan": recipe.is_vegan,
        "is_halal": recipe.is_halal,
        "halal_status": recipe.halal_status.value,
        "is_gluten_free": recipe.is_gluten_free,
    }


# ============================================================
# LISTE DES RECETTES
# ============================================================

@router.get("")
def list_recipes(
    search: Optional[str] = Query(None, description="Recherche par nom ou slug"),
    language: str = Query("fr", min_length=2, max_length=5),
    is_vegetarian: Optional[bool] = None,
    is_vegan: Optional[bool] = None,
    is_halal: Optional[bool] = None,
    is_gluten_free: Optional[bool] = None,
    max_cost_level: Optional[int] = Query(None, ge=1, le=3),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = (
        select(Recipe)
        .outerjoin(
            RecipeTranslation,
            (RecipeTranslation.recipe_id == Recipe.id)
            & (RecipeTranslation.language_code == language),
        )
        .options(selectinload(Recipe.translations))
    )

    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Recipe.slug.ilike(pattern)) | (RecipeTranslation.name.ilike(pattern))
        )

    if is_vegetarian is not None:
        query = query.where(Recipe.is_vegetarian == is_vegetarian)
    if is_vegan is not None:
        query = query.where(Recipe.is_vegan == is_vegan)
    if is_halal is not None:
        query = query.where(Recipe.is_halal == is_halal)
    if is_gluten_free is not None:
        query = query.where(Recipe.is_gluten_free == is_gluten_free)
    if max_cost_level is not None:
        query = query.where(Recipe.estimated_cost_level <= max_cost_level)

    all_matches = db.execute(query).unique().scalars().all()
    total = len(all_matches)

    page = sorted(all_matches, key=lambda r: r.slug)[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "language": language,
        "items": [_serialize_recipe_summary(recipe, language) for recipe in page],
    }


# ============================================================
# RECHERCHE PAR INGREDIENT / INVENTAIRE / MOMENT SPORT
# ============================================================

@router.get("/by-ingredient")
def list_recipes_by_ingredient(
    food_slug: str = Query(..., min_length=1, max_length=100),
    language: str = Query("fr", min_length=2, max_length=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Recettes contenant un aliment donne (regle 23)."""
    food = db.execute(select(Food).where(Food.slug == food_slug)).scalar_one_or_none()
    if food is None:
        raise HTTPException(status_code=404, detail="Aliment introuvable.")

    query = (
        select(Recipe)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .where(RecipeIngredient.food_id == food.id)
        .options(selectinload(Recipe.translations))
    )
    all_matches = db.execute(query).unique().scalars().all()
    total = len(all_matches)
    page = sorted(all_matches, key=lambda r: r.slug)[offset : offset + limit]

    return {
        "food_slug": food.slug,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_serialize_recipe_summary(recipe, language) for recipe in page],
    }


@router.get("/from-inventory/{user_id}")
def list_recipes_from_inventory(
    user_id: UUID,
    min_ratio: float = Query(0.8, ge=0.0, le=1.0,
        description="Part minimale d'ingredients disponibles (0.8 = 80%, regle 15)"),
    language: str = Query("fr", min_length=2, max_length=5),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Recettes realisables avec le stock de l'utilisateur (regle 15).
    Note perf : une requete d'inventaire par recette (check_recipe_availability) ;
    acceptable tant que le nombre de recettes reste modeste (a revoir si ca grossit).
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    recipes = db.execute(
        select(Recipe).options(selectinload(Recipe.translations), selectinload(Recipe.ingredients))
    ).unique().scalars().all()

    results = []
    for recipe in recipes:
        availability = check_recipe_availability(db, recipe, user_id)
        ingredients = availability.get("ingredients") or []
        if not ingredients:
            continue
        ok_count = sum(1 for item in ingredients if item["status"] == "ok")
        ratio = ok_count / len(ingredients)
        if ratio >= min_ratio:
            results.append({
                **_serialize_recipe_summary(recipe, language),
                "availability_ratio": round(ratio, 2),
                "can_cook": availability["can_cook"],
                "missing_ingredients": [i["food_slug"] for i in ingredients if i["status"] != "ok"],
            })

    results.sort(key=lambda r: r["availability_ratio"], reverse=True)

    return {
        "user_id": str(user_id),
        "min_ratio": min_ratio,
        "total": len(results),
        "items": results[:limit],
    }


# Seuils heuristiques (regle 12) : le projet n'a pas de champ dedie
# pre_workout/post_workout (MealType reste breakfast/lunch/dinner/snack,
# partage avec les repas reellement logges). Plutot que d'ajouter une
# migration qui toucherait aussi le modele Meal, on filtre sur les macros
# deja calculees par recipe_enrichment (etape 7), en l'assumant explicitement
# comme une classification approximative.
PRE_WORKOUT_MIN_CARBS_G = 30
POST_WORKOUT_MIN_PROTEIN_G = 20


@router.get("/pre-workout")
def list_pre_workout_recipes(
    language: str = Query("fr", min_length=2, max_length=5),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Classification heuristique (pas de champ dedie en base, voir
    commentaire ci-dessus) : recettes riches en glucides, pour l'energie
    avant l'effort (regle 12). Ne considere que les recettes dont la
    nutrition a pu etre calculee au moins partiellement."""
    query = (
        select(Recipe)
        .where(Recipe.nutrition_status != RecipeNutritionStatus.UNKNOWN)
        .where(Recipe.carbs_g >= PRE_WORKOUT_MIN_CARBS_G)
        .options(selectinload(Recipe.translations))
    )
    recipes = sorted(
        db.execute(query).unique().scalars().all(),
        key=lambda r: float(r.carbs_g or 0),
        reverse=True,
    )[:limit]

    return {
        "criteria": f"carbs_g >= {PRE_WORKOUT_MIN_CARBS_G} par portion (heuristique)",
        "total": len(recipes),
        "items": [_serialize_recipe_summary(recipe, language) for recipe in recipes],
    }


@router.get("/post-workout")
def list_post_workout_recipes(
    language: str = Query("fr", min_length=2, max_length=5),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Classification heuristique (voir commentaire ci-dessus) : recettes
    riches en proteines, pour la recuperation apres l'effort (regle 12)."""
    query = (
        select(Recipe)
        .where(Recipe.nutrition_status != RecipeNutritionStatus.UNKNOWN)
        .where(Recipe.protein_g >= POST_WORKOUT_MIN_PROTEIN_G)
        .options(selectinload(Recipe.translations))
    )
    recipes = sorted(
        db.execute(query).unique().scalars().all(),
        key=lambda r: float(r.protein_g or 0),
        reverse=True,
    )[:limit]

    return {
        "criteria": f"protein_g >= {POST_WORKOUT_MIN_PROTEIN_G} par portion (heuristique)",
        "total": len(recipes),
        "items": [_serialize_recipe_summary(recipe, language) for recipe in recipes],
    }


# ============================================================
# DETAIL D'UNE RECETTE
# ============================================================

@router.get("/{recipe_id}")
def get_recipe(
    recipe_id: UUID,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    recipe = db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.translations),
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps).selectinload(RecipeStep.translations),
            selectinload(Recipe.videos),
        )
    ).scalar_one_or_none()

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable.")

    summary = _serialize_recipe_summary(recipe, language)

    ingredients = []
    for ingredient in recipe.ingredients:
        food_translation = _food_translation(ingredient.food, language)
        ingredients.append(
            {
                "food_slug": ingredient.food.slug,
                "food_name": food_translation.name if food_translation else _humanize_slug(ingredient.food.slug),
                "quantity": float(ingredient.quantity),
                "unit": ingredient.unit.value,
            }
        )

    steps = []
    for step in recipe.steps:
        by_language = {t.language_code: t for t in step.translations}
        step_translation = (
            by_language.get(language)
            or by_language.get("en")
            or by_language.get("fr")
            or next(iter(step.translations), None)
        )
        steps.append(
            {
                "step_number": step.step_number,
                "instruction": step_translation.instruction if step_translation else None,
                "image_url": step.image_url,
            }
        )

    videos = [
        {
            "url": video.url,
            "platform": video.platform.value,
            "title": video.title,
            "thumbnail_url": video.thumbnail_url,
            "language": video.language_code,
        }
        for video in recipe.videos
        if video.language_code == language
    ] or [
        {
            "url": video.url,
            "platform": video.platform.value,
            "title": video.title,
            "thumbnail_url": video.thumbnail_url,
            "language": video.language_code,
        }
        for video in recipe.videos
    ]

    return {
        **summary,
        "ingredients": ingredients,
        "steps": steps,
        "videos": videos,
        # Toujours disponible, meme quand aucune video n'est stockee en DB.
        "youtube_search_url": youtube_search_url(summary["name"]),
    }


# ============================================================
# LIEN AVEC L'INVENTAIRE
# ============================================================

@router.get("/{recipe_id}/can-cook/{user_id}")
def can_cook_recipe(
    recipe_id: UUID,
    user_id: UUID,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    recipe = db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.ingredients),
            selectinload(Recipe.translations),
        )
    ).scalar_one_or_none()

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    translation = _recipe_translation(recipe, language)

    availability = check_recipe_availability(db, recipe, user_id)

    return {
        "recipe_id": str(recipe.id),
        "recipe_slug": recipe.slug,
        "recipe_name": translation.name if translation else _humanize_slug(recipe.slug),
        "user_id": str(user_id),
        **availability,
    }
