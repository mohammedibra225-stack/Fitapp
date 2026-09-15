"""add recipe nutrition (fiber/sugar/sodium + status), cost, halal_status

Revision ID: a7c2e4f1b3d9
Revises: f4a1b2c3d5e6
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7c2e4f1b3d9'
down_revision: Union[str, None] = 'f4a1b2c3d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    recipe_nutrition_status = postgresql.ENUM(
        'complete', 'partial', 'unknown', name='recipe_nutrition_status', create_type=False
    )
    recipe_nutrition_status.create(bind, checkfirst=True)

    recipe_cost_status = postgresql.ENUM(
        'known', 'partial', 'unknown', name='recipe_cost_status', create_type=False
    )
    recipe_cost_status.create(bind, checkfirst=True)

    # Type Postgres distinct de 'halal_status' (deja utilise par foods),
    # meme convention que measurement_unit / inventory_measurement_unit /
    # recipe_ingredient_unit : un type par table, meme si l'enum Python
    # (HalalStatus) est partage.
    recipe_halal_status = postgresql.ENUM(
        'halal', 'not_halal', 'unknown', name='recipe_halal_status', create_type=False
    )
    recipe_halal_status.create(bind, checkfirst=True)

    # --- Nutrition (regle 6) ---
    op.add_column('recipes', sa.Column('fiber_g', sa.Numeric(6, 2), nullable=True))
    op.add_column('recipes', sa.Column('sugar_g', sa.Numeric(6, 2), nullable=True))
    op.add_column('recipes', sa.Column('sodium_mg', sa.Numeric(7, 2), nullable=True))
    op.add_column(
        'recipes',
        sa.Column('nutrition_status', recipe_nutrition_status, nullable=False, server_default='unknown'),
    )

    # --- Cout reel (regle 8), distinct de estimated_cost_level ---
    op.add_column('recipes', sa.Column('cost_per_serving_da', sa.Numeric(8, 2), nullable=True))
    op.add_column(
        'recipes',
        sa.Column('cost_status', recipe_cost_status, nullable=False, server_default='unknown'),
    )

    # --- Halal a 3 valeurs (regle 10) ---
    op.add_column(
        'recipes',
        sa.Column('halal_status', recipe_halal_status, nullable=False, server_default='unknown'),
    )

    # Backfill : les recettes deja marquees is_halal=true (saisies
    # manuellement via seed_recipes.py) doivent garder ce statut au
    # lieu de retomber a 'unknown' et disparaitre des filtres
    # halal_required (regle 28 : ne pas casser l'existant).
    op.execute("UPDATE recipes SET halal_status = 'halal' WHERE is_halal = true")


def downgrade() -> None:
    op.drop_column('recipes', 'halal_status')
    op.drop_column('recipes', 'cost_status')
    op.drop_column('recipes', 'cost_per_serving_da')
    op.drop_column('recipes', 'nutrition_status')
    op.drop_column('recipes', 'sodium_mg')
    op.drop_column('recipes', 'sugar_g')
    op.drop_column('recipes', 'fiber_g')

    bind = op.get_bind()
    postgresql.ENUM(name='recipe_halal_status').drop(bind, checkfirst=True)
    postgresql.ENUM(name='recipe_cost_status').drop(bind, checkfirst=True)
    postgresql.ENUM(name='recipe_nutrition_status').drop(bind, checkfirst=True)
