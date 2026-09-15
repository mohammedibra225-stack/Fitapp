"""
Service de correspondance (matching) entre les aliments détectés par l'IA
et la base de données Food de Fitapp.

Prend en compte :
- La résolution multilingue via les FoodTranslation (FR, EN, AR, ES)
- Le slug des Food
- L'enrichissement avec les seuils de confiance (HIGH / MEDIUM)
- Le calcul nutritionnel via le service existant meal_calculator

Ce service est indépendant du fournisseur de vision : il consomme un
MealVisionAnalysis, peu importe le modèle qui l'a produit.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config_ai import (
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
)
from app.models.food import Food, FoodTranslation
from app.schemas.meal_analysis import (
    MatchedFoodAnalysisItem,
    MealAnalysisDetail,
    MealVisionAnalysis,
    MealVisionFood,
    NutritionTotals,
)
from app.services.meal_calculator import calculate_food_nutrition


def strip_accents(value: str) -> str:
    """Retire les accents d'une chaîne de caractères."""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def normalize_food_name(value: str) -> str:
    """Normalise un nom pour la comparaison : minuscules, sans ponctuation, sans accents."""
    val = strip_accents(value).lower()
    val = re.sub(r"[^a-z0-9\s]", " ", val)
    return re.sub(r"\s+", " ", val).strip()


class FoodIndex:
    """Index en mémoire des Food pour une recherche rapide multilingue."""

    def __init__(self, foods: List[Food]):
        self.foods_by_id: Dict[UUID, Food] = {f.id: f for f in foods}
        # maps normalized term -> food
        self.term_to_food: Dict[str, Food] = {}
        # maps original food slug -> food
        self.slug_to_food: Dict[str, Food] = {}

        for food in foods:
            self.slug_to_food[food.slug] = food
            norm_slug = normalize_food_name(food.slug.replace("_", " "))
            if norm_slug:
                self.term_to_food[norm_slug] = food

            for trans in food.translations:
                norm_trans = normalize_food_name(trans.name)
                if norm_trans and norm_trans not in self.term_to_food:
                    self.term_to_food[norm_trans] = food

    @classmethod
    def load_from_db(cls, db: Session) -> "FoodIndex":
        stmt = select(Food).options(selectinload(Food.translations))
        foods = db.execute(stmt).scalars().unique().all()
        return cls(foods)

    def find_food(self, query: str) -> Optional[Tuple[Food, float]]:
        """
        Recherche un aliment par correspondance exacte ou approchée.
        Retourne (Food, similarity_score) ou None si non trouvé.
        """
        norm_query = normalize_food_name(query)
        if not norm_query:
            return None

        # 1. Correspondance exacte sur terme ou slug
        if norm_query in self.term_to_food:
            return self.term_to_food[norm_query], 1.0

        # 2. Correspondance par sous-chaîne ou mot clé
        for term, food in self.term_to_food.items():
            if norm_query == term:
                return food, 1.0
            if (len(norm_query) >= 4 and norm_query in term) or (len(term) >= 4 and term in norm_query):
                return food, 0.90

        # 3. Fuzzy matching
        matches = difflib.get_close_matches(norm_query, list(self.term_to_food.keys()), n=1, cutoff=0.75)
        if matches:
            best_term = matches[0]
            ratio = difflib.SequenceMatcher(None, norm_query, best_term).ratio()
            return self.term_to_food[best_term], ratio

        return None


def get_translated_food_name(food: Food, language: str = "fr") -> str:
    """Récupère le nom traduit de l'aliment pour la langue souhaitée avec fallback."""
    for trans in food.translations:
        if trans.language_code == language:
            return trans.name
    # Fallback FR puis EN puis slug
    for trans in food.translations:
        if trans.language_code == "fr":
            return trans.name
    for trans in food.translations:
        if trans.language_code == "en":
            return trans.name
    return food.slug


def match_and_calculate_meal_items(
    db: Session,
    raw_analysis: MealVisionAnalysis,
    language: str = "fr",
) -> MealAnalysisDetail:
    """
    Rapproche chaque élément détecté par le modèle de vision avec la table Food,
    puis utilise Meal Calculator pour déterminer macros et calories.
    """
    food_index = FoodIndex.load_from_db(db)

    matched_items: List[MatchedFoodAnalysisItem] = []
    total_cals = Decimal("0")
    total_prot = Decimal("0")
    total_carbs = Decimal("0")
    total_fat = Decimal("0")
    total_fiber = Decimal("0")

    for item in raw_analysis.foods:
        match_result = food_index.find_food(item.name)
        if match_result is None and item.alternatives:
            # Essayer les alternatives suggérées par le modèle de vision
            for alt in item.alternatives:
                match_result = food_index.find_food(alt)
                if match_result:
                    break

        food: Optional[Food] = None
        match_score: float = 0.0
        if match_result:
            food, match_score = match_result

        # Déterminer si une confirmation ou correction est requise
        needs_confirmation = item.confidence < HIGH_CONFIDENCE_THRESHOLD or (match_score < 0.90)
        needs_correction = item.confidence < MEDIUM_CONFIDENCE_THRESHOLD or (food is None)

        if food is not None:
            # Calcul nutritionnel avec le Meal Calculator existant
            unit = item.unit.strip().lower() if item.unit else "g"
            # Si unité inconnue du calculator, repli sur "g"
            if unit not in ("g", "kg", "ml", "l", "piece", "unit", "pcs"):
                unit = "g"

            try:
                nutrition = calculate_food_nutrition(
                    food=food,
                    quantity=item.estimated_quantity,
                    unit=unit,
                )
                grams = float(nutrition["grams"])
                cals = float(nutrition["calories_kcal"])
                prot = float(nutrition["protein_g"])
                carbs = float(nutrition["carbs_g"])
                fat = float(nutrition["fat_g"])
                fiber = float(nutrition["fiber_g"])

                total_cals += Decimal(str(cals))
                total_prot += Decimal(str(prot))
                total_carbs += Decimal(str(carbs))
                total_fat += Decimal(str(fat))
                total_fiber += Decimal(str(fiber))

            except Exception:
                # Si le calcul échoue (ex: pièce sans unit_weight_g), on laisse vide pour saisie utilisateur
                grams = None
                cals = None
                prot = None
                carbs = None
                fat = None
                fiber = None
                needs_confirmation = True

            matched_items.append(
                MatchedFoodAnalysisItem(
                    detected_name=item.name,
                    matched=True,
                    matched_food_id=food.id,
                    matched_food_slug=food.slug,
                    matched_food_name=get_translated_food_name(food, language),
                    preparation=item.preparation,
                    confidence=round(item.confidence, 2),
                    alternatives=item.alternatives,
                    needs_confirmation=needs_confirmation,
                    needs_correction=needs_correction,
                    estimated_quantity=item.estimated_quantity,
                    estimated_unit=unit,
                    calculated_grams=grams,
                    calories_kcal=cals,
                    protein_g=prot,
                    carbs_g=carbs,
                    fat_g=fat,
                    fiber_g=fiber,
                )
            )
        else:
            # Aliment non trouvé en base
            matched_items.append(
                MatchedFoodAnalysisItem(
                    detected_name=item.name,
                    matched=False,
                    matched_food_id=None,
                    matched_food_slug=None,
                    matched_food_name=None,
                    preparation=item.preparation,
                    confidence=round(item.confidence, 2),
                    alternatives=item.alternatives,
                    needs_confirmation=True,
                    needs_correction=True,
                    estimated_quantity=item.estimated_quantity,
                    estimated_unit=item.unit or "g",
                    calculated_grams=None,
                    calories_kcal=None,
                    protein_g=None,
                    carbs_g=None,
                    fat_g=None,
                    fiber_g=None,
                )
            )

    totals = NutritionTotals(
        calories=float(round(total_cals, 1)),
        protein_g=float(round(total_prot, 1)),
        carbs_g=float(round(total_carbs, 1)),
        fat_g=float(round(total_fat, 1)),
        fiber_g=float(round(total_fiber, 1)),
    )

    return MealAnalysisDetail(
        meal_type=raw_analysis.meal_type,
        overall_confidence=round(raw_analysis.overall_confidence, 2),
        foods=matched_items,
        totals=totals,
        notes=raw_analysis.notes,
    )
