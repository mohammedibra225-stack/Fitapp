"""
Routes pour l'analyse IA de repas (AI Meal Analysis).

Fournisseur de vision : Hugging Face ZeroGPU
(modele multimodal Qwen2.5-VL-3B-Instruct).

Le modele ne fait QUE :
- identification visuelle des aliments
- estimation des portions
- estimation de la préparation
- score de confiance

Les macros sont calculees par le Food Matching Service et le Meal Calculator
existants de Fitapp.

Architecture :
- POST /api/v1/meal-analysis/analyze
    image -> Hugging Face -> matching Food -> macros

- POST /api/v1/meal-analysis/recalculate
    recalcul apres corrections utilisateur

- GET /api/v1/meal-analysis/quota/{id}
    quota quotidien restant

- GET /api/v1/meal-analysis/health
    diagnostic Hugging Face ZeroGPU
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config_ai import (
    ALLOWED_IMAGE_MIME_TYPES,
    MAX_IMAGE_SIZE_BYTES,
    MAX_MEAL_ANALYSES_PER_DAY,
)
from app.database.connection import get_db
from app.models.ai import MealPhotoAnalysis, MealPhotoAnalysisItem
from app.models.enums import AnalysisStatus
from app.models.food import Food
from app.models.user import User
from app.schemas.meal_analysis import (
    MealAnalysisRecalculateRequest,
    MealAnalysisResponse,
)
from app.services.food_matching_service import (
    get_translated_food_name,
    match_and_calculate_meal_items,
)
from app.services.image_preprocessing import (
    ImagePreprocessingError,
    normalize_meal_image,
)
from app.services.meal_calculator import calculate_food_nutrition

from app.services.huggingface_vision_service import (
    HuggingFaceVisionError,
    HuggingFaceUnavailableError,
    HuggingFaceTimeoutError,
    HuggingFaceInvalidResponseError,
    huggingface_vision_service,
)

logger = logging.getLogger("fitapp.meal_analysis_route")

router = APIRouter(
    prefix="/meal-analysis",
    tags=["Meal Analysis (AI)"],
)


def _count_analyses_today(db: Session, user_id: UUID) -> int:
    """Nombre d'analyses de repas deja effectuees aujourd'hui (UTC)."""

    today_start = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    return (
        db.query(func.count(MealPhotoAnalysis.id))
        .filter(
            MealPhotoAnalysis.user_id == user_id,
            MealPhotoAnalysis.created_at >= today_start,
        )
        .scalar()
        or 0
    )


@router.get(
    "/health",
    summary="Diagnostic du service de vision Hugging Face",
    description="Indique si le service Hugging Face ZeroGPU est correctement configure.",
)
def meal_analysis_health():
    """
    Health check du fournisseur de vision.

    Ce endpoint ne lance pas une inference GPU.
    Il retourne simplement les informations de configuration
    du service Hugging Face.
    """

    return huggingface_vision_service.health()


@router.get(
    "/quota/{user_id}",
    summary="Quota quotidien d'analyses de repas restant pour un utilisateur",
)
def get_meal_analysis_quota(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    used = _count_analyses_today(db, user_id)

    return {
        "limit": MAX_MEAL_ANALYSES_PER_DAY,
        "used": used,
        "remaining": max(0, MAX_MEAL_ANALYSES_PER_DAY - used),
    }


@router.post(
    "/analyze",
    response_model=MealAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyser une photo de repas avec Hugging Face Vision AI",
    description=(
        "Identifie les aliments avec Qwen2.5-VL, estime les portions, "
        "effectue le matching avec la base Food et calcule les macros."
    ),
)
async def analyze_meal_photo(
    image: UploadFile = File(
        ...,
        description="Fichier image du repas",
    ),
    user_id: UUID = Form(
        ...,
        description="ID de l'utilisateur",
    ),
    language: str = Form(
        "fr",
        description="Langue demandee pour les libelles (fr, en, ar, es)",
    ),
    db: Session = Depends(get_db),
):
    # ============================================================
    # 0. UTILISATEUR + QUOTA
    # ============================================================

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    analyses_today = _count_analyses_today(
        db,
        user_id,
    )

    if analyses_today >= MAX_MEAL_ANALYSES_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Limite quotidienne atteinte "
                f"({MAX_MEAL_ANALYSES_PER_DAY} analyses de repas par jour). "
                "Réessaie demain."
            ),
        )

    # ============================================================
    # 1. VALIDATION DU TYPE MIME
    # ============================================================

    content_type = (
        image.content_type or ""
    ).lower()

    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Type de fichier non autorisé ({content_type}). "
                f"Formats acceptés: "
                f"{', '.join(ALLOWED_IMAGE_MIME_TYPES)}"
            ),
        )

    # ============================================================
    # 2. LECTURE + VALIDATION DE LA TAILLE
    # ============================================================

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier image fourni est vide.",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        max_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)

        raise HTTPException(
            status_code=413,
            detail=(
                f"Image trop volumineuse. "
                f"Taille maximum autorisée: {max_mb:.1f} Mo."
            ),
        )

    # ============================================================
    # 3. NORMALISATION DE L'IMAGE
    # ============================================================

    try:
        normalized_bytes, normalized_mime = normalize_meal_image(
            image_bytes,
            content_type,
        )

    except ImagePreprocessingError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except Exception as exc:
        logger.error(
            "Erreur inattendue pendant la preparation de l'image: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de lire cette image.",
        )

    # ============================================================
    # 4. HUGGING FACE VISION AI
    # ============================================================

    try:
        """
        Le client Gradio est synchrone.

        Comme cette route FastAPI est async, on execute l'inference
        dans un thread afin de ne pas bloquer la boucle evenementielle
        de FastAPI pendant que Hugging Face traite l'image.
        """

        raw_analysis = await asyncio.to_thread(
            huggingface_vision_service.analyze_meal,
            normalized_bytes,
            normalized_mime,
        )

    except HuggingFaceUnavailableError as exc:
        logger.error(
            "Hugging Face indisponible: %s",
            exc,
        )

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except HuggingFaceTimeoutError as exc:
        logger.error(
            "Timeout Hugging Face: %s",
            exc,
        )

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except HuggingFaceInvalidResponseError as exc:
        logger.error(
            "Réponse Hugging Face invalide: %s",
            exc,
        )

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except HuggingFaceVisionError as exc:
        logger.error(
            "Erreur Hugging Face Vision: %s",
            exc,
        )

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except Exception as exc:
        logger.exception(
            "Erreur inattendue pendant l'analyse Hugging Face: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Une erreur interne est survenue "
                "lors de l'analyse du repas."
            ),
        )

    # ============================================================
    # 5. MATCHING FOOD + CALCUL DES MACROS
    # ============================================================

    try:
        analysis_detail = match_and_calculate_meal_items(
            db=db,
            raw_analysis=raw_analysis,
            language=language,
        )

    except Exception as exc:
        logger.exception(
            "Erreur pendant le matching/calcul du repas: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "L'analyse visuelle a réussi, "
                "mais le calcul nutritionnel a échoué."
            ),
        )

    # ============================================================
    # 6. SAUVEGARDE EN BASE DE DONNEES
    # ============================================================

    try:
        db_analysis = MealPhotoAnalysis(
            user_id=user.id,
            status=AnalysisStatus.PROCESSED,
            raw_ai_response=raw_analysis.model_dump(),
        )

        db.add(db_analysis)
        db.flush()

        for item in analysis_detail.foods:
            db_item = MealPhotoAnalysisItem(
                analysis_id=db_analysis.id,
                detected_label=item.detected_name,
                matched_food_id=item.matched_food_id,
                estimated_portion=item.estimated_quantity,
                estimated_unit=item.estimated_unit,
                estimated_calories_kcal=item.calories_kcal,
                estimated_protein_g=item.protein_g,
                estimated_carbs_g=item.carbs_g,
                estimated_fat_g=item.fat_g,
            )

            db.add(db_item)

        db.commit()

        analysis_detail.analysis_id = db_analysis.id

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Erreur lors de la sauvegarde de l'analyse repas: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de sauvegarder l'analyse du repas.",
        )

    # ============================================================
    # 7. REPONSE
    # ============================================================

    return MealAnalysisResponse(
        success=True,
        analysis=analysis_detail,
    )


@router.post(
    "/recalculate",
    summary="Recalculer les macros d'aliments ajustés par l'utilisateur",
    description=(
        "Permet à l'utilisateur de modifier aliments et portions "
        "puis d'obtenir les macros calculées."
    ),
)
def recalculate_meal_analysis(
    request: MealAnalysisRecalculateRequest,
    language: str = "fr",
    db: Session = Depends(get_db),
):
    calculated_items = []

    total_cals = 0.0
    total_prot = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    total_fiber = 0.0

    for item in request.items:

        food = (
            db.query(Food)
            .filter(Food.slug == item.food_slug)
            .first()
        )

        if not food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Aliment avec le slug "
                    f"'{item.food_slug}' introuvable."
                ),
            )

        nutrition = calculate_food_nutrition(
            food=food,
            quantity=item.quantity,
            unit=item.unit,
        )

        cals = float(nutrition["calories_kcal"])
        prot = float(nutrition["protein_g"])
        carbs = float(nutrition["carbs_g"])
        fat = float(nutrition["fat_g"])
        fiber = float(nutrition["fiber_g"])

        total_cals += cals
        total_prot += prot
        total_carbs += carbs
        total_fat += fat
        total_fiber += fiber

        calculated_items.append(
            {
                "food_slug": food.slug,
                "food_name": get_translated_food_name(
                    food,
                    language,
                ),
                "quantity": item.quantity,
                "unit": item.unit,
                "grams": float(nutrition["grams"]),
                "calories_kcal": cals,
                "protein_g": prot,
                "carbs_g": carbs,
                "fat_g": fat,
                "fiber_g": fiber,
            }
        )

    return {
        "success": True,
        "items": calculated_items,
        "totals": {
            "calories": round(total_cals, 1),
            "protein_g": round(total_prot, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "fiber_g": round(total_fiber, 1),
        },
    }