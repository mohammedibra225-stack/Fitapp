"""
Schémas Pydantic pour la fonctionnalité AI Meal Analysis.

Séparation stricte :
- Détection IA brute (MealVisionFood, MealVisionAnalysis)
- Résultat enrichi avec matching Food + Meal Calculator (MatchedFoodAnalysisItem, MealAnalysisResponse)
- Recalcul après correction utilisateur (MealAnalysisRecalculateRequest)

Le modèle de vision (Ollama / Qwen2.5-VL) ne renvoie QUE de l'identification
visuelle et des estimations de portions. Les valeurs nutritionnelles finales
proviennent toujours de la base Food de Fitapp et du Meal Calculator.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MealVisionFood(BaseModel):
    """Aliment détecté et estimé par le modèle de vision."""

    name: str = Field(..., description="Nom de l'aliment détecté (ex: rice, chicken breast, pomme)")
    estimated_quantity: float = Field(..., gt=0, description="Quantité estimée (dans l'unité 'unit')")
    unit: str = Field(default="g", description="Unité estimée (g, kg, ml, l, piece)")
    preparation: Optional[str] = Field(None, description="Préparation observée (cooked, grilled, raw, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Score de confiance entre 0.0 et 1.0")
    alternatives: List[str] = Field(default_factory=list, description="Alternatives possibles en cas de doute")


class MealVisionAnalysis(BaseModel):
    """Structure JSON renvoyée par le modèle de vision, après validation."""

    meal_type: str = Field(default="lunch", description="Type de repas déduit (breakfast, lunch, dinner, snack)")
    foods: List[MealVisionFood] = Field(default_factory=list, description="Liste des aliments identifiés")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance globale de l'analyse")
    notes: List[str] = Field(default_factory=list, description="Notes ou observations éventuelles de l'IA")


# Alias de compatibilité : l'ancien code (et d'éventuels scripts/tests) importait
# ces noms. Ils pointent désormais sur les schémas neutres ci-dessus.
GeminiVisionFoodItem = MealVisionFood
GeminiVisionAnalysis = MealVisionAnalysis


class MatchedFoodAnalysisItem(BaseModel):
    """
    Aliment après recherche dans la table Food et calcul nutritionnel
    par le Meal Calculator de Fitapp.
    """

    detected_name: str
    matched: bool = Field(..., description="Indique si l'aliment a été retrouvé dans la base Food")
    matched_food_id: Optional[UUID] = None
    matched_food_slug: Optional[str] = None
    matched_food_name: Optional[str] = None
    preparation: Optional[str] = None
    confidence: float
    alternatives: List[str] = Field(default_factory=list)
    needs_confirmation: bool = Field(..., description="True si confidence < HIGH_CONFIDENCE_THRESHOLD")
    needs_correction: bool = Field(..., description="True si confidence < MEDIUM_CONFIDENCE_THRESHOLD ou non trouvé")

    # Quantités
    estimated_quantity: float
    estimated_unit: str
    calculated_grams: Optional[float] = None

    # Valeurs nutritionnelles calculées par Meal Calculator (JAMAIS par le modèle de vision)
    calories_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class NutritionTotals(BaseModel):
    """Totaux nutritionnels calculés."""

    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0


class MealAnalysisDetail(BaseModel):
    """Détail complet d'une analyse."""

    analysis_id: Optional[UUID] = None
    meal_type: str
    overall_confidence: float
    foods: List[MatchedFoodAnalysisItem] = Field(default_factory=list)
    totals: NutritionTotals = Field(default_factory=NutritionTotals)
    notes: List[str] = Field(default_factory=list)


class MealAnalysisResponse(BaseModel):
    """Réponse de l'endpoint POST /api/v1/meal-analysis/analyze."""

    success: bool = True
    analysis: MealAnalysisDetail


class UserCorrectionItem(BaseModel):
    """Correction apportée par l'utilisateur pour un item analysé."""

    food_slug: str = Field(..., min_length=1, description="Slug de l'aliment choisi dans la base")
    quantity: float = Field(..., gt=0, description="Quantité ajustée")
    unit: str = Field(default="g", description="Unité de mesure (g, piece, etc.)")


class MealAnalysisRecalculateRequest(BaseModel):
    """Permet de recalculer les macros après ajustements par l'utilisateur."""

    items: List[UserCorrectionItem] = Field(..., min_length=1)
