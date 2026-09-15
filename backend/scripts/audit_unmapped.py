

from __future__ import annotations
import argparse
import sys
from pathlib import Path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import func, select  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402
from app.models.recipe import Recipe, UnmappedRecipeIngredient  # noqa: E402
from app.services.ingredient_mapper import normalize_ingredient_core  # noqa: E402

def audit(limit: int) -> None:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(
                UnmappedRecipeIngredient.raw_text,
                func.count(UnmappedRecipeIngredient.id).label("occurrences"),
                func.count(func.distinct(UnmappedRecipeIngredient.recipe_id)).label("recipes"),
            )
            .group_by(UnmappedRecipeIngredient.raw_text)
            .order_by(func.count(UnmappedRecipeIngredient.id).desc())
            .limit(limit)
        ).all()

        total = db.scalar(select(func.count(UnmappedRecipeIngredient.id))) or 0
        recipe_count = db.scalar(
            select(func.count(func.distinct(UnmappedRecipeIngredient.recipe_id)))
        ) or 0
        imported_count = db.scalar(
            select(func.count(Recipe.id)).where(Recipe.source.is_not(None))
        ) or 0
        print("AUDIT DES INGREDIENTS NON MAPPES")
        print(f"Total unmapped             : {total}")
        print(f"Recettes concernees        : {recipe_count}")
        print(f"Recettes avec une source   : {imported_count}")
        print("\nTop des textes a couvrir :")
        print("Occurrences | Recettes | Texte | Normalise")
        print("-" * 78)
        for raw_text, occurrences, recipes in rows:
            normalized = normalize_ingredient_core(raw_text)
            print(f"{occurrences:11} | {recipes:8} | {raw_text[:42]:42} | {normalized}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit des ingredients non mappes.")
    parser.add_argument("--limit", type=int, default=50, help="Nombre de lignes a afficher.")
    args = parser.parse_args()
    audit(max(1, args.limit))
