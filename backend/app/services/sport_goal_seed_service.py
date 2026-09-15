from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goals import Goal, GoalTranslation, SportGoalMatrix
from app.models.sport import Sport
from app.services.goal_seed import GOAL_SEED
from app.services.sport_goal_matrix_seed import SPORT_GOAL_MATRIX


def seed_goals_and_sport_goal_matrix(db: Session) -> dict:
    created_goals = 0
    created_mappings = 0

    for item in GOAL_SEED:
        goal = db.execute(select(Goal).where(Goal.slug == item["slug"])).scalar_one_or_none()
        if goal is None:
            goal = Goal(
                slug=item["slug"],
                category=item["category"],
                is_active=True,
            )
            db.add(goal)
            db.flush()
            created_goals += 1

        for language_code, payload in item["translations"].items():
            existing_translation = db.execute(
                select(GoalTranslation).where(
                    GoalTranslation.goal_id == goal.id,
                    GoalTranslation.language_code == language_code,
                )
            ).scalar_one_or_none()
            if existing_translation is None:
                db.add(
                    GoalTranslation(
                        goal_id=goal.id,
                        language_code=language_code,
                        name=payload["name"],
                        description=payload["description"],
                    )
                )

    for sport_slug, objectives in SPORT_GOAL_MATRIX.items():
        sport = db.execute(select(Sport).where(Sport.slug == sport_slug)).scalar_one_or_none()
        if sport is None:
            continue

        for objective_slug, relevance in objectives.items():
            goal = db.execute(select(Goal).where(Goal.slug == objective_slug)).scalar_one_or_none()
            if goal is None:
                continue

            existing = db.execute(
                select(SportGoalMatrix).where(
                    SportGoalMatrix.sport_id == sport.id,
                    SportGoalMatrix.goal_id == goal.id,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    SportGoalMatrix(
                        sport_id=sport.id,
                        goal_id=goal.id,
                        relevance_score=relevance,
                        priority=int(relevance * 100),
                        is_primary=relevance >= 0.9,
                    )
                )
                created_mappings += 1

    db.commit()
    return {
        "created_goals": created_goals,
        "created_mappings": created_mappings,
    }
