"""add missing exercise_translations.instructions column

Revision ID: c2a4b6d8e1f3
Revises: b1f3a9d2c8e4
Create Date: 2026-09-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a4b6d8e1f3'
down_revision: Union[str, None] = 'b1f3a9d2c8e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Oublie lors de b1f3a9d2c8e4 : le modele ExerciseTranslation a un
    # champ 'instructions' (module Sport, partie 3) qui n'avait pas ete
    # ajoute a la migration precedente.
    op.add_column(
        'exercise_translations',
        sa.Column('instructions', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('exercise_translations', 'instructions')
