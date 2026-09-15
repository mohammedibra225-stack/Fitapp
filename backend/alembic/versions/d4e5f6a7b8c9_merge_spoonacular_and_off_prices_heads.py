"""merge spoonacular and off/open prices heads

Revision ID: d4e5f6a7b8c9
Revises: b7c4d5e6f7a8, a1b2c3d4e5f6
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = ('b7c4d5e6f7a8', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pure merge migration - no schema changes.
    pass


def downgrade() -> None:
    # Pure merge migration - no schema changes.
    pass
