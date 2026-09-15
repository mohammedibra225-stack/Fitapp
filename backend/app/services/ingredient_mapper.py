"""
Normalisation et rapprochement d'un texte d'ingredient brut (issu d'une
source externe) avec notre table `foods` existante.

Regle 4/5 (spec import recettes) :
    texte source -> normalisation -> recherche Food -> match
    Si la correspondance est incertaine : "unmapped" plutot qu'un mauvais
    match. On ne devine JAMAIS un aliment a partir d'un mot vague
    ("sauce", "spice mix", etc.).

Ce module ne fait aucun appel reseau ni acces DB en ecriture : il prend
en entree un index de Food deja charge (build_food_index) et une ligne
de texte brute, et renvoie un resultat structure.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import MeasurementUnit
from app.models.food import Food, FoodTranslation


# ============================================================
# UNITES : alias texte -> MeasurementUnit (+ facteur de conversion
# eventuel vers l'unite cible, pour les unites US absentes de notre enum)
# ============================================================

# (unite_cible, facteur_multiplicatif applique a la quantite)
UNIT_ALIASES: dict[str, tuple[MeasurementUnit, Decimal]] = {
    # masse
    "g": (MeasurementUnit.G, Decimal("1")),
    "gram": (MeasurementUnit.G, Decimal("1")),
    "grams": (MeasurementUnit.G, Decimal("1")),
    "gramme": (MeasurementUnit.G, Decimal("1")),
    "grammes": (MeasurementUnit.G, Decimal("1")),
    "kg": (MeasurementUnit.KG, Decimal("1")),
    "kilogram": (MeasurementUnit.KG, Decimal("1")),
    "kilograms": (MeasurementUnit.KG, Decimal("1")),
    "oz": (MeasurementUnit.G, Decimal("28.35")),
    "ounce": (MeasurementUnit.G, Decimal("28.35")),
    "ounces": (MeasurementUnit.G, Decimal("28.35")),
    "lb": (MeasurementUnit.G, Decimal("453.6")),
    "lbs": (MeasurementUnit.G, Decimal("453.6")),
    "pound": (MeasurementUnit.G, Decimal("453.6")),
    "pounds": (MeasurementUnit.G, Decimal("453.6")),
    # volume
    "ml": (MeasurementUnit.ML, Decimal("1")),
    "milliliter": (MeasurementUnit.ML, Decimal("1")),
    "milliliters": (MeasurementUnit.ML, Decimal("1")),
    "l": (MeasurementUnit.L, Decimal("1")),
    "liter": (MeasurementUnit.L, Decimal("1")),
    "liters": (MeasurementUnit.L, Decimal("1")),
    "litre": (MeasurementUnit.L, Decimal("1")),
    "litres": (MeasurementUnit.L, Decimal("1")),
    "fl oz": (MeasurementUnit.ML, Decimal("29.57")),
    "fluid ounce": (MeasurementUnit.ML, Decimal("29.57")),
    "fluid ounces": (MeasurementUnit.ML, Decimal("29.57")),
    "pint": (MeasurementUnit.ML, Decimal("473")),
    "pints": (MeasurementUnit.ML, Decimal("473")),
    "quart": (MeasurementUnit.ML, Decimal("946")),
    "quarts": (MeasurementUnit.ML, Decimal("946")),
    # unites relatives (deja dans MeasurementUnit)
    "cup": (MeasurementUnit.CUP, Decimal("1")),
    "cups": (MeasurementUnit.CUP, Decimal("1")),
    "tbsp": (MeasurementUnit.TBSP, Decimal("1")),
    "tbsps": (MeasurementUnit.TBSP, Decimal("1")),
    "tablespoon": (MeasurementUnit.TBSP, Decimal("1")),
    "tablespoons": (MeasurementUnit.TBSP, Decimal("1")),
    "tbs": (MeasurementUnit.TBSP, Decimal("1")),
    "tsp": (MeasurementUnit.TSP, Decimal("1")),
    "tsps": (MeasurementUnit.TSP, Decimal("1")),
    "teaspoon": (MeasurementUnit.TSP, Decimal("1")),
    "teaspoons": (MeasurementUnit.TSP, Decimal("1")),
    "serving": (MeasurementUnit.SERVING, Decimal("1")),
    "servings": (MeasurementUnit.SERVING, Decimal("1")),
    # pieces
    "piece": (MeasurementUnit.PIECE, Decimal("1")),
    "pieces": (MeasurementUnit.PIECE, Decimal("1")),
    "pc": (MeasurementUnit.PIECE, Decimal("1")),
    "pcs": (MeasurementUnit.PIECE, Decimal("1")),
    "whole": (MeasurementUnit.PIECE, Decimal("1")),
    "clove": (MeasurementUnit.PIECE, Decimal("1")),
    "cloves": (MeasurementUnit.PIECE, Decimal("1")),
    "slice": (MeasurementUnit.PIECE, Decimal("1")),
    "slices": (MeasurementUnit.PIECE, Decimal("1")),
}

# Trie par longueur decroissante pour matcher "fl oz" avant "oz".
_UNIT_TOKENS_BY_LENGTH = sorted(UNIT_ALIASES.keys(), key=len, reverse=True)

UNICODE_FRACTIONS = {
    "¼": Decimal("0.25"), "½": Decimal("0.5"), "¾": Decimal("0.75"),
    "⅓": Decimal("0.3333"), "⅔": Decimal("0.6667"),
    "⅛": Decimal("0.125"), "⅜": Decimal("0.375"),
    "⅝": Decimal("0.625"), "⅞": Decimal("0.875"),
}

# Mots de preparation a retirer avant de chercher le nom de l'aliment
# (ils ne font pas partie du nom lui-meme).
PREP_WORDS = {
    "chopped", "diced", "minced", "sliced", "crushed", "peeled", "grated",
    "shredded", "cooked", "raw", "fresh", "dried", "ground", "large",
    "small", "medium", "ripe", "boneless", "skinless", "beaten", "melted",
    "softened", "room", "temperature", "finely", "coarsely", "thinly",
    "washed", "trimmed", "halved", "quartered", "cubed", "to", "taste",
    "optional", "for", "serving", "garnish", "of", "a", "an", "the",
}


# ============================================================
# NORMALISATION DE TEXTE
# ============================================================

def _strip_accents(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def normalize_text(value: str) -> str:
    """minuscule, sans accents, ponctuation retiree, espaces compresses."""
    value = _strip_accents(value).lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _strip_prep_words(value: str) -> str:
    words = [w for w in value.split(" ") if w and w not in PREP_WORDS]
    return " ".join(words)


def _singularize(word: str) -> str:
    """Heuristique simple, suffisante pour du vocabulaire culinaire courant."""
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxz":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalize_ingredient_core(value: str) -> str:
    """Nettoie un texte d'ingredient (deja debarrasse de la quantite/unite)
    pour ne garder que le coeur du nom, pret a etre compare a l'index Food.

    Retire TOUTES les clauses entre parentheses ou apres une virgule, ou
    qu'elles apparaissent dans la chaine (pas seulement la premiere) :
    - "chicken breast (skinless, boneless)" -> "chicken breast"
    - "(240 ml) milk" -> "milk" (le paranthese peut precede le nom quand
      elle contient une conversion metrique laissee par l'unite parsee ;
      un simple split sur le premier '(' viderait alors tout le texte).
    """
    # Retire tout groupe entre parentheses, ou qu'il soit dans la chaine.
    value = re.sub(r"\([^)]*\)", " ", value)
    # Retire aussi une clause finale introduite par une virgule
    # (qualificatif de preparation, ex: ", diced").
    value = value.split(",")[0]
    value = normalize_text(value)
    value = _strip_prep_words(value)
    words = [_singularize(w) for w in value.split(" ") if w]
    return " ".join(words)


# ============================================================
# PARSING QUANTITE + UNITE
# ============================================================

@dataclass
class ParsedIngredientLine:
    raw_text: str
    quantity: Optional[Decimal]
    unit: Optional[MeasurementUnit]
    name_text: str  # ce qui reste apres avoir retire quantite/unite


def _parse_quantity_token(token: str) -> Optional[Decimal]:
    token = token.strip()
    if not token:
        return None
    if token in UNICODE_FRACTIONS:
        return UNICODE_FRACTIONS[token]
    # Nombre mixte avec fraction unicode, collee ou espacee : "1½", "1 ½".
    mixed_unicode = re.match(r"^(\d+)\s*([¼½¾⅓⅔⅛⅜⅝⅞])$", token)
    if mixed_unicode:
        whole, frac_char = mixed_unicode.groups()
        return Decimal(whole) + UNICODE_FRACTIONS[frac_char]
    # "1 1/2" (nombre mixte)
    mixed = re.match(r"^(\d+)\s+(\d+)/(\d+)$", token)
    if mixed:
        whole, num, den = mixed.groups()
        try:
            return Decimal(whole) + (Decimal(num) / Decimal(den))
        except (InvalidOperation, ZeroDivisionError):
            return None
    # "1/2"
    frac = re.match(r"^(\d+)/(\d+)$", token)
    if frac:
        num, den = frac.groups()
        try:
            return Decimal(num) / Decimal(den)
        except (InvalidOperation, ZeroDivisionError):
            return None
    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def parse_ingredient_line(raw_line: str) -> ParsedIngredientLine:
    """Extrait (quantite, unite, reste_du_texte) d'une ligne d'ingredient
    brute type '2 eggs', '1 1/2 cups flour', '100 g rice', 'Salt to taste'.

    Si aucune quantite n'est reconnue au debut de la ligne, quantity et
    unit valent None : l'appelant doit alors traiter la ligne comme non
    exploitable pour une RecipeIngredient stricte (regle : pas de 0/valeur
    inventee), et la stocker en ingredient non mappe.
    """
    text = raw_line.strip()

    qty_match = re.match(
        r"^(?P<qty>(?:\d+\s+\d+/\d+)|(?:\d+\s*[¼½¾⅓⅔⅛⅜⅝⅞])|(?:\d+/\d+)|(?:\d+(?:\.\d+)?)|[¼½¾⅓⅔⅛⅜⅝⅞])\s*",
        text,
    )
    if not qty_match:
        return ParsedIngredientLine(raw_text=raw_line, quantity=None, unit=None, name_text=text)

    quantity = _parse_quantity_token(qty_match.group("qty"))
    remainder = text[qty_match.end():].strip()

    if quantity is None:
        return ParsedIngredientLine(raw_text=raw_line, quantity=None, unit=None, name_text=text)

    # Cherche un token d'unite juste apres la quantite (le plus long
    # d'abord, pour matcher "fl oz" avant "oz").
    lowered = remainder.lower()
    unit: Optional[MeasurementUnit] = None
    factor = Decimal("1")
    for token in _UNIT_TOKENS_BY_LENGTH:
        if lowered == token or lowered.startswith(token + " ") or lowered.startswith(token + "."):
            unit, factor = UNIT_ALIASES[token]
            remainder = remainder[len(token):].lstrip(". ").strip()
            break

    if unit is None:
        # Pas d'unite reconnue : un compte nu ("2 eggs") vaut "piece".
        unit = MeasurementUnit.PIECE

    quantity = quantity * factor

    return ParsedIngredientLine(
        raw_text=raw_line,
        quantity=quantity,
        unit=unit,
        name_text=remainder or text,
    )


# ============================================================
# INDEX FOOD (a construire une fois par import, pas par ligne)
# ============================================================

# Alias explicites, limites aux synonymes culinaires certains. Ils eviteront
# d'augmenter le fuzzy matching, qui doit rester prudent.
FOOD_ALIASES: dict[str, tuple[str, ...]] = {
    "ail": ("garlic clove", "garlic cloves", "fresh garlic", "ail frais"),
    "gingembre": ("fresh ginger", "ginger root"),
    "persil": ("fresh parsley", "flat leaf parsley", "italian parsley"),
    "coriandre": ("fresh cilantro", "coriander", "fresh coriander"),
    "poivre_noir": ("ground black pepper", "pepper"),
    "sauce_soja": ("soy sauce", "soya sauce"),
    "patate_douce": ("sweet potato", "sweet potatoes"),
    "mais": ("corn kernels", "sweet corn", "canned corn"),
    "farine": ("all purpose flour", "all-purpose flour", "plain flour", "wheat flour", "self raising flour", "self-raising flour"),
    "chapelure": ("bread crumbs", "panko", "panko breadcrumbs"),
    "viande_hachee": ("ground beef", "minced beef", "beef mince"),
    "dinde": ("turkey breast", "ground turkey"),
    "saumon": ("salmon fillet", "salmon filet"),
    "crevettes": ("shrimp", "prawns", "prawn"),
    "beurre": ("unsalted butter", "salted butter"),
    "citron": ("lemon juice", "fresh lemon juice", "lemon zest"),
    "fraise": ("strawberries", "fresh strawberries"),
    "noix": ("walnut", "walnuts", "chopped walnuts"),
    "beurre_cacahuete": ("peanut butter", "smooth peanut butter"),
    "lait_de_coco": ("coconut milk", "full fat coconut milk"),
    "sauce_tomate": ("passata", "tomato passata"),

    # --- Elargissement V2 : legumes, epicerie, viandes ---
    "aubergine": ("eggplant", "eggplants", "aubergines"),
    "epinards": ("spinach", "fresh spinach", "baby spinach"),
    "concombre": ("cucumber", "cucumbers"),
    "poivron": ("bell pepper", "bell peppers", "green pepper", "red pepper", "yellow pepper", "capsicum", "sweet pepper"),
    "champignon": ("mushroom", "mushrooms", "button mushrooms", "white mushrooms"),
    "chou": ("cabbage", "green cabbage", "white cabbage"),
    "poireau": ("leek", "leeks"),
    "brocoli": ("broccoli", "broccoli florets"),
    "chou_fleur": ("cauliflower", "cauliflower florets"),
    "haricots_verts": ("green beans", "string beans", "french beans"),
    "petits_pois": ("peas", "green peas", "frozen peas"),
    "oignon_vert": ("green onion", "green onions", "scallion", "scallions", "spring onion", "spring onions"),
    "pois_chiches": ("garbanzo beans", "garbanzos"),
    "haricots_secs": ("dried beans", "kidney beans", "white beans", "navy beans"),

    "sucre": ("granulated sugar", "caster sugar", "white sugar", "powdered sugar", "icing sugar", "confectioners sugar"),
    "cassonade": ("brown sugar", "light brown sugar", "dark brown sugar"),
    "levure_chimique": ("baking powder",),
    "bicarbonate": ("baking soda", "bicarbonate of soda", "sodium bicarbonate"),
    "levure_boulangere": ("yeast", "dry yeast", "active dry yeast", "instant yeast"),
    "cacao": ("cocoa powder", "unsweetened cocoa", "cocoa"),
    "chocolat_noir": ("dark chocolate", "semisweet chocolate", "chocolate chips", "bittersweet chocolate"),
    "noix_coco_rapee": ("shredded coconut", "desiccated coconut", "grated coconut", "coconut flakes"),
    "raisins_secs": ("raisins", "sultanas"),
    "vanille": ("vanilla extract", "vanilla essence", "vanilla"),
    "maizena": ("cornstarch", "corn starch", "corn flour"),

    "feuille_laurier": ("bay leaf", "bay leaves"),
    "origan": ("oregano", "dried oregano"),
    "basilic": ("basil", "fresh basil", "dried basil"),
    "cannelle": ("cinnamon", "ground cinnamon", "cinnamon stick"),

    "creme_liquide": ("heavy cream", "whipping cream", "double cream", "heavy whipping cream"),
    "creme_fraiche": ("sour cream", "creme fraiche"),
    "cheddar": ("cheddar cheese", "grated cheddar", "sharp cheddar"),
    "mayonnaise": ("mayo",),
    "moutarde": ("mustard", "dijon mustard", "yellow mustard"),
    "ketchup": ("tomato ketchup", "catsup"),
    "bouillon_cube": ("stock cube", "bouillon cube", "chicken stock", "chicken broth", "vegetable stock", "vegetable broth", "beef stock", "beef broth"),

    "cuisse_poulet": ("chicken thigh", "chicken thighs", "chicken legs"),
    "agneau": ("lamb", "ground lamb", "lamb chops", "lamb shoulder"),

    "vin": ("wine", "red wine", "white wine", "cooking wine"),
    "bacon": ("bacon strips", "bacon slices", "streaky bacon"),
    "jambon": ("ham", "sliced ham", "cooked ham"),
    "porc": ("pork", "pork chop", "pork loin", "ground pork", "pork shoulder"),
    "gelatine": ("gelatin", "gelatine", "gelatin powder", "unflavored gelatin"),

    # Substitution generique raisonnable pour "huile" non precisee dans
    # une recette (l'huile de tournesol est la plus courante/economique).
    "huile_tournesol": ("vegetable oil", "cooking oil", "sunflower oil", "neutral oil"),
}

def build_food_index(db: Session) -> dict[str, Food]:
    """Construit {nom_normalise: Food} a partir des slugs et traductions
    (fr/en) de tous les Food existants. Plusieurs cles peuvent pointer
    vers le meme Food (slug + chaque traduction)."""

    foods = db.execute(
        select(Food).options(selectinload(Food.translations))
    ).scalars().unique().all()

    index: dict[str, Food] = {}
    for food in foods:
        candidates = {food.slug.replace("_", " ")}
        for translation in food.translations:
            if translation.language_code in ("en", "fr"):
                candidates.add(translation.name)
        candidates.update(FOOD_ALIASES.get(food.slug, ()))

        for candidate in candidates:
            key = normalize_ingredient_core(candidate)
            if key and key not in index:
                index[key] = food

    return index


# ============================================================
# MATCH
# ============================================================

@dataclass
class FoodMatch:
    food: Optional[Food]
    confidence: float


def match_food(name_text: str, food_index: dict[str, Food]) -> FoodMatch:
    """Rapproche un nom d'ingredient (deja isole de sa quantite) d'un Food
    existant. Renvoie food=None si aucune correspondance suffisamment
    fiable n'est trouvee (regle : ne jamais deviner)."""

    core = normalize_ingredient_core(name_text)
    if not core:
        return FoodMatch(food=None, confidence=0.0)

    if core in food_index:
        return FoodMatch(food=food_index[core], confidence=1.0)

    # Essai sur le dernier mot seul (ex: "large chicken breast" -> "breast"
    # a deja ete nettoye par _strip_prep_words ; ici on tente le premier
    # mot significatif si le texte complet ne matche pas).
    words = core.split(" ")
    if len(words) > 1 and words[-1] in food_index:
        return FoodMatch(food=food_index[words[-1]], confidence=0.9)

    close = difflib.get_close_matches(core, food_index.keys(), n=1, cutoff=0.84)
    if close:
        ratio = difflib.SequenceMatcher(None, core, close[0]).ratio()
        return FoodMatch(food=food_index[close[0]], confidence=ratio)

    return FoodMatch(food=None, confidence=0.0)
