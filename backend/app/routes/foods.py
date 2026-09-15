from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.food import Food, FoodTranslation
from app.services import open_prices
from app.services.food_price import calculate_unit_price
from app.services.open_prices import OpenPricesUnavailable


router = APIRouter(
    prefix="/foods",
    tags=["Foods"],
)


@router.get("")
def get_foods(
    search: Optional[str] = Query(
        None,
        description="Recherche par nom ou slug",
    ),
    language: str = Query(
        "fr",
        min_length=2,
        max_length=5,
        description="Code langue : fr, en, es, ar",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Food)
        .outerjoin(
            FoodTranslation,
            (FoodTranslation.food_id == Food.id)
            & (FoodTranslation.language_code == language),
        )
    )

    if search:
        search_pattern = f"%{search}%"

        query = query.filter(
            (Food.slug.ilike(search_pattern))
            | (FoodTranslation.name.ilike(search_pattern))
        )

    total = query.count()

    foods = (
        query
        .order_by(Food.slug)
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []

    for food in foods:
        translation = next(
            (
                t
                for t in food.translations
                if t.language_code == language
            ),
            None,
        )

        items.append(
            {
                "id": str(food.id),
                "slug": food.slug,
                "name": translation.name if translation else food.slug,
                "is_liquid": food.is_liquid,
                "calories_kcal": float(food.calories_kcal),
                "protein_g": float(food.protein_g),
                "carbs_g": float(food.carbs_g),
                "fat_g": float(food.fat_g),
                "fiber_g": (
                    float(food.fiber_g)
                    if food.fiber_g is not None
                    else None
                ),
                "sugar_g": (
                    float(food.sugar_g)
                    if food.sugar_g is not None
                    else None
                ),
                "sodium_mg": (
                    float(food.sodium_mg)
                    if food.sodium_mg is not None
                    else None
                ),
                "saturated_fat_g": (
                    float(food.saturated_fat_g)
                    if food.saturated_fat_g is not None
                    else None
                ),
                "category": food.category,
                "default_unit": food.default_unit,
                "unit_weight_g": (
                    float(food.unit_weight_g)
                    if food.unit_weight_g is not None
                    else None
                ),
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "language": language,
        "items": items,
    }


@router.get("/{food_id}")
def get_food(
    food_id: str,
    language: str = Query(
        "fr",
        min_length=2,
        max_length=5,
        description="Code langue : fr, en, es, ar",
    ),
    db: Session = Depends(get_db),
):
    food = (
        db.query(Food)
        .filter(Food.id == food_id)
        .first()
    )

    if not food:
        return {
            "error": "Food not found"
        }

    translation = next(
        (
            t
            for t in food.translations
            if t.language_code == language
        ),
        None,
    )

    return {
        "id": str(food.id),
        "slug": food.slug,
        "name": translation.name if translation else food.slug,
        "is_liquid": food.is_liquid,
        "calories_kcal": float(food.calories_kcal),
        "protein_g": float(food.protein_g),
        "carbs_g": float(food.carbs_g),
        "fat_g": float(food.fat_g),
        "fiber_g": (
            float(food.fiber_g)
            if food.fiber_g is not None
            else None
        ),
        "sugar_g": (
            float(food.sugar_g)
            if food.sugar_g is not None
            else None
        ),
        "sodium_mg": (
            float(food.sodium_mg)
            if food.sodium_mg is not None
            else None
        ),
        "saturated_fat_g": (
            float(food.saturated_fat_g)
            if food.saturated_fat_g is not None
            else None
        ),
        "category": food.category,
        "default_unit": food.default_unit,
        "unit_weight_g": (
            float(food.unit_weight_g)
            if food.unit_weight_g is not None
            else None
        ),
    }


# ============================================================
# PRIX D'UN ALIMENT (Open Prices, regle 4/14)
# ============================================================

def _serialize_food_price(price) -> dict:
    return {
        "id": str(price.id),
        "price": float(price.price_da),
        "currency": price.currency,
        "quantity": float(price.quantity),
        "unit": price.unit,
        "valid_from": price.valid_from.isoformat() if price.valid_from else None,
        "store_name": price.store_name,
        "location": price.location,
        "source": price.source.value,
    }


@router.get("/{food_id}/prices")
def get_food_prices(
    food_id: str,
    sync: bool = Query(
        False,
        description="Forcer une resynchronisation avec Open Prices avant de repondre",
    ),
    db: Session = Depends(get_db),
):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Aliment introuvable.")

    # Regle 16 : on ne va chercher Open Prices que si on force la sync,
    # ou si on n'a strictement aucun prix local pour cet aliment.
    should_sync = food.barcode and (sync or not food.prices)
    sync_error: Optional[str] = None

    if should_sync:
        try:
            open_prices.sync_prices_by_barcode(db, food.barcode)
            db.commit()
            db.refresh(food)
        except OpenPricesUnavailable:
            # Regle 4/20 : Open Prices indisponible -> on continue avec
            # les prix locaux existants, on ne casse jamais la reponse.
            db.rollback()
            sync_error = "Open Prices est momentanement indisponible ; prix locaux affiches."

    latest_price = open_prices.get_latest_known_price(food)

    unit_price = None
    if latest_price is not None:
        try:
            unit_price = float(calculate_unit_price(latest_price))
        except (ValueError, ZeroDivisionError):
            unit_price = None

    return {
        "food_id": str(food.id),
        "food_slug": food.slug,
        "currency": latest_price.currency if latest_price else None,
        "latest_price": _serialize_food_price(latest_price) if latest_price else None,
        "unit_price": unit_price,
        "prices": [
            _serialize_food_price(p) for p in food.prices if p.is_active
        ],
        "sync_warning": sync_error,
    }