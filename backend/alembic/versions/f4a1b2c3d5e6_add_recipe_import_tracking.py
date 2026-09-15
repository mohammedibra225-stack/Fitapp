"""add recipe import tracking (source, cuisine, meal_type) + unmapped ingredients

Revision ID: f4a1b2c3d5e6
Revises: d4e5f6a7b8c9
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f4a1b2c3d5e6'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Nouveaux enums (crees explicitement une seule fois ici ;
    # create_type=False empeche SQLAlchemy de re-emettre un second
    # CREATE TYPE quand le type est ensuite utilise dans une colonne) ---
    recipe_data_source = postgresql.ENUM(
        'manual', 'wikibooks_cookbook', name='recipe_data_source', create_type=False
    )
    recipe_data_source.create(op.get_bind(), checkfirst=True)

    ingredient_match_status = postgresql.ENUM(
        'matched', 'unmapped', name='ingredient_match_status', create_type=False
    )
    ingredient_match_status.create(op.get_bind(), checkfirst=True)

    recipe_meal_type = postgresql.ENUM(
        'breakfast', 'lunch', 'dinner', 'snack', name='recipe_meal_type', create_type=False
    )
    recipe_meal_type.create(op.get_bind(), checkfirst=True)

    # --- Nouveaux champs sur recipes ---
    op.add_column('recipes', sa.Column('cuisine', sa.String(length=50), nullable=True))
    op.add_column(
        'recipes',
        sa.Column('meal_type', recipe_meal_type, nullable=True),
    )
    op.add_column(
        'recipes',
        sa.Column(
            'source',
            recipe_data_source,
            nullable=False,
            server_default='manual',
        ),
    )
    op.add_column('recipes', sa.Column('source_id', sa.String(length=150), nullable=True))
    op.add_column('recipes', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.create_index('ix_recipes_source_id', 'recipes', ['source_id'])

    # --- Table des ingredients non mappes ---
    op.create_table(
        'unmapped_recipe_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_text', sa.String(length=300), nullable=False),
        sa.Column('raw_quantity', sa.String(length=100), nullable=True),
        sa.Column('display_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('status', ingredient_match_status, nullable=False, server_default='unmapped'),
    )
    op.create_index(
        'ix_unmapped_recipe_ingredients_recipe_id',
        'unmapped_recipe_ingredients',
        ['recipe_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_unmapped_recipe_ingredients_recipe_id', table_name='unmapped_recipe_ingredients')
    op.drop_table('unmapped_recipe_ingredients')

    op.drop_index('ix_recipes_source_id', table_name='recipes')
    op.drop_column('recipes', 'source_url')
    op.drop_column('recipes', 'source_id')
    op.drop_column('recipes', 'source')
    op.drop_column('recipes', 'meal_type')
    op.drop_column('recipes', 'cuisine')

    postgresql.ENUM(name='recipe_data_source').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='ingredient_match_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='recipe_meal_type').drop(op.get_bind(), checkfirst=True)
