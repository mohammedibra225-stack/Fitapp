"""
Service de synchronisation Open Food Facts.

Regle 15/16/18 :
    fetch -> parse -> validate -> normalize -> save/update
    minimise les appels externes, ne casse rien si l'API est indisponible.

Ce service NE remplace PAS les aliments generiques existants
(saisis manuellement, source=MANUAL) : il sert a importer/enrichir
des PRODUITS (avec code-barres) dans la meme table `foods`, en les
distinguant via `source=OPEN_FOOD_FACTS` (regle 13).

Halal (regle 3) : on ne deduit JAMAIS le statut halal a partir du nom
du produit. On regarde uniquement `labels_tags` fournis par Open Food
Facts. Si aucune information exploitable n'est presente -> UNKNOWN.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FoodDataSource, HalalStatus
from app.models.food import Food, FoodTranslation

OFF_BASE_URL = "https://world.openfoodfacts.org"
OFF_PRODUCT_URL = OFF_BASE_URL + "/api/v2/product/{barcode}.json"
OFF_SEARCH_URL = OFF_BASE_URL + "/cgi/search.pl"

# Champs demandes a l'API pour limiter la taille des reponses.
OFF_FIELDS = ",".join(
    [
        "code",
        "product_name",
        "product_name_fr",
        "brands",
        "categories_tags",
        "labels_tags",
        "ingredients_text",
        "image_url",
        "image_front_url",
        "quantity",
        "nutriments",
        "serving_size",
        "origins",
    ]
)

# Labels Open Food Facts qui indiquent explicitement un statut halal.
# On ne considere que des tags explicites, jamais une deduction par nom.
HALAL_LABEL_TAGS = {"en:halal", "en:halal-france", "fr:halal"}
NOT_HALAL_LABEL_TAGS = {"en:contains-alcohol", "en:non-halal", "en:not-halal"}


class OpenFoodFactsUnavailable(Exception):
    """Leve quand l'API Open Food Facts est injoignable ou en erreur."""


# ============================================================
# FETCH
# ============================================================

def fetch_product_by_barcode(barcode: str) -> Optional[dict[str, Any]]:
    """Recupere un produit par code-barres. Renvoie None si absent (status=0),
    leve OpenFoodFactsUnavailable si l'API est injoignable."""

    try:
        response = httpx.get(
            OFF_PRODUCT_URL.format(barcode=barcode),
            params={"fields": OFF_FIELDS},
            timeout=10,
            headers={"User-Agent": "Fitapp/1.0 - contact via app"},
        )
    except httpx.RequestError as exc:
        raise OpenFoodFactsUnavailable(
            "Open Food Facts est momentanement inaccessible."
        ) from exc

    if response.status_code >= 500:
        raise OpenFoodFactsUnavailable(
            f"Open Food Facts a repondu avec une erreur serveur ({response.status_code})."
        )
    if response.status_code >= 400:
        # 404 et autres 4xx : on considere que le produit n'existe pas,
        # ce n'est pas une panne du service externe.
        return None

    payload = response.json()
    if payload.get("status") != 1:
        return None

    return payload.get("product")


def search_products(
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Recherche des produits par nom. Renvoie une liste (vide si rien
    trouve ou si l'API est indisponible - une recherche qui echoue ne
    doit pas casser le reste de l'application)."""

    try:
        response = httpx.get(
            OFF_SEARCH_URL,
            params={
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page": page,
                "page_size": page_size,
                "fields": OFF_FIELDS,
            },
            timeout=10,
            headers={"User-Agent": "Fitapp/1.0 - contact via app"},
        )
    except httpx.RequestError:
        return []

    if response.status_code >= 400:
        return []

    payload = response.json()
    return payload.get("products", []) or []


# ============================================================
# HALAL
# ============================================================

def determine_halal_status(raw_product: dict[str, Any]) -> HalalStatus:
    labels_tags = set(raw_product.get("labels_tags") or [])

    if labels_tags & HALAL_LABEL_TAGS:
        return HalalStatus.HALAL
    if labels_tags & NOT_HALAL_LABEL_TAGS:
        return HalalStatus.NOT_HALAL
    return HalalStatus.UNKNOWN


# ============================================================
# NORMALISATION
# ============================================================

def _slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90] or "produit"


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def parse_off_product(raw_product: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Transforme un produit brut Open Food Facts en dict normalise,
    pret a etre valide/sauvegarde. Renvoie None si le produit n'a pas
    assez d'informations nutritionnelles exploitables."""

    nutriments = raw_product.get("nutriments") or {}

    calories_kcal = _to_float(nutriments.get("energy-kcal_100g"))
    if calories_kcal is None:
        # Certains produits ne donnent l'energie qu'en kJ.
        energy_kj = _to_float(nutriments.get("energy_100g"))
        calories_kcal = round(energy_kj / 4.184, 2) if energy_kj is not None else None

    protein_g = _to_float(nutriments.get("proteins_100g")) or 0.0
    carbs_g = _to_float(nutriments.get("carbohydrates_100g")) or 0.0
    fat_g = _to_float(nutriments.get("fat_100g")) or 0.0

    if calories_kcal is None:
        # Sans calories, l'aliment est inutilisable pour les calculs
        # nutritionnels du reste de l'app (regle : ne pas mettre 0 arbitraire).
        return None

    barcode = (raw_product.get("code") or "").strip() or None
    name = (
        raw_product.get("product_name_fr")
        or raw_product.get("product_name")
        or None
    )
    if not name:
        return None

    return {
        "barcode": barcode,
        "source_id": barcode,
        "name": name.strip(),
        "brand": (raw_product.get("brands") or "").split(",")[0].strip() or None,
        "image_url": raw_product.get("image_front_url") or raw_product.get("image_url") or None,
        "category": (raw_product.get("categories_tags") or [None])[0],
        "halal_status": determine_halal_status(raw_product),
        "calories_kcal": calories_kcal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "fiber_g": _to_float(nutriments.get("fiber_100g")),
        "sugar_g": _to_float(nutriments.get("sugars_100g")),
        "sodium_mg": (
            round(_to_float(nutriments.get("sodium_100g")) * 1000, 2)
            if _to_float(nutriments.get("sodium_100g")) is not None
            else None
        ),
        "saturated_fat_g": _to_float(nutriments.get("saturated-fat_100g")),
    }


# ============================================================
# SAVE / UPDATE (upsert, sans doublons)
# ============================================================

def upsert_food_from_off(
    db: Session,
    raw_product: dict[str, Any],
    language: str = "fr",
) -> Optional[Food]:
    """Cree ou met a jour un Food a partir d'un produit Open Food Facts brut.
    Deduplique par barcode (regle 18). Ne fait pas le commit final :
    a l'appelant de commit, comme le reste du projet."""

    normalized = parse_off_product(raw_product)
    if normalized is None:
        return None

    barcode = normalized["barcode"]

    food: Optional[Food] = None
    if barcode:
        food = db.execute(
            select(Food).where(Food.barcode == barcode)
        ).scalar_one_or_none()

    if food is None:
        slug_base = _slugify(normalized["name"])
        slug = slug_base
        suffix = 1
        while db.execute(select(Food).where(Food.slug == slug)).scalar_one_or_none():
            suffix += 1
            slug = f"{slug_base}-{suffix}"

        food = Food(
            slug=slug,
            source=FoodDataSource.OPEN_FOOD_FACTS,
            default_unit="g",
        )
        db.add(food)

    food.brand = normalized["brand"]
    food.image_url = normalized["image_url"]
    food.category = normalized["category"]
    food.halal_status = normalized["halal_status"]
    food.source = FoodDataSource.OPEN_FOOD_FACTS
    food.source_id = normalized["source_id"]
    food.barcode = barcode
    food.calories_kcal = normalized["calories_kcal"]
    food.protein_g = normalized["protein_g"]
    food.carbs_g = normalized["carbs_g"]
    food.fat_g = normalized["fat_g"]
    food.fiber_g = normalized["fiber_g"]
    food.sugar_g = normalized["sugar_g"]
    food.sodium_mg = normalized["sodium_mg"]
    food.saturated_fat_g = normalized["saturated_fat_g"]
    food.last_synced_at = datetime.now(timezone.utc)

    db.flush()  # pour obtenir food.id si nouvellement cree

    translation = next(
        (t for t in food.translations if t.language_code == language),
        None,
    )
    if translation is None:
        translation = FoodTranslation(
            food_id=food.id,
            language_code=language,
            name=normalized["name"],
        )
        db.add(translation)
    else:
        translation.name = normalized["name"]

    return food


def sync_product_by_barcode(
    db: Session,
    barcode: str,
    language: str = "fr",
) -> Optional[Food]:
    """Point d'entree pratique : recupere + upsert un produit par code-barres.
    Renvoie None si le produit n'existe pas sur OFF ou si les donnees sont
    insuffisantes. Leve OpenFoodFactsUnavailable si l'API est en panne
    (a l'appelant de decider de retomber sur la base locale)."""

    raw_product = fetch_product_by_barcode(barcode)
    if raw_product is None:
        return None
    return upsert_food_from_off(db, raw_product, language=language)
