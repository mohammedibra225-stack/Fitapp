"""
Service de synchronisation Open Prices.

Regle 4/15/16/18 :
    fetch -> parse -> validate -> normalize -> save/update
    minimise les appels externes, ne casse rien si l'API est indisponible.

Ce service alimente la table `food_prices` deja existante (utilisee par
app.services.food_price pour le calcul de cout), en marquant les lignes
importees avec `source=OPEN_PRICES` (regle 5 : notre PostgreSQL reste la
source principale, Open Prices ne fait qu'enrichir/synchroniser).

Important (regle 4) :
    Open Prices a une couverture incomplete, notamment pour l'Algerie.
    Ce service ne DOIT JAMAIS inventer un prix a 0. Si rien n'est
    disponible, les fonctions renvoient une liste/valeur vide et
    l'appelant doit traiter cela comme "prix inconnu", pas comme "gratuit".
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FoodDataSource
from app.models.food import Food, FoodPrice

OP_BASE_URL = "https://prices.openfoodfacts.org/api/v1"
OP_PRICES_URL = OP_BASE_URL + "/prices"

# price_per renvoye par Open Prices : soit au kilo, soit a la piece.
# On normalise vers nos unites internes (regle : reutiliser food_price.py).
PRICE_PER_TO_UNIT = {
    "KILOGRAM": "kg",
    "UNIT": "piece",
}


class OpenPricesUnavailable(Exception):
    """Leve quand l'API Open Prices est injoignable ou en erreur serveur."""


# ============================================================
# FETCH
# ============================================================

def fetch_prices_by_barcode(
    barcode: str,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Recupere les derniers prix connus pour un code-barres.

    Renvoie une liste vide si aucun prix n'existe (couverture incomplete,
    regle 4) ou si le code-barres est invalide (400/404 : pas une panne).
    Leve OpenPricesUnavailable uniquement pour les vraies pannes reseau
    ou erreurs serveur, pour laisser l'appelant retomber sur PostgreSQL.
    """

    try:
        response = httpx.get(
            OP_PRICES_URL,
            params={
                "product_code": barcode,
                "order_by": "-date",
                "page_size": page_size,
            },
            timeout=10,
            headers={"User-Agent": "Fitapp/1.0 - contact via app"},
        )
    except httpx.RequestError as exc:
        raise OpenPricesUnavailable(
            "Open Prices est momentanement inaccessible."
        ) from exc

    if response.status_code >= 500:
        raise OpenPricesUnavailable(
            f"Open Prices a repondu avec une erreur serveur ({response.status_code})."
        )
    if response.status_code >= 400:
        return []

    payload = response.json()
    return payload.get("items", []) or []


# ============================================================
# NORMALISATION
# ============================================================

def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _parse_date(raw_date: Any) -> Optional[date]:
    if not raw_date:
        return None
    try:
        return datetime.fromisoformat(str(raw_date)[:10]).date()
    except ValueError:
        return None


def parse_op_price(raw_item: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Transforme un prix brut Open Prices en dict normalise.

    Renvoie None si le prix n'a pas assez d'informations exploitables
    (pas de valeur de prix, ou unite non convertible) : mieux vaut
    ignorer une ligne incomplete que d'enregistrer un prix douteux.
    """

    price_value = _to_float(raw_item.get("price"))
    if price_value is None or price_value < 0:
        return None

    unit = PRICE_PER_TO_UNIT.get((raw_item.get("price_per") or "").upper())
    if unit is None:
        # Pas de quantite exploitable (regle : ne pas deviner une unite).
        return None

    location = raw_item.get("location") or {}
    store_name = (
        location.get("osm_name")
        or location.get("name")
        or raw_item.get("location_osm_id")
    )
    location_label = ", ".join(
        part
        for part in [
            location.get("osm_address_city"),
            location.get("osm_address_country"),
        ]
        if part
    ) or None

    return {
        "source_id": str(raw_item.get("id")) if raw_item.get("id") is not None else None,
        "price": price_value,
        "quantity": 1.0,
        "unit": unit,
        "currency": (raw_item.get("currency") or "").strip() or None,
        "valid_from": _parse_date(raw_item.get("date")),
        "store_name": str(store_name) if store_name else None,
        "location": location_label,
    }


# ============================================================
# SAVE / UPDATE (upsert, sans doublons)
# ============================================================

def upsert_prices_for_food(
    db: Session,
    food: Food,
    raw_items: list[dict[str, Any]],
) -> list[FoodPrice]:
    """Cree ou met a jour les FoodPrice d'un aliment a partir de prix
    Open Prices bruts. Deduplique par source_id (regle 18) : un meme
    prix Open Prices ne cree jamais deux lignes. Ne fait pas le commit
    final : a l'appelant de commit, comme le reste du projet."""

    existing_by_source_id: dict[str, FoodPrice] = {
        fp.source_id: fp
        for fp in food.prices
        if fp.source == FoodDataSource.OPEN_PRICES and fp.source_id
    }

    saved: list[FoodPrice] = []

    for raw_item in raw_items:
        normalized = parse_op_price(raw_item)
        if normalized is None or normalized["currency"] is None:
            # Sans devise fiable, on prefere ignorer la ligne plutot que
            # de supposer DZD par defaut (regle 4/11 : pas d'invention).
            continue

        source_id = normalized["source_id"]
        food_price = existing_by_source_id.get(source_id) if source_id else None

        if food_price is None:
            food_price = FoodPrice(
                food_id=food.id,
                source=FoodDataSource.OPEN_PRICES,
                source_id=source_id,
            )
            db.add(food_price)
            food.prices.append(food_price)

        food_price.price_da = normalized["price"]
        food_price.quantity = normalized["quantity"]
        food_price.unit = normalized["unit"]
        food_price.currency = normalized["currency"]
        food_price.valid_from = normalized["valid_from"]
        food_price.store_name = normalized["store_name"]
        food_price.location = normalized["location"]
        food_price.is_active = True

        saved.append(food_price)

    return saved


def sync_prices_by_barcode(
    db: Session,
    barcode: str,
) -> list[FoodPrice]:
    """Point d'entree pratique : recupere + upsert les prix d'un aliment
    deja present en base (identifie par son barcode). Renvoie une liste
    vide si l'aliment est inconnu chez nous ou si aucun prix Open Prices
    n'est disponible (regle 4 : jamais de plantage, jamais de 0 invente).
    Leve OpenPricesUnavailable si l'API est en panne (a l'appelant de
    decider de retomber sur les prix locaux existants)."""

    food = db.execute(select(Food).where(Food.barcode == barcode)).scalar_one_or_none()
    if food is None:
        return []

    raw_items = fetch_prices_by_barcode(barcode)
    if not raw_items:
        return []

    return upsert_prices_for_food(db, food, raw_items)


# ============================================================
# LECTURE : dernier prix connu (local d'abord, regle 5/16)
# ============================================================

def get_latest_known_price(food: Food) -> Optional[FoodPrice]:
    """Renvoie le prix le plus recent connu pour un aliment (toutes
    sources confondues, actif uniquement), ou None si aucun prix
    n'est disponible. Ne renvoie jamais un prix a 0 par defaut :
    l'appelant doit afficher "prix inconnu" quand ceci renvoie None."""

    active_prices = [fp for fp in food.prices if fp.is_active]
    if not active_prices:
        return None

    return max(
        active_prices,
        key=lambda fp: fp.valid_from or date.min,
    )
