"""
Outils backend Fitapp utilisables par l'Assistant IA (Function Calling).

Ce module implémente les 9 outils demandés :
1. get_user_profile
2. get_today_nutrition
3. get_meals_today
4. search_food
5. get_food
6. calculate_meal
7. get_goal
8. get_inventory
9. get_training

Chaque outil :
- s'exécute strictement à travers les modèles et services existants de Fitapp
- ne donne AUCUN accès SQL direct au modèle IA
- filtre les données pour ne renvoyer que le strict nécessaire
- gère proprement les conversions de types (Decimal -> float)
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.food import Food, FoodPrice, FoodTranslation
from app.models.inventory import Inventory, InventoryItem
from app.models.meal import Meal, MealItem
from app.models.profile import Profile
from app.models.user import User
from app.services.meal_calculator import calculate_food_nutrition, calculate_meal as base_calculate_meal
from app.services.nutrition import calculate_calories
from app.services.training_recommender import recommend_workout
from app.services.training_service import get_user_sports
from app.services.training_session_translations import translate_session_name

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Serialisation des objets ORM Exercise imbriques dans le dict
# retourne par recommend_workout() (module Sport, etape 6).
# Meme logique que _serialize_recommendation dans routes/sport.py
# (pas duplique tel quel pour eviter une dependance vers la couche
# routes depuis un service) : convertit chaque Exercise ORM en dict
# JSON-serialisable avant de le renvoyer au modele IA.
# ------------------------------------------------------------

def _tool_exercise_to_dict(exercise, language: str = "fr") -> Optional[Dict[str, Any]]:
    if exercise is None:
        return None
    translations = exercise.translations or []
    match = next((t for t in translations if t.language_code == language), None)
    name = match.name if match else (translations[0].name if translations else exercise.slug)
    return {
        "slug": exercise.slug,
        "name": name,
        "category": exercise.category,
        "equipment": exercise.equipment,
        "difficulty": exercise.difficulty.value if exercise.difficulty else None,
    }


def _tool_serialize_recommendation(recommendation: Optional[dict], language: str = "fr") -> Optional[Dict[str, Any]]:
    if not recommendation:
        return None

    def _bookend(entry: Optional[dict]) -> Optional[dict]:
        if not entry:
            return None
        return {**entry, "exercise": _tool_exercise_to_dict(entry.get("exercise"), language)}

    return {
        "session_name": translate_session_name(recommendation.get("session_name"), language),
        "goal": recommendation["goal"].value if recommendation.get("goal") else None,
        "training_type": recommendation["training_type"].value if recommendation.get("training_type") else None,
        "difficulty": recommendation["difficulty"].value if recommendation.get("difficulty") else None,
        "level": recommendation["level"].value if recommendation.get("level") else None,
        "planned_duration_minutes": recommendation.get("planned_duration_minutes"),
        "target_rpe": float(recommendation["target_rpe"]) if recommendation.get("target_rpe") is not None else None,
        "warmup": _bookend(recommendation.get("warmup")),
        "cooldown": _bookend(recommendation.get("cooldown")),
        "exercises": [
            {
                **{k: v for k, v in item.items() if k != "exercise" and k != "sets"},
                "exercise": _tool_exercise_to_dict(item.get("exercise"), language),
            }
            for item in recommendation.get("exercises", [])
        ],
        "finisher": _bookend(recommendation.get("finisher")),
    }


# ============================================================
# DÉCLARATION DES SCHÉMAS D'OUTILS (SPEC KIE AI / GPT-6 ASTRA)
# Format plat requis par Kie AI : {"type": "function", "name": "...", "description": "...", "parameters": {...}}
# ============================================================

FITAPP_TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_user_profile",
        "description": "Récupère les informations de profil de l'utilisateur (âge, sexe, taille, poids, niveau d'activité, préférences, etc.).",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "type": "function",
        "name": "get_today_nutrition",
        "description": "Récupère le bilan nutritionnel du jour (calories et macronutriments consommés vs cibles quotidiennes). Permet de savoir ce qu'il reste à consommer.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {
                    "type": "string",
                    "description": "Date au format YYYY-MM-DD. Si omise, la date du jour est utilisée.",
                }
            },
        },
    },
    {
        "type": "function",
        "name": "get_meals_today",
        "description": "Liste les repas et aliments enregistrés par l'utilisateur aujourd'hui avec leurs portions et calories.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {
                    "type": "string",
                    "description": "Date au format YYYY-MM-DD. Si omise, la date du jour est utilisée.",
                }
            },
        },
    },
    {
        "type": "function",
        "name": "search_food",
        "description": "Recherche un aliment dans la base de données nutritionnelle officielle de Fitapp par mot-clé.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nom ou terme de recherche (ex: 'riz', 'poulet', 'avocat')",
                },
                "language": {
                    "type": "string",
                    "description": "Code langue ('fr', 'en', 'es', 'ar'). Par défaut 'fr'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Nombre maximum d'aliments à retourner (défaut 5).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "get_food",
        "description": "Récupère les détails nutritionnels complets pour 100g d'un aliment précis par son slug ou ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "food_identifier": {
                    "type": "string",
                    "description": "Slug ou UUID de l'aliment (ex: 'riz-blanc-cuit' ou 'riz')",
                },
                "language": {
                    "type": "string",
                    "description": "Code langue (défaut 'fr').",
                },
            },
            "required": ["food_identifier"],
        },
    },
    {
        "type": "function",
        "name": "calculate_meal",
        "description": "Calcule exactement les calories et macronutriments (protéines, glucides, lipides) pour une liste d'aliments et quantités.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Liste des aliments composant le repas ou la portion",
                    "items": {
                        "type": "object",
                        "properties": {
                            "food_slug": {
                                "type": "string",
                                "description": "Slug de l'aliment (ex: 'riz', 'flocons-d-avoine')",
                            },
                            "quantity": {
                                "type": "number",
                                "description": "Quantité numérique (ex: 150)",
                            },
                            "unit": {
                                "type": "string",
                                "description": "Unité de mesure ('g', 'kg', 'ml', 'l', 'piece')",
                            },
                        },
                        "required": ["food_slug", "quantity", "unit"],
                    },
                }
            },
            "required": ["items"],
        },
    },
    {
        "type": "function",
        "name": "get_goal",
        "description": "Récupère les objectifs de l'utilisateur (perte de poids, prise de masse, maintien, calories cibles, macros cibles).",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "type": "function",
        "name": "get_inventory",
        "description": "Consulte le stock d'aliments disponibles chez l'utilisateur (frigo, congélateur, placard), et les produits bientôt périmés.",
        "parameters": {
            "type": "object",
            "properties": {
                "inventory_type": {
                    "type": "string",
                    "description": "Optionnel: 'fridge', 'freezer', 'pantry' pour filtrer.",
                }
            },
        },
    },
    {
        "type": "function",
        "name": "get_training",
        "description": "Récupère les séances de sport prévues aujourd'hui, les sports pratiqués et les recommandations d'entraînement.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


# ============================================================
# IMPLÉMENTATION DES OUTILS FITAPP
# ============================================================

class FitappToolsExecutor:
    """Exécuteur d'outils encapsulé et sécurisé pour l'Assistant IA."""

    def __init__(self, db: Session, user_id: Optional[UUID], language: str = "fr"):
        self.db = db
        self.user_id = user_id
        self.language = language

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route et exécute un outil par son nom."""
        method = getattr(self, f"tool_{tool_name}", None)
        if method is None:
            logger.warning(f"Outil inconnu demandé : {tool_name}")
            return {"error": f"Outil inconnu : '{tool_name}'"}

        try:
            return method(**arguments)
        except Exception as exc:
            logger.exception(f"Erreur lors de l'exécution du tool {tool_name}: {exc}")
            return {"error": f"Échec de l'outil {tool_name}: {str(exc)}"}

    # 1. get_user_profile
    def tool_get_user_profile(self) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        user = self.db.get(User, self.user_id)
        if not user:
            return {"error": "Utilisateur introuvable."}

        profile = self.db.execute(
            select(Profile).where(Profile.user_id == self.user_id)
        ).scalar_one_or_none()

        data: Dict[str, Any] = {
            "username": user.username,
            "preferred_language": user.preferred_language,
        }

        if profile:
            data.update({
                "age": profile.age,
                "sex": profile.sex.value if profile.sex else None,
                "height_cm": float(profile.height_cm) if profile.height_cm is not None else None,
                "current_weight_kg": float(profile.current_weight_kg) if profile.current_weight_kg is not None else None,
                "activity_level": profile.activity_level.value if profile.activity_level else None,
                "primary_goal": profile.primary_goal.value if profile.primary_goal else None,
                "unit_system": profile.unit_system.value if profile.unit_system else "metric",
                "dietary_preferences": profile.dietary_preferences,
                "allergies": profile.allergies,
                "halal_required": profile.halal_required,
            })

        return data

    # 2. get_today_nutrition
    def tool_get_today_nutrition(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        target_date = date.today()
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                pass

        # Totaux consommés
        totals = self.db.execute(
            select(
                func.coalesce(func.sum(Meal.total_calories_kcal), 0),
                func.coalesce(func.sum(Meal.total_protein_g), 0),
                func.coalesce(func.sum(Meal.total_carbs_g), 0),
                func.coalesce(func.sum(Meal.total_fat_g), 0),
            ).where(Meal.user_id == self.user_id, Meal.consumed_on == target_date)
        ).one()

        consumed = {
            "calories_kcal": round(float(totals[0]), 1),
            "protein_g": round(float(totals[1]), 1),
            "carbs_g": round(float(totals[2]), 1),
            "fat_g": round(float(totals[3]), 1),
        }

        result: Dict[str, Any] = {
            "date": target_date.isoformat(),
            "consumed": consumed,
        }

        # Cibles calculées depuis le profil
        profile = self.db.execute(
            select(Profile).where(Profile.user_id == self.user_id)
        ).scalar_one_or_none()

        if profile and all(getattr(profile, f) is not None for f in (
            "age", "sex", "height_cm", "current_weight_kg", "activity_level", "primary_goal"
        )):
            targets = calculate_calories(
                weight_kg=float(profile.current_weight_kg),
                height_cm=float(profile.height_cm),
                age=profile.age,
                sex=profile.sex,
                activity_level=profile.activity_level,
                goal=profile.primary_goal,
            )
            result["targets"] = {
                "daily_calories": targets["daily_calories"],
                "protein_g": targets["protein_g"],
                "carbs_g": targets["carbs_g"],
                "fat_g": targets["fat_g"],
            }
            # Reste à consommer
            result["remaining"] = {
                "calories_kcal": round(max(0.0, targets["daily_calories"] - consumed["calories_kcal"]), 1),
                "protein_g": round(max(0.0, targets["protein_g"] - consumed["protein_g"]), 1),
                "carbs_g": round(max(0.0, targets["carbs_g"] - consumed["carbs_g"]), 1),
                "fat_g": round(max(0.0, targets["fat_g"] - consumed["fat_g"]), 1),
            }

        return result

    # 3. get_meals_today
    def tool_get_meals_today(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        target_date = date.today()
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                pass

        meals = self.db.execute(
            select(Meal)
            .options(selectinload(Meal.items).selectinload(MealItem.food))
            .where(Meal.user_id == self.user_id, Meal.consumed_on == target_date)
            .order_by(Meal.consumed_at.asc().nullslast())
        ).scalars().all()

        meals_data = []
        for meal in meals:
            items_data = []
            for item in meal.items:
                items_data.append({
                    "food": item.food.slug if item.food else "inconnu",
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "calories_kcal": float(item.calories_kcal),
                    "protein_g": float(item.protein_g),
                    "carbs_g": float(item.carbs_g),
                    "fat_g": float(item.fat_g),
                })
            meals_data.append({
                "meal_type": meal.meal_type.value if hasattr(meal.meal_type, "value") else str(meal.meal_type),
                "name": meal.name,
                "total_calories_kcal": float(meal.total_calories_kcal),
                "total_protein_g": float(meal.total_protein_g),
                "total_carbs_g": float(meal.total_carbs_g),
                "total_fat_g": float(meal.total_fat_g),
                "items": items_data,
            })

        return {
            "date": target_date.isoformat(),
            "meals_count": len(meals_data),
            "meals": meals_data,
        }

    # 4. search_food
    def tool_search_food(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        lang = language or self.language or "fr"
        limit = max(1, min(limit, 10))
        pattern = f"%{query.strip()}%"

        foods_q = (
            self.db.query(Food)
            .outerjoin(
                FoodTranslation,
                (FoodTranslation.food_id == Food.id) & (FoodTranslation.language_code == lang),
            )
            .filter((Food.slug.ilike(pattern)) | (FoodTranslation.name.ilike(pattern)))
            .limit(limit)
            .all()
        )

        results = []
        for food in foods_q:
            tr = next((t for t in food.translations if t.language_code == lang), None)
            results.append({
                "slug": food.slug,
                "name": tr.name if tr else food.slug,
                "calories_kcal_per_100g": float(food.calories_kcal),
                "protein_g_per_100g": float(food.protein_g),
                "carbs_g_per_100g": float(food.carbs_g),
                "fat_g_per_100g": float(food.fat_g),
                "default_unit": food.default_unit,
                "unit_weight_g": float(food.unit_weight_g) if food.unit_weight_g else None,
            })

        return {
            "query": query,
            "count": len(results),
            "foods": results,
        }

    # 5. get_food
    def tool_get_food(
        self,
        food_identifier: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        lang = language or self.language or "fr"
        query_str = food_identifier.strip()

        # Essai par UUID puis par slug
        food = None
        try:
            food_uuid = UUID(query_str)
            food = self.db.get(Food, food_uuid)
        except (ValueError, TypeError):
            food = None

        if not food:
            food = (
                self.db.query(Food)
                .filter(Food.slug.ilike(query_str))
                .first()
            )

        if not food:
            # Recherche partielle si slug exact non trouvé
            food = (
                self.db.query(Food)
                .filter(Food.slug.ilike(f"%{query_str}%"))
                .first()
            )

        if not food:
            return {"error": f"Aliment '{food_identifier}' introuvable dans la base Fitapp."}

        tr = next((t for t in food.translations if t.language_code == lang), None)

        return {
            "slug": food.slug,
            "name": tr.name if tr else food.slug,
            "per_100g": {
                "calories_kcal": float(food.calories_kcal),
                "protein_g": float(food.protein_g),
                "carbs_g": float(food.carbs_g),
                "fat_g": float(food.fat_g),
                "fiber_g": float(food.fiber_g) if food.fiber_g is not None else None,
                "sugar_g": float(food.sugar_g) if food.sugar_g is not None else None,
            },
            "unit_weight_g": float(food.unit_weight_g) if food.unit_weight_g is not None else None,
            "default_unit": food.default_unit,
        }

    # 6. calculate_meal
    def tool_calculate_meal(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not items:
            return {"error": "La liste d'aliments à calculer est vide."}

        calculated_items = []
        total_calories = Decimal("0")
        total_protein = Decimal("0")
        total_carbs = Decimal("0")
        total_fat = Decimal("0")

        for item in items:
            slug = item.get("food_slug") or item.get("slug")
            quantity = item.get("quantity")
            unit = item.get("unit", "g")

            if not slug or quantity is None:
                continue

            # Recherche Food
            food = (
                self.db.query(Food)
                .filter(Food.slug.ilike(slug.strip()))
                .first()
            )

            if not food:
                # Recherche partielle
                food = (
                    self.db.query(Food)
                    .filter(Food.slug.ilike(f"%{slug.strip()}%"))
                    .first()
                )

            if not food:
                return {"error": f"Aliment introuvable pour le calcul: '{slug}'"}

            try:
                nutr = calculate_food_nutrition(food=food, quantity=quantity, unit=unit)
            except Exception as exc:
                return {"error": f"Calcul impossible pour '{slug}': {str(exc)}"}

            total_calories += nutr["calories_kcal"]
            total_protein += nutr["protein_g"]
            total_carbs += nutr["carbs_g"]
            total_fat += nutr["fat_g"]

            calculated_items.append({
                "food_slug": food.slug,
                "quantity": float(quantity),
                "unit": unit,
                "grams": float(nutr["grams"]),
                "calories_kcal": float(nutr["calories_kcal"]),
                "protein_g": float(nutr["protein_g"]),
                "carbs_g": float(nutr["carbs_g"]),
                "fat_g": float(nutr["fat_g"]),
            })

        return {
            "items": calculated_items,
            "totals": {
                "calories_kcal": round(float(total_calories), 1),
                "protein_g": round(float(total_protein), 1),
                "carbs_g": round(float(total_carbs), 1),
                "fat_g": round(float(total_fat), 1),
            },
        }

    # 7. get_goal
    def tool_get_goal(self) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        profile = self.db.execute(
            select(Profile).where(Profile.user_id == self.user_id)
        ).scalar_one_or_none()

        if not profile:
            return {"error": "Profil utilisateur non complété."}

        goal_data: Dict[str, Any] = {
            "primary_goal": profile.primary_goal.value if profile.primary_goal else None,
            "current_weight_kg": float(profile.current_weight_kg) if profile.current_weight_kg is not None else None,
            "activity_level": profile.activity_level.value if profile.activity_level else None,
        }

        if all(getattr(profile, f) is not None for f in (
            "age", "sex", "height_cm", "current_weight_kg", "activity_level", "primary_goal"
        )):
            targets = calculate_calories(
                weight_kg=float(profile.current_weight_kg),
                height_cm=float(profile.height_cm),
                age=profile.age,
                sex=profile.sex,
                activity_level=profile.activity_level,
                goal=profile.primary_goal,
            )
            goal_data["nutrition_targets"] = targets

        return goal_data

    # 8. get_inventory
    def tool_get_inventory(self, inventory_type: Optional[str] = None) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        query = select(Inventory).where(Inventory.user_id == self.user_id)
        inventories = self.db.execute(query).scalars().all()

        items_list = []
        today = date.today()

        for inv in inventories:
            inv_type_val = inv.inventory_type.value if hasattr(inv.inventory_type, "value") else str(inv.inventory_type)
            if inventory_type and inv_type_val.lower() != inventory_type.lower():
                continue

            for item in inv.items:
                tr = next((t for t in item.food.translations if t.language_code == self.language), None)
                is_expired = item.expires_on is not None and item.expires_on < today
                is_expiring_soon = (
                    item.expires_on is not None
                    and not is_expired
                    and item.expires_on <= today + timedelta(days=3)
                )

                items_list.append({
                    "location": inv_type_val,
                    "food_slug": item.food.slug,
                    "food_name": tr.name if tr else item.food.slug,
                    "quantity": float(item.quantity),
                    "unit": item.unit.value if hasattr(item.unit, "value") else str(item.unit),
                    "expires_on": item.expires_on.isoformat() if item.expires_on else None,
                    "is_expired": is_expired,
                    "is_expiring_soon": is_expiring_soon,
                })

        return {
            "inventory_items_count": len(items_list),
            "items": items_list,
        }

    # 9. get_training
    def tool_get_training(self) -> Dict[str, Any]:
        if not self.user_id:
            return {"error": "Aucun utilisateur identifié."}

        sports = get_user_sports(self.db, self.user_id)
        sports_summary = [
            {
                "sport_name": s["sport"].slug if s.get("sport") else "Inconnu",
                "is_primary": s.get("is_primary", False),
                "level": s["level"].value if hasattr(s.get("level"), "value") else str(s.get("level")),
            }
            for s in sports
        ]

        try:
            workout_rec = recommend_workout(self.db, self.user_id)
            workout_rec = _tool_serialize_recommendation(workout_rec, self.language)
        except Exception:
            workout_rec = None

        return {
            "user_sports": sports_summary,
            "recommended_workout_today": workout_rec,
        }
