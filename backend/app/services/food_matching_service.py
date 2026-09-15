from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from app.models.food import Food


# ============================================================
# ALIAS COURANTS
# ============================================================

COMMON_ALIASES = {
    "pommes de terre": "pomme de terre",
    "pommes de terre frites": "pomme de terre",
    "patates": "pomme de terre",
    "patate": "pomme de terre",

    "potatoes": "potato",
    "french fries": "potato",
    "fries": "potato",

    "patatas": "papa",

    "pommes": "pomme",
    "bananes": "banane",
    "oranges": "orange",
    "tomates": "tomate",
    "oeufs": "oeuf",
    "œufs": "oeuf",
}


# ============================================================
# MOTS DE PREPARATION
# ============================================================

PREPARATION_WORDS = {
    "cuit",
    "cuite",
    "cuits",
    "cuites",

    "frit",
    "frite",
    "frites",
    "frits",
    "friture",

    "grille",
    "grillee",
    "grillees",
    "grilles",

    "bouilli",
    "bouillie",
    "bouillis",
    "bouillies",

    "vapeur",

    "roti",
    "rotie",
    "rotis",
    "roties",

    "croustillant",
    "croustillante",
    "croustillants",
    "croustillantes",

    "cru",
    "crue",
    "crus",
    "crues",
}


# ============================================================
# NORMALISATION
# ============================================================

def normalize_text(value: str) -> str:
    """
    Normalise un texte pour faciliter la recherche :

    - minuscules
    - suppression des accents
    - remplacement des caractères spéciaux
    - espaces propres
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    # Suppression des accents
    value = unicodedata.normalize("NFD", value)
    value = "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )

    # Apostrophes / tirets -> espace
    value = re.sub(r"[-_/']", " ", value)

    # Garder lettres + chiffres + espaces
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    # Espaces multiples
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# CANONICALISATION
# ============================================================

def canonicalize_food_name(name: str) -> str:
    """
    Transforme un nom détecté par l'IA vers une forme canonique.
    """

    normalized = normalize_text(name)

    if not normalized:
        return ""

    # Alias exact
    if normalized in COMMON_ALIASES:
        return normalize_text(COMMON_ALIASES[normalized])

    # Alias après suppression des mots de préparation
    words = normalized.split()

    cleaned_words = [
        word
        for word in words
        if word not in PREPARATION_WORDS
    ]

    cleaned = " ".join(cleaned_words).strip()

    if cleaned in COMMON_ALIASES:
        return normalize_text(COMMON_ALIASES[cleaned])

    return cleaned


# ============================================================
# FOOD INDEX
# ============================================================

class FoodIndex:
    """
    Index des aliments disponibles dans la base Fitapp.

    Objectif :
    - éviter les faux matchs
    - gérer les pluriels simples
    - gérer les accents
    - gérer les mots de préparation
    - gérer quelques alias courants
    """

    def __init__(self, foods: list[Food]):
        self.foods = foods

        self.normalized_map: dict[str, Food] = {}

        for food in foods:
            slug = getattr(food, "slug", None)

            if not slug:
                continue

            normalized_slug = canonicalize_food_name(
                slug.replace("_", " ")
            )

            if normalized_slug:
                self.normalized_map[normalized_slug] = food

    # --------------------------------------------------------
    # CHARGEMENT
    # --------------------------------------------------------

    @classmethod
    def load_from_db(cls, db: Session) -> "FoodIndex":
        foods = db.query(Food).all()
        return cls(foods)

    # --------------------------------------------------------
    # SUPPRESSION PREPARATION
    # --------------------------------------------------------

    def _remove_preparation_words(self, value: str) -> str:
        normalized = normalize_text(value)

        words = normalized.split()

        cleaned = [
            word
            for word in words
            if word not in PREPARATION_WORDS
        ]

        return " ".join(cleaned).strip()

    # --------------------------------------------------------
    # RECHERCHE EXACTE
    # --------------------------------------------------------

    def _find_exact(self, value: str) -> Optional[Food]:
        normalized = canonicalize_food_name(value)

        if not normalized:
            return None

        return self.normalized_map.get(normalized)

    # --------------------------------------------------------
    # RECHERCHE FUZZY
    # --------------------------------------------------------

    def _fuzzy_find(
        self,
        value: str,
        threshold: float = 0.88,
    ) -> Optional[tuple[Food, float]]:

        normalized = canonicalize_food_name(value)

        if not normalized:
            return None

        best_food: Optional[Food] = None
        best_score = 0.0

        for candidate_name, food in self.normalized_map.items():

            score = SequenceMatcher(
                None,
                normalized,
                candidate_name,
            ).ratio()

            if score > best_score:
                best_score = score
                best_food = food

        if best_food is not None and best_score >= threshold:
            return best_food, round(best_score, 2)

        return None

    # --------------------------------------------------------
    # RECHERCHE PRINCIPALE
    # --------------------------------------------------------

    def find_food(
        self,
        detected_name: str,
    ) -> Optional[tuple[Food, float]]:

        if not detected_name:
            return None

        original = normalize_text(detected_name)

        if not original:
            return None

        # ----------------------------------------------------
        # 1. Recherche exacte
        # ----------------------------------------------------

        food = self._find_exact(original)

        if food:
            return food, 1.0

        # ----------------------------------------------------
        # 2. Suppression des mots de préparation
        # ----------------------------------------------------

        without_preparation = self._remove_preparation_words(
            original
        )

        if without_preparation and without_preparation != original:

            food = self._find_exact(without_preparation)

            if food:
                return food, 1.0

        # ----------------------------------------------------
        # 3. Gestion pluriel simple
        # ----------------------------------------------------

        singular = without_preparation

        if singular.endswith("s") and len(singular) > 3:
            singular = singular[:-1]

        food = self._find_exact(singular)

        if food:
            return food, 0.98

        # ----------------------------------------------------
        # 4. Recherche fuzzy
        # ----------------------------------------------------

        fuzzy_result = self._fuzzy_find(
            without_preparation or original
        )

        if fuzzy_result:
            return fuzzy_result

        # ----------------------------------------------------
        # Aucun match
        # ----------------------------------------------------

        return None


# ============================================================
# TRADUCTION DU NOM
# ============================================================

def get_translated_food_name(
    db: Session,
    food: Food,
    language: str = "fr",
) -> str:
    """
    Retourne le nom traduit d'un aliment.

    Si une traduction correspondant à la langue demandée
    existe, elle est utilisée.

    Sinon, on utilise le slug comme fallback.
    """

    if food is None:
        return ""

    translations = getattr(
        food,
        "translations",
        None,
    )

    if translations:

        for translation in translations:

            translation_language = getattr(
                translation,
                "language",
                None,
            )

            if translation_language == language:

                translated_name = getattr(
                    translation,
                    "name",
                    None,
                )

                if translated_name:
                    return translated_name

    slug = getattr(
        food,
        "slug",
        None,
    )

    if slug:
        return slug.replace("_", " ")

    return str(food)


# ============================================================
# MATCH + CALCUL
# ============================================================

def match_and_calculate_meal_items(
    db: Session,
    detected_foods: list,
) -> list:
    """
    Associe les aliments détectés par l'IA aux aliments
    existants dans la base Fitapp.

    Cette fonction ne modifie pas les valeurs nutritionnelles
    selon la préparation.
    """

    index = FoodIndex.load_from_db(db)

    results = []

    for detected in detected_foods:

        if isinstance(detected, dict):
            detected_name = detected.get(
                "food_name"
            ) or detected.get(
                "detected_name"
            )

            quantity = detected.get(
                "estimated_quantity_g"
            )

            preparation = detected.get(
                "preparation"
            )

            confidence = detected.get(
                "confidence"
            )

        else:
            detected_name = str(detected)
            quantity = None
            preparation = None
            confidence = None

        match = index.find_food(
            detected_name
        )

        if match:

            food, match_confidence = match

            results.append({
                "detected_name": detected_name,
                "matched": True,
                "matched_food_id": getattr(
                    food,
                    "id",
                    None,
                ),
                "matched_food_slug": getattr(
                    food,
                    "slug",
                    None,
                ),
                "matched_food_name": get_translated_food_name(
                    db,
                    food,
                    "fr",
                ),
                "estimated_quantity_g": quantity,
                "preparation": preparation,
                "confidence": confidence,
                "match_confidence": match_confidence,
            })

        else:

            results.append({
                "detected_name": detected_name,
                "matched": False,
                "matched_food_id": None,
                "matched_food_slug": None,
                "matched_food_name": None,
                "estimated_quantity_g": quantity,
                "preparation": preparation,
                "confidence": confidence,
                "match_confidence": 0.0,
            })

    return results