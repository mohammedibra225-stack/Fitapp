"""
Inventaire alimentaire de l'utilisateur (frigo / congelateur / placard).

Les modeles Inventory et InventoryItem existent deja
(app/models/inventory.py, deja en base via la migration initiale).
Ce fichier ajoute les routes qui manquaient encore :

    POST   /inventory/{user_id}/items          -> ajouter un aliment au stock
    GET    /inventory/{user_id}                -> lister le stock (par type ou tout)
    GET    /inventory/{user_id}/expiring        -> aliments bientot perimes
    PATCH  /inventory/items/{item_id}           -> modifier quantite / date peremption
    DELETE /inventory/items/{item_id}           -> retirer un aliment du stock

Un "contenant" (Inventory : frigo/congelateur/placard) est cree
automatiquement au premier ajout, sur le meme principe que
_get_or_create_sport dans app/routes/onboarding.py.
"""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import InventoryType, MeasurementUnit
from app.models.food import Food, FoodTranslation
from app.models.inventory import Inventory, InventoryItem
from app.models.user import User

router = APIRouter(prefix="/inventory", tags=["inventory"])


# ============================================================
# SCHEMAS
# ============================================================

class InventoryItemCreate(BaseModel):
    inventory_type: InventoryType
    food_slug: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: MeasurementUnit
    expires_on: date | None = None


class InventoryItemUpdate(BaseModel):
    quantity: float | None = Field(None, gt=0)
    expires_on: date | None = None


# ============================================================
# HELPERS
# ============================================================

def _get_or_create_inventory(
    db: Session,
    user_id: UUID,
    inventory_type: InventoryType,
) -> Inventory:
    """Recupere le contenant (frigo/congelo/placard) de l'utilisateur, ou le cree."""

    inventory = db.execute(
        select(Inventory).where(
            Inventory.user_id == user_id,
            Inventory.inventory_type == inventory_type,
        )
    ).scalar_one_or_none()

    if inventory is not None:
        return inventory

    inventory = Inventory(user_id=user_id, inventory_type=inventory_type)
    db.add(inventory)
    db.flush()  # attribue l'id avant de creer les items lies

    return inventory


def _serialize_item(item: InventoryItem, language: str) -> dict:
    translation = next(
        (t for t in item.food.translations if t.language_code == language),
        None,
    )

    today = date.today()
    is_expired = item.expires_on is not None and item.expires_on < today
    is_expiring_soon = (
        item.expires_on is not None
        and not is_expired
        and item.expires_on <= today + timedelta(days=3)
    )

    return {
        "id": str(item.id),
        "food_slug": item.food.slug,
        "food_name": translation.name if translation else item.food.slug,
        "quantity": float(item.quantity),
        "unit": item.unit.value,
        "added_on": item.added_on.isoformat(),
        "expires_on": item.expires_on.isoformat() if item.expires_on else None,
        "is_expired": is_expired,
        "is_expiring_soon": is_expiring_soon,
    }


# ============================================================
# AJOUTER UN ALIMENT AU STOCK
# ============================================================

@router.post("/{user_id}/items", status_code=201)
def add_inventory_item(
    user_id: UUID,
    payload: InventoryItemCreate,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    food = db.execute(
        select(Food).where(Food.slug == payload.food_slug)
    ).scalar_one_or_none()
    if food is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aliment introuvable : {payload.food_slug}",
        )

    inventory = _get_or_create_inventory(db, user_id, payload.inventory_type)

    item = InventoryItem(
        inventory_id=inventory.id,
        food_id=food.id,
        quantity=payload.quantity,
        unit=payload.unit,
        added_on=date.today(),
        expires_on=payload.expires_on,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return _serialize_item(item, language)


# ============================================================
# LISTER LE STOCK
# ============================================================

@router.get("/{user_id}")
def list_inventory(
    user_id: UUID,
    inventory_type: InventoryType | None = Query(
        None, description="Filtrer par type : fridge, freezer, pantry"
    ),
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    query = select(Inventory).where(Inventory.user_id == user_id)
    if inventory_type is not None:
        query = query.where(Inventory.inventory_type == inventory_type)

    inventories = db.execute(query).scalars().all()

    return {
        "user_id": str(user_id),
        "inventories": [
            {
                "inventory_type": inventory.inventory_type.value,
                "name": inventory.name,
                "items": [
                    _serialize_item(item, language) for item in inventory.items
                ],
            }
            for inventory in inventories
        ],
    }


# ============================================================
# ALIMENTS BIENTOT PERIMES
# ============================================================

@router.get("/{user_id}/expiring")
def list_expiring_items(
    user_id: UUID,
    days: int = Query(3, ge=0, le=30),
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    limit_date = date.today() + timedelta(days=days)

    items = db.execute(
        select(InventoryItem)
        .join(Inventory, Inventory.id == InventoryItem.inventory_id)
        .where(
            Inventory.user_id == user_id,
            InventoryItem.expires_on.is_not(None),
            InventoryItem.expires_on <= limit_date,
        )
        .order_by(InventoryItem.expires_on.asc())
    ).scalars().all()

    return {
        "user_id": str(user_id),
        "within_days": days,
        "items": [_serialize_item(item, language) for item in items],
    }


# ============================================================
# MODIFIER UN ALIMENT DU STOCK
# ============================================================

@router.patch("/items/{item_id}")
def update_inventory_item(
    item_id: UUID,
    payload: InventoryItemUpdate,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Aliment introuvable dans le stock.")

    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.expires_on is not None:
        item.expires_on = payload.expires_on

    db.commit()
    db.refresh(item)

    return _serialize_item(item, language)


# ============================================================
# RETIRER UN ALIMENT DU STOCK
# ============================================================

@router.delete("/items/{item_id}", status_code=204)
def delete_inventory_item(item_id: UUID, db: Session = Depends(get_db)):
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Aliment introuvable dans le stock.")

    db.delete(item)
    db.commit()

    return None
