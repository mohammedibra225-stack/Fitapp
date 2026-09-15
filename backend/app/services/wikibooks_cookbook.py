
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

import httpx

API_URL = "https://en.wikibooks.org/w/api.php"
CONTACT_INFO =  "mailto:mohammedibra225@gmail.com"
USER_AGENT = f"FitappRecipeImport/1.0 ({CONTACT_INFO})"

REQUEST_DELAY_SECONDS = 0.4

CUISINE_CATEGORY_RE = re.compile(r"^(?P<cuisine>.+?)\s+recipes$", re.IGNORECASE)

MEAL_TYPE_KEYWORDS = {
    "breakfast": "breakfast",
    "brunch": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "main dish": "dinner",
    "main course": "dinner",
    "entree": "dinner",
    "dessert": "snack",
    "snack": "snack",
    "appetizer": "snack",
}


class WikibooksCookbookUnavailable(Exception):
    """Leve uniquement pour une vraie panne reseau/serveur (pas pour une
    page absente, qui est un cas normal)."""


# ============================================================
# HTTP CLIENT
# ============================================================

def make_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )


def _get_with_retry(client: httpx.Client, params: dict[str, Any], max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            response = client.get(API_URL, params=params)
        except httpx.RequestError as exc:
            if attempt == max_retries - 1:
                raise WikibooksCookbookUnavailable(str(exc)) from exc
            time.sleep(1.5 * (attempt + 1))
            continue

        if response.status_code == 429:
            time.sleep(2.0 * (attempt + 1))
            continue
        if response.status_code >= 500:
            if attempt == max_retries - 1:
                raise WikibooksCookbookUnavailable(f"HTTP {response.status_code}")
            time.sleep(1.5 * (attempt + 1))
            continue

        response.raise_for_status()
        return response.json()

    raise WikibooksCookbookUnavailable("Trop de tentatives echouees.")


# ============================================================
# LISTE DES RECETTES (Category:Recipes, paginee)
# ============================================================

def iter_recipe_titles(client: httpx.Client, limit: Optional[int] = None) -> Iterator[str]:
    """Genere les titres de page ('Cookbook:...') de Category:Recipes.
    S'arrete apres `limit` titres si fourni (utile pour tester)."""

    cmcontinue: Optional[str] = None
    yielded = 0

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Recipes",
            "cmlimit": "500",
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        payload = _get_with_retry(client, params)
        members = payload.get("query", {}).get("categorymembers", [])

        for member in members:
            title = member.get("title")
            if not title:
                continue
            yield title
            yielded += 1
            if limit is not None and yielded >= limit:
                return

        cmcontinue = payload.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            return

        time.sleep(REQUEST_DELAY_SECONDS)


# ============================================================
# RECUPERATION D'UNE PAGE
# ============================================================

def fetch_page_wikitext(client: httpx.Client, title: str) -> Optional[dict[str, Any]]:
    """Recupere le wikitext brut + categories d'une page. Renvoie None si
    la page n'existe pas/plus (cas normal, pas une panne)."""

    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext|categories",
        "redirects": "1",
        "format": "json",
    }
    payload = _get_with_retry(client, params)

    if "error" in payload:
        return None

    parse = payload.get("parse")
    if not parse:
        return None

    wikitext = parse.get("wikitext", {}).get("*", "")
    categories = [c.get("*", "") for c in parse.get("categories", [])]

    return {
        "title": parse.get("title", title),
        "pageid": parse.get("pageid"),
        "wikitext": wikitext,
        "categories": categories,
    }


# ============================================================
# NETTOYAGE WIKITEXT -> TEXTE BRUT
# ============================================================

def strip_wikitext(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)  # templates simples (non imbriques)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", text)  # [[lien|texte]]
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)  # [[lien]]
    text = text.replace("_", " ")
    text = re.sub(r"'''?(.*?)'''?", r"\1", text)  # '''gras''' / ''italique''
    text = re.sub(r"<[^>]+>", "", text)  # balises HTML restantes
    return text.strip()


# ============================================================
# EXTRACTION DES SECTIONS (Ingredients / Procedure)
# ============================================================

_SECTION_RE = re.compile(r"^={2,4}\s*(.+?)\s*={2,4}\s*$", re.MULTILINE)

_INGREDIENT_HEADINGS = ("ingredient",)
_STEP_HEADINGS = ("procedure", "direction", "instruction", "method", "preparation")


def _split_sections(wikitext: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(wikitext))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        heading = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(wikitext)
        sections[heading] = wikitext[start:end]
    return sections


def _find_section(sections: dict[str, str], keywords: tuple[str, ...]) -> Optional[str]:
    for heading, content in sections.items():
        if any(keyword in heading for keyword in keywords):
            return content
    return None


def extract_ingredient_lines(wikitext: str) -> list[str]:
    sections = _split_sections(wikitext)
    content = _find_section(sections, _INGREDIENT_HEADINGS)
    if not content:
        return []
    lines = re.findall(r"^\*+\s*(.+)$", content, flags=re.MULTILINE)
    return [strip_wikitext(line).strip() for line in lines if strip_wikitext(line).strip()]


def extract_step_lines(wikitext: str) -> list[str]:
    sections = _split_sections(wikitext)
    content = _find_section(sections, _STEP_HEADINGS)
    if not content:
        return []
    lines = re.findall(r"^#+\s*(.+)$", content, flags=re.MULTILINE)
    if not lines:
        # Certaines pages utilisent des puces plutot qu'une liste numerotee.
        lines = re.findall(r"^\*+\s*(.+)$", content, flags=re.MULTILINE)
    return [strip_wikitext(line).strip() for line in lines if strip_wikitext(line).strip()]


# ============================================================
# CATEGORIES -> cuisine / meal_type / vegetarien / vegan
# ============================================================

@dataclass
class CategoryHints:
    cuisine: Optional[str] = None
    meal_type: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False


def parse_category_hints(categories: list[str]) -> CategoryHints:
    hints = CategoryHints()
    for raw_category in categories:
        category = raw_category.replace("Category:", "").replace("_", " ").strip()
        lowered = category.lower()

        if "vegan" in lowered:
            hints.is_vegan = True
            hints.is_vegetarian = True
        elif "vegetarian" in lowered:
            hints.is_vegetarian = True

        if hints.meal_type is None:
            for keyword, meal_type in MEAL_TYPE_KEYWORDS.items():
                if keyword in lowered:
                    hints.meal_type = meal_type
                    break

        if hints.cuisine is None:
            match = CUISINE_CATEGORY_RE.match(category)
            if match:
                candidate = match.group("cuisine").strip()
                # Evite les categories generiques ("Recipes by ingredient",
                # "Vegetarian recipes"...) qui ne sont pas des cuisines.
                if candidate.lower() not in ("vegetarian", "vegan", "quick", "easy") and len(candidate) < 30:
                    hints.cuisine = candidate

    return hints


# ============================================================
# STRUCTURE FINALE D'UNE RECETTE PARSEE
# ============================================================

@dataclass
class ParsedRecipePage:
    title: str
    display_name: str
    source_id: str
    source_url: str
    ingredient_lines: list[str] = field(default_factory=list)
    step_lines: list[str] = field(default_factory=list)
    cuisine: Optional[str] = None
    meal_type: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False


def parse_recipe_page(page_data: dict[str, Any]) -> ParsedRecipePage:
    title = page_data["title"]
    wikitext = page_data["wikitext"]
    hints = parse_category_hints(page_data.get("categories", []))

    display_name = title.replace("Cookbook:", "").replace("_", " ").strip()

    return ParsedRecipePage(
        title=title,
        display_name=display_name,
        source_id=title,
        source_url="https://en.wikibooks.org/wiki/" + title.replace(" ", "_"),
        ingredient_lines=extract_ingredient_lines(wikitext),
        step_lines=extract_step_lines(wikitext),
        cuisine=hints.cuisine,
        meal_type=hints.meal_type,
        is_vegetarian=hints.is_vegetarian,
        is_vegan=hints.is_vegan,
    )
