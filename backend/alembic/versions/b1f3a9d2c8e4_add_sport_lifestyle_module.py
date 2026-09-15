"""add sport/lifestyle module (training types, lifestyle profile, daily activity)

Revision ID: b1f3a9d2c8e4
Revises: a7c2e4f1b3d9
Create Date: 2026-09-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1f3a9d2c8e4'
down_revision: Union[str, None] = 'a7c2e4f1b3d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRAINING_TYPE_VALUES = (
    'strength', 'hypertrophy', 'endurance', 'cardio', 'interval',
    'speed', 'agility', 'power', 'mobility', 'technique', 'recovery', 'mixed',
)
DIFFICULTY_VALUES = ('easy', 'medium', 'hard')


def upgrade() -> None:
    bind = op.get_bind()

    # --- Nouveaux types Postgres (un type par table/colonne, meme
    # convention que recipe_halal_status vs halal_status : cf. migration
    # a7c2e4f1b3d9) ---
    exercise_training_type = postgresql.ENUM(
        *TRAINING_TYPE_VALUES, name='training_type', create_type=False
    )
    exercise_training_type.create(bind, checkfirst=True)

    workout_training_type = postgresql.ENUM(
        *TRAINING_TYPE_VALUES, name='workout_training_type', create_type=False
    )
    workout_training_type.create(bind, checkfirst=True)

    exercise_difficulty = postgresql.ENUM(
        *DIFFICULTY_VALUES, name='exercise_difficulty', create_type=False
    )
    exercise_difficulty.create(bind, checkfirst=True)

    workout_difficulty = postgresql.ENUM(
        *DIFFICULTY_VALUES, name='workout_difficulty', create_type=False
    )
    workout_difficulty.create(bind, checkfirst=True)

    lifestyle_goal = postgresql.ENUM(
        'eat_healthier', 'maintain_weight', 'lose_weight', 'healthy_lifestyle',
        'better_habits', 'more_energy', 'better_hydration', 'better_sleep',
        name='lifestyle_goal', create_type=False,
    )
    lifestyle_goal.create(bind, checkfirst=True)

    activity_data_source = postgresql.ENUM(
        'manual', 'device', name='activity_data_source', create_type=False
    )
    activity_data_source.create(bind, checkfirst=True)

    # --- exercises : types d'entrainement + difficulte + actif ---
    op.add_column(
        'exercises',
        sa.Column(
            'training_types',
            postgresql.ARRAY(exercise_training_type),
            nullable=True,
        ),
    )
    op.add_column('exercises', sa.Column('difficulty', exercise_difficulty, nullable=True))
    op.add_column(
        'exercises',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )

    # --- workouts : sport, type, difficulte, duree, intensite, calories ---
    op.add_column('workouts', sa.Column('sport_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_workouts_sport_id', 'workouts', 'sports', ['sport_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index(op.f('ix_workouts_sport_id'), 'workouts', ['sport_id'], unique=False)

    op.add_column('workouts', sa.Column('training_type', workout_training_type, nullable=True))
    op.add_column('workouts', sa.Column('difficulty', workout_difficulty, nullable=True))
    op.add_column('workouts', sa.Column('planned_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('workouts', sa.Column('target_rpe', sa.Numeric(3, 1), nullable=True))
    op.add_column('workouts', sa.Column('estimated_calories_kcal', sa.Numeric(7, 2), nullable=True))

    # --- workout_sets : intensite ciblee par serie ---
    op.add_column('workout_sets', sa.Column('target_rpe', sa.Numeric(3, 1), nullable=True))

    # --- lifestyle_profiles ---
    op.create_table(
        'lifestyle_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('lifestyle_goal', lifestyle_goal, nullable=True),
        sa.Column('daily_steps_target', sa.Integer(), nullable=True),
        sa.Column('sleep_target_minutes', sa.Integer(), nullable=True),
        sa.Column('hydration_target_ml', sa.Integer(), nullable=True),
        sa.Column(
            'wants_activity_suggestions', sa.Boolean(), nullable=False, server_default='true'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_lifestyle_profiles_user_id'), 'lifestyle_profiles', ['user_id'], unique=True
    )

    # --- daily_activity_logs ---
    op.create_table(
        'daily_activity_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('log_date', sa.Date(), nullable=False),
        sa.Column('steps', sa.Integer(), nullable=True),
        sa.Column('walking_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('distance_m', sa.Numeric(8, 2), nullable=True),
        sa.Column('active_minutes', sa.SmallInteger(), nullable=True),
        sa.Column(
            'source', activity_data_source, nullable=False, server_default='manual'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'log_date', name='uq_daily_activity_user_date'),
    )
    op.create_index(
        op.f('ix_daily_activity_logs_user_id'), 'daily_activity_logs', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_daily_activity_logs_log_date'), 'daily_activity_logs', ['log_date'], unique=False
    )
    op.create_index(
        'ix_daily_activity_user_date', 'daily_activity_logs', ['user_id', 'log_date'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_daily_activity_user_date', table_name='daily_activity_logs')
    op.drop_index(op.f('ix_daily_activity_logs_log_date'), table_name='daily_activity_logs')
    op.drop_index(op.f('ix_daily_activity_logs_user_id'), table_name='daily_activity_logs')
    op.drop_table('daily_activity_logs')

    op.drop_index(op.f('ix_lifestyle_profiles_user_id'), table_name='lifestyle_profiles')
    op.drop_table('lifestyle_profiles')

    op.drop_column('workout_sets', 'target_rpe')

    op.drop_column('workouts', 'estimated_calories_kcal')
    op.drop_column('workouts', 'target_rpe')
    op.drop_column('workouts', 'planned_duration_minutes')
    op.drop_column('workouts', 'difficulty')
    op.drop_column('workouts', 'training_type')
    op.drop_index(op.f('ix_workouts_sport_id'), table_name='workouts')
    op.drop_constraint('fk_workouts_sport_id', 'workouts', type_='foreignkey')
    op.drop_column('workouts', 'sport_id')

    op.drop_column('exercises', 'is_active')
    op.drop_column('exercises', 'difficulty')
    op.drop_column('exercises', 'training_types')

    bind = op.get_bind()
    postgresql.ENUM(name='activity_data_source').drop(bind, checkfirst=True)
    postgresql.ENUM(name='lifestyle_goal').drop(bind, checkfirst=True)
    postgresql.ENUM(name='workout_difficulty').drop(bind, checkfirst=True)
    postgresql.ENUM(name='exercise_difficulty').drop(bind, checkfirst=True)
    postgresql.ENUM(name='workout_training_type').drop(bind, checkfirst=True)
    postgresql.ENUM(name='training_type').drop(bind, checkfirst=True)
