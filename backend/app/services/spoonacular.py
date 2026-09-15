import os
from typing import Any

import httpx
from fastapi import HTTPException

SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
SPOONACULAR_INFO_URL = "https://api.spoonacular.com/recipes/{recipe_id}/information"
SPOONACULAR_MEAL_TYPES = {
    "breakfast": "breakfast",
    "lunch": "main course",
    "dinner": "main course",
    "snack": "snack",
}


def search_spoonacular_recipes(
    query: str,
    offset: int = 0,
    number: int = 20,
    diet: str | None = None,
    meal_type: str | None = None,
    max_calories: float | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("SPOONACULAR_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Spoonacular n'est pas configure. Ajoutez SPOONACULAR_API_KEY dans backend/.env.",
        )

    params: dict[str, Any] = {
        "apiKey": api_key,
        "query": query,
        "offset": offset,
        "number": number,
        "addRecipeInformation": "true",
        "addRecipeNutrition": "true",
        "instructionsRequired": "true",
    }
    if diet:
        params["diet"] = diet
    if meal_type:
        params["type"] = SPOONACULAR_MEAL_TYPES.get(meal_type, meal_type)
    if max_calories:
        params["maxCalories"] = round(max_calories)

    try:
        response = httpx.get(SPOONACULAR_URL, params=params, timeout=20)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Spoonacular est momentanément inaccessible.") from exc

    if response.status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="La clé Spoonacular est invalide ou n'est pas une clé officielle Spoonacular.",
        )
    if response.status_code == 403:
        raise HTTPException(
            status_code=502,
            detail="Accès Spoonacular refusé. Vérifiez que la clé vient de spoonacular.com et que l'API Food/Recipe est activée, pas de RapidAPI.",
        )
    if response.status_code == 402:
        raise HTTPException(status_code=429, detail="Le quota Spoonacular est épuisé.")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Spoonacular a refusé la recherche.")

    payload = response.json()
    return {
        "source": "spoonacular",
        "query": query,
        "offset": payload.get("offset", offset),
        "total": payload.get("totalResults", 0),
        "items": [_serialize_recipe(recipe) for recipe in payload.get("results", [])],
    }


def get_spoonacular_recipe(recipe_id: int) -> dict[str, Any]:
    api_key = os.getenv("SPOONACULAR_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise HTTPException(status_code=503, detail="Spoonacular n'est pas configure.")
    try:
        response = httpx.get(
            SPOONACULAR_INFO_URL.format(recipe_id=recipe_id),
            params={"apiKey": api_key, "includeNutrition": "true"},
            timeout=20,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Spoonacular est momentanément inaccessible.") from exc
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Recette Spoonacular introuvable.")
    if response.status_code == 401:
        raise HTTPException(status_code=502, detail="La clé Spoonacular est invalide.")
    if response.status_code == 402:
        raise HTTPException(status_code=429, detail="Le quota Spoonacular est épuisé.")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Spoonacular a refusé la recette.")
    return _serialize_recipe(response.json())


def _serialize_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    nutrients = {
        nutrient.get("name"): nutrient.get("amount", 0)
        for nutrient in recipe.get("nutrition", {}).get("nutrients", [])
    }
    instructions = recipe.get("analyzedInstructions", [])
    steps = [
        {"number": step.get("number"), "step": step.get("step")}
        for group in instructions
        for step in group.get("steps", [])
    ]
    return {
        "id": recipe.get("id"),
        "label": recipe.get("title"),
        "name": recipe.get("title"),
        "description": recipe.get("summary"),
        "image": recipe.get("image"),
        "source": recipe.get("sourceName"),
        "url": recipe.get("sourceUrl"),
        "servings": recipe.get("servings"),
        "ingredient_lines": [
            ingredient.get("original")
            for ingredient in recipe.get("extendedIngredients", [])
        ],
        "steps": steps,
        "calories": _nutrient(nutrients, "Calories"),
        "protein_g": _nutrient(nutrients, "Protein"),
        "carbs_g": _nutrient(nutrients, "Carbohydrates"),
        "fat_g": _nutrient(nutrients, "Fat"),
        "total_time_minutes": recipe.get("readyInMinutes"),
        "diet_labels": recipe.get("diets", []),
        "health_labels": recipe.get("dishTypes", []),
    }


def _nutrient(nutrients: dict[str, Any], name: str) -> float:
    return round(float(nutrients.get(name, 0) or 0), 2)