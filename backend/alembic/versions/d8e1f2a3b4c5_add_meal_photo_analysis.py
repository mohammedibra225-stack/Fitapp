"""add meal_photo_analyses and meal_photo_analysis_items (AI Meal Analysis)

Revision ID: d8e1f2a3b4c5
Revises: c7d79267f89c
Create Date: 2026-09-11 00:00:00.000000

NOTE (corrige apres coup) : les tables meal_photo_analyses et
meal_photo_analysis_items existaient DEJA depuis la toute premiere
migration (f2ca8c4593df_initial_database.py). Cette migration avait ete
ecrite sans s'en rendre compte et tentait de les recreer, ce qui provoque
un "DuplicateTable" au upgrade. Elle est donc neutralisee (no-op) : la
correction reelle (image_url nullable) est portee par la migration
suivante e1a2b3c4d5f6.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision: str = 'd8e1f2a3b4c5'
down_revision: Union[str, None] = 'c7d79267f89c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Les tables existent deja (creees par f2ca8c4593df_initial_database.py).
    # Rien a faire ici : voir la note en tete de fichier.
    pass


def downgrade() -> None:
    # No-op symetrique : ces tables appartiennent au cycle de vie de la
    # migration initiale, pas a celle-ci.
    pass
