"""
Import automatique de recettes depuis Wikibooks Cookbook vers notre
PostgreSQL (etape 5 + 6 du plan Fitapp).

    Wikibooks Cookbook (categorymembers)
            v
    fetch wikitext + categories (wikibooks_cookbook.py)
            v
    parse ingredients/steps/categories
            v
    normalisation + mapping vers Food (ingredient_mapper.py)
            v
    Recipe / RecipeIngredient / RecipeStep (matches)
    UnmappedRecipeIngredient (non-matches, n'empeche pas l'import)

Deduplication : source=WIKIBOOKS_COOKBOOK + source_id=titre de la page
(regle 21) -> une recette deja importee est ignoree (idempotent, on peut
relancer le script sans creer de doublons).

Ne calcule PAS encore la nutrition/le cout (etape 7/8, prochaine etape) :
Recipe.calories_kcal etc. restent NULL pour les recettes importees ici.

Usage :
    cd backend
    python scripts/import_recipes.py --limit 30
    python scripts/import_recipes.py --limit 30 --dry-run
    python scripts/import_recipes.py            # tout Category:Recipes (long)
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

# Permet de lancer ce script directement (python scripts/import_recipes.py)
# en ayant quand meme acces aux modules `app.*` du backend.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database.connection import SessionLocal  # noqa: E402
from app.models.enums import IngredientMatchStatus, RecipeDataSource  # noqa: E402
from app.models.recipe import (  # noqa: E402
    Recipe,
    RecipeIngredient,
    RecipeStep,
    RecipeStepTranslation,
    RecipeTranslation,
    UnmappedRecipeIngredient,
)
from app.services.ingredient_mapper import (  # noqa: E402
    build_food_index,
    match_food,
    parse_ingredient_line,
)
from app.services.wikibooks_cookbook import (  # noqa: E402
    ParsedRecipePage,
    fetch_page_wikitext,
    iter_recipe_titles,
    make_client,
    parse_recipe_page,
    REQUEST_DELAY_SECONDS,
    WikibooksCookbookUnavailable,
)

# Seuil de confiance minimal pour accepter un match flou (regle : mieux
# vaut "unmapped" qu'une mauvaise association).
MIN_MATCH_CONFIDENCE = 0.84

# En dessous de ce nombre d'ingredients exploitables, on saute la recette
# (page trop pauvre pour etre utile a l'app).
MIN_INGREDIENT_LINES = 2


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:140] or "recette"


def unique_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    suffix = 1
    while db.execute(select(Recipe.id).where(Recipe.slug == slug)).scalar_one_or_none():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


class ImportStats:
    def __init__(self) -> None:
        self.created = 0
        self.skipped_duplicate = 0
        self.skipped_too_thin = 0
        self.errors = 0
        self.ingredients_matched = 0
        self.ingredients_unmapped = 0

    def report(self) -> str:
        return (
            "=" * 60 + "\n"
            "IMPORT RECETTES WIKIBOOKS COOKBOOK TERMINE\n" + "=" * 60 + "\n"
            f"Recettes créées                : {self.created}\n"
            f"Recettes ignorées (doublon)     : {self.skipped_duplicate}\n"
            f"Recettes ignorées (trop pauvres): {self.skipped_too_thin}\n"
            f"Erreurs (loguees, import continué) : {self.errors}\n"
            f"Ingrédients rapprochés d'un Food: {self.ingredients_matched}\n"
            f"Ingrédients non mappés (unmapped): {self.ingredients_unmapped}\n"
            + "=" * 60
        )


def recipe_already_imported(db: Session, source_id: str) -> bool:
    existing = db.execute(
        select(Recipe.id).where(
            Recipe.source == RecipeDataSource.WIKIBOOKS_COOKBOOK,
            Recipe.source_id == source_id,
        )
    ).scalar_one_or_none()
    return existing is not None


def import_one_recipe(
    db: Session,
    parsed: ParsedRecipePage,
    food_index: dict,
    stats: ImportStats,
    dry_run: bool,
) -> None:
    if len(parsed.ingredient_lines) < MIN_INGREDIENT_LINES or not parsed.step_lines:
        stats.skipped_too_thin += 1
        return

    if recipe_already_imported(db, parsed.source_id):
        stats.skipped_duplicate += 1
        return

    slug = unique_slug(db, slugify(parsed.display_name))

    recipe = Recipe(
        slug=slug,
        servings=1,
        is_vegetarian=parsed.is_vegetarian,
        is_vegan=parsed.is_vegan,
        is_halal=False,  # jamais deduit automatiquement (regle 10)
        is_gluten_free=False,
        cuisine=parsed.cuisine,
        meal_type=parsed.meal_type,
        source=RecipeDataSource.WIKIBOOKS_COOKBOOK,
        source_id=parsed.source_id,
        source_url=parsed.source_url,
    )
    db.add(recipe)
    db.flush()  # pour recipe.id

    db.add(
        RecipeTranslation(
            recipe_id=recipe.id,
            language_code="en",
            name=parsed.display_name,
            description=None,
        )
    )

    for order, raw_line in enumerate(parsed.ingredient_lines):
        parsed_line = parse_ingredient_line(raw_line)

        matched_food = None
        if parsed_line.quantity is not None and parsed_line.unit is not None:
            match = match_food(parsed_line.name_text, food_index)
            if match.food is not None and match.confidence >= MIN_MATCH_CONFIDENCE:
                matched_food = match.food

        if matched_food is not None:
            db.add(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    food_id=matched_food.id,
                    quantity=parsed_line.quantity,
                    unit=parsed_line.unit,
                    display_order=order,
                )
            )
            stats.ingredients_matched += 1
        else:
            db.add(
                UnmappedRecipeIngredient(
                    recipe_id=recipe.id,
                    raw_text=raw_line[:300],
                    raw_quantity=(str(parsed_line.quantity) if parsed_line.quantity is not None else None),
                    display_order=order,
                    status=IngredientMatchStatus.UNMAPPED,
                )
            )
            stats.ingredients_unmapped += 1

    for step_number, step_text in enumerate(parsed.step_lines, start=1):
        step = RecipeStep(recipe_id=recipe.id, step_number=step_number)
        db.add(step)
        db.flush()
        db.add(
            RecipeStepTranslation(
                recipe_step_id=step.id,
                language_code="en",
                instruction=step_text[:2000],
            )
        )

    if dry_run:
        db.rollback()
    else:
        db.commit()
    stats.created += 1


def run_import(limit: int | None, dry_run: bool) -> None:
    db = SessionLocal()
    stats = ImportStats()

    try:
        food_index = build_food_index(db)
        print(f"Index Food construit : {len(food_index)} entrées de recherche.")

        with make_client() as client:
            titles = list(iter_recipe_titles(client, limit=limit))
            print(f"{len(titles)} pages à traiter (Category:Recipes).")

            for i, title in enumerate(titles, start=1):
                try:
                    page_data = fetch_page_wikitext(client, title)
                    time.sleep(REQUEST_DELAY_SECONDS)

                    if page_data is None:
                        continue

                    parsed = parse_recipe_page(page_data)
                    import_one_recipe(db, parsed, food_index, stats, dry_run)

                except WikibooksCookbookUnavailable as exc:
                    print(f"[{i}/{len(titles)}] Wikibooks indisponible, arrêt : {exc}")
                    break
                except Exception as exc:  # noqa: BLE001 - on log et on continue (regle 20)
                    db.rollback()
                    stats.errors += 1
                    print(f"[{i}/{len(titles)}] Erreur sur '{title}': {exc}")
                    continue

                if i % 10 == 0:
                    print(f"[{i}/{len(titles)}] traité...")

        print(stats.report())

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import de recettes depuis Wikibooks Cookbook.")
    parser.add_argument(
        "--limit", type=int, default=30,
        help="Nombre de pages a traiter (defaut: 30, pour tester sans tout importer). "
             "Utilise --limit 0 pour ne pas limiter (tout Category:Recipes, plusieurs milliers de pages).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse et affiche les stats sans rien enregistrer en base.",
    )
    args = parser.parse_args()

    run_import(limit=(None if args.limit == 0 else args.limit), dry_run=args.dry_run)
