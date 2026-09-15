"""Complete notification settings and notification categories."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a3f1d2c4e5b"
down_revision: Union[str, None] = "7e79087d273c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_NOTIFICATION_VALUES = (
    "RECOVERY_REMINDER",
    "DAILY_GOAL",
    "MEAL_PLAN",
    "PROGRESS_ALERT",
    "CUSTOM",
)


def upgrade() -> None:
    for enum_name in ("notification_type", "notification_log_type"):
        for value in NEW_NOTIFICATION_VALUES:
            op.execute(
                sa.text(
                    f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"
                )
            )

    op.add_column(
        "notification_settings",
        sa.Column("days_of_week", sa.JSON(), nullable=True),
    )
    op.add_column(
        "notification_settings",
        sa.Column("title", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "notification_settings",
        sa.Column("body", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE notification_settings "
        "SET days_of_week = '[0,1,2,3,4,5,6]'::json "
        "WHERE days_of_week IS NULL"
    )
    op.alter_column("notification_settings", "days_of_week", nullable=False)


def downgrade() -> None:
    op.drop_column("notification_settings", "body")
    op.drop_column("notification_settings", "title")
    op.drop_column("notification_settings", "days_of_week")
    # PostgreSQL does not support removing enum values safely in-place.
