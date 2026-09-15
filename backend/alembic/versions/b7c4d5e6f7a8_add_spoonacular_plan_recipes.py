"""Store Spoonacular recipes in meal plan meals."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c4d5e6f7a8"
down_revision: Union[str, None] = "9a3f1d2c4e5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meal_plan_meals", sa.Column("spoonacular_recipe_id", sa.Integer(), nullable=True))
    op.add_column("meal_plan_meals", sa.Column("spoonacular_recipe_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("meal_plan_meals", "spoonacular_recipe_data")
    op.drop_column("meal_plan_meals", "spoonacular_recipe_id")