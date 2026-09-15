"""
Calcule/rafraichit nutrition + cout + halal_status pour les recettes
deja en base (etapes 7 + 8 + 9 du plan Fitapp).

    Recipe (+ ingredients + food + food.prices + unmapped_ingredients)
            v
    app.services.recipe_enrichment.enrich_recipe
            v
    Recipe.calories_kcal / protein_g / ... / nutrition_status
    Recipe.cost_per_serving_da / cost_status
    Recipe.halal_status (+ is_halal en synchro)

Idempotent : relancer le script recalcule simplement les memes recettes
(utile apres avoir enrichi la Food DB ou ajoute des prix). Ne modifie
jamais les ingredients/mapping (c'est le role de import_recipes.py).

Usage :
    cd backend
    python scripts/enrich_recipes.py --limit 10
    python scripts/enrich_recipes.py --limit 10 --dry-run
    python scripts/enrich_recipes.py --slug omelette-simple
    python scripts/enrich_recipes.py            # toutes les recettes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session, selectinload  # noqa: E402

from app.database.connection import SessionLocal  # noqa: E402
from app.models.enums import HalalStatus, RecipeCostStatus, RecipeNutritionStatus  # noqa: E402
from app.models.food import Food  # noqa: E402
from app.models.recipe import Recipe, RecipeIngredient  # noqa: E402
from app.services.recipe_enrichment import enrich_recipe  # noqa: E402


class EnrichStats:
    def __init__(self) -> None:
        self.processed = 0
        self.errors = 0
        self.nutrition = {s: 0 for s in RecipeNutritionStatus}
        self.cost = {s: 0 for s in RecipeCostStatus}
        self.halal = {s: 0 for s in HalalStatus}

    def record(self, result: dict) -> None:
        self.processed += 1
        self.nutrition[result["nutrition"]["status"]] += 1
        self.cost[result["cost"]["status"]] += 1
        self.halal[result["halal_status"]] += 1

    def report(self) -> str:
        lines = [
            "=" * 60,
            "ENRICHISSEMENT RECETTES TERMINE",
            "=" * 60,
            f"Recettes traitées : {self.processed}",
            f"Erreurs (loguées, traitement continué) : {self.errors}",
            "-" * 60,
            "Nutrition : " + ", ".join(f"{s.value}={n}" for s, n in self.nutrition.items()),
            "Coût      : " + ", ".join(f"{s.value}={n}" for s, n in self.cost.items()),
            "Halal     : " + ", ".join(f"{s.value}={n}" for s, n in self.halal.items()),
            "=" * 60,
        ]
        return "\n".join(lines)


def load_recipes(db: Session, limit: int | None, slug: str | None) -> list[Recipe]:
    query = (
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.food).selectinload(Food.prices),
            selectinload(Recipe.unmapped_ingredients),
        )
        .order_by(Recipe.slug)
    )
    if slug:
        query = query.where(Recipe.slug == slug)
    if limit is not None:
        query = query.limit(limit)
    return list(db.execute(query).scalars().unique().all())


def run_enrichment(limit: int | None, slug: str | None, dry_run: bool) -> None:
    db = SessionLocal()
    stats = EnrichStats()

    try:
        recipes = load_recipes(db, limit=limit, slug=slug)
        print(f"{len(recipes)} recette(s) à traiter.")

        for i, recipe in enumerate(recipes, start=1):
            try:
                result = enrich_recipe(recipe)
                stats.record(result)

                if dry_run:
                    print(
                        f"[{i}/{len(recipes)}] {recipe.slug} -> "
                        f"nutrition={result['nutrition']['status'].value} "
                        f"cost={result['cost']['status'].value} "
                        f"halal={result['halal_status'].value}"
                    )
                    db.rollback()
                else:
                    db.commit()

            except Exception as exc:  # noqa: BLE001 - on log et on continue (regle 20)
                db.rollback()
                stats.errors += 1
                print(f"[{i}/{len(recipes)}] Erreur sur '{recipe.slug}': {exc}")
                continue

        print(stats.report())

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcule nutrition/cout/halal des recettes.")
    parser.add_argument("--limit", type=int, default=None, help="Nombre de recettes a traiter (defaut: toutes).")
    parser.add_argument("--slug", type=str, default=None, help="Ne traiter qu'une seule recette (par slug).")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcule et affiche les résultats sans rien enregistrer en base.",
    )
    args = parser.parse_args()

    run_enrichment(limit=args.limit, slug=args.slug, dry_run=args.dry_run)
