from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.models.enums import MealType, MeasurementUnit
from app.models.food import Food
from app.models.meal import Meal, MealItem
from app.models.profile import Profile
from app.models.user import User
from app.services.meal_calculator import calculate_food_nutrition
from app.services.nutrition import calculate_calories

router = APIRouter(prefix="/nutrition-tracking", tags=["nutrition-tracking"])


class TrackedMealItemCreate(BaseModel):
    food_slug: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1)


class TrackedMealCreate(BaseModel):
    meal_type: MealType
    consumed_on: date | None = None
    consumed_at: datetime | None = None
    name: str | None = Field(default=None, max_length=150)
    # Optional direct nutrition values (e.g. for a recommended recipe from the plan)
    calories_kcal: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carbs_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    # items only required if no direct nutrition values were provided
    items: list[TrackedMealItemCreate] = Field(default_factory=list)


class TrackedMealItemOut(BaseModel):
    food_slug: str
    quantity: float
    unit: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class TrackedMealOut(BaseModel):
    id: UUID
    user_id: UUID
    meal_type: MealType
    consumed_on: date
    consumed_at: datetime | None
    name: str | None
    total_calories_kcal: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    items: list[TrackedMealItemOut]

    model_config = {"from_attributes": True}


@router.post("/meals/{user_id}", response_model=TrackedMealOut, status_code=201)
def create_tracked_meal(
    user_id: UUID,
    payload: TrackedMealCreate,
    db: Session = Depends(get_db),
):
    ensure_user_exists(user_id, db)
    consumed_at = payload.consumed_at or datetime.now(timezone.utc)
    consumed_on = payload.consumed_on or consumed_at.date()
    meal = Meal(
        user_id=user_id,
        meal_type=payload.meal_type,
        consumed_on=consumed_on,
        consumed_at=consumed_at,
        name=payload.name,
    )
    totals = {key: Decimal("0") for key in ("calories_kcal", "protein_g", "carbs_g", "fat_g")}
    output_items = []

    has_direct_nutrition = any(
        getattr(payload, key) is not None
        for key in ("calories_kcal", "protein_g", "carbs_g", "fat_g")
    )

    if not payload.items and not has_direct_nutrition:
        raise HTTPException(status_code=400, detail="Aucun aliment ou valeur nutritionnelle fournie.")

    if has_direct_nutrition:
        # Nutrition values already computed (e.g. recommended recipe) — stored as-is.
        for key in totals:
            totals[key] = Decimal(str(getattr(payload, key) or 0))
        output_items.append(
            TrackedMealItemOut(
                food_slug=payload.name or payload.meal_type.value,
                quantity=1,
                unit="serving",
                calories_kcal=float(totals["calories_kcal"]),
                protein_g=float(totals["protein_g"]),
                carbs_g=float(totals["carbs_g"]),
                fat_g=float(totals["fat_g"]),
            )
        )

    for item in payload.items:
        food = db.execute(select(Food).where(Food.slug == item.food_slug)).scalar_one_or_none()
        if food is None:
            raise HTTPException(status_code=404, detail=f"Aliment introuvable : {item.food_slug}")
        try:
            measurement_unit = MeasurementUnit(item.unit.strip().lower())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Unité non supportée : {item.unit}") from exc
        try:
            calculated = calculate_food_nutrition(food, item.quantity, measurement_unit.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        meal.items.append(
            MealItem(
                food_id=food.id,
                quantity=item.quantity,
                unit=measurement_unit,
                calories_kcal=calculated["calories_kcal"],
                protein_g=calculated["protein_g"],
                carbs_g=calculated["carbs_g"],
                fat_g=calculated["fat_g"],
            )
        )
        for key in totals:
            totals[key] += calculated[key]
        output_items.append(
            TrackedMealItemOut(
                food_slug=food.slug,
                quantity=float(item.quantity),
                unit=measurement_unit.value,
                calories_kcal=float(calculated["calories_kcal"]),
                protein_g=float(calculated["protein_g"]),
                carbs_g=float(calculated["carbs_g"]),
                fat_g=float(calculated["fat_g"]),
            )
        )

    meal.total_calories_kcal = totals["calories_kcal"]
    meal.total_protein_g = totals["protein_g"]
    meal.total_carbs_g = totals["carbs_g"]
    meal.total_fat_g = totals["fat_g"]
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return {
        **{field: getattr(meal, field) for field in (
            "id", "user_id", "meal_type", "consumed_on", "consumed_at", "name",
        )},
        "total_calories_kcal": float(meal.total_calories_kcal),
        "total_protein_g": float(meal.total_protein_g),
        "total_carbs_g": float(meal.total_carbs_g),
        "total_fat_g": float(meal.total_fat_g),
        "items": output_items,
    }


@router.get("/meals/{user_id}", response_model=list[TrackedMealOut])
def list_tracked_meals(
    user_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    ensure_user_exists(user_id, db)
    query = (
        select(Meal)
        .options(selectinload(Meal.items).selectinload(MealItem.food))
        .where(Meal.user_id == user_id)
    )
    if start_date:
        query = query.where(Meal.consumed_on >= start_date)
    if end_date:
        query = query.where(Meal.consumed_on <= end_date)
    meals = db.execute(query.order_by(Meal.consumed_on.desc(), Meal.consumed_at.desc())).scalars().all()
    return [meal_to_response(meal) for meal in meals]


@router.get("/daily/{user_id}")
def get_daily_summary(
    user_id: UUID,
    tracked_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    ensure_user_exists(user_id, db)
    summary_date = tracked_date or date.today()
    totals = db.execute(
        select(
            func.coalesce(func.sum(Meal.total_calories_kcal), 0),
            func.coalesce(func.sum(Meal.total_protein_g), 0),
            func.coalesce(func.sum(Meal.total_carbs_g), 0),
            func.coalesce(func.sum(Meal.total_fat_g), 0),
        ).where(Meal.user_id == user_id, Meal.consumed_on == summary_date)
    ).one()
    result = {
        "user_id": str(user_id),
        "date": summary_date.isoformat(),
        "consumed": {
            "calories_kcal": float(totals[0]),
            "protein_g": float(totals[1]),
            "carbs_g": float(totals[2]),
            "fat_g": float(totals[3]),
        },
    }
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    if profile and all(getattr(profile, field) is not None for field in (
        "age", "sex", "height_cm", "current_weight_kg", "activity_level", "primary_goal",
    )):
        targets = calculate_calories(
            weight_kg=float(profile.current_weight_kg),
            height_cm=float(profile.height_cm),
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.primary_goal,
        )
        result["targets"] = targets
    return result


def meal_to_response(meal: Meal) -> dict:
    return {
        "id": meal.id,
        "user_id": meal.user_id,
        "meal_type": meal.meal_type,
        "consumed_on": meal.consumed_on,
        "consumed_at": meal.consumed_at,
        "name": meal.name,
        "total_calories_kcal": float(meal.total_calories_kcal),
        "total_protein_g": float(meal.total_protein_g),
        "total_carbs_g": float(meal.total_carbs_g),
        "total_fat_g": float(meal.total_fat_g),
        "items": [
            {
                "food_slug": item.food.slug,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "calories_kcal": float(item.calories_kcal),
                "protein_g": float(item.protein_g),
                "carbs_g": float(item.carbs_g),
                "fat_g": float(item.fat_g),
            }
            for item in meal.items
        ],
    }


def ensure_user_exists(user_id: UUID, db: Session) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")