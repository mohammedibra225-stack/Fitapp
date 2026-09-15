"""fix meal_photo_analyses.image_url : doit etre nullable (V1 ne persiste pas la photo)

La toute premiere migration (f2ca8c4593df_initial_database.py) avait cree
cette colonne en NOT NULL. Le modele (app/models/ai.py) et la migration
d8e1f2a3b4c5 la declarent nullable, mais editer un fichier de migration
deja applique ne change pas retroactivement la contrainte en base :
il faut un ALTER COLUMN explicite.

Revision ID: e1a2b3c4d5f6
Revises: d8e1f2a3b4c5
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, None] = 'd8e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'meal_photo_analyses',
        'image_url',
        existing_type=sa.String(length=500),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'meal_photo_analyses',
        'image_url',
        existing_type=sa.String(length=500),
        nullable=False,
    )
