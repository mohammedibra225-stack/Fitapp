from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment, EquipmentTranslation, Environment, EnvironmentTranslation, SportEquipment, SportEnvironment
from app.models.sport import Sport
from app.services.equipment_seed import ENVIRONMENT, EQUIPMENT


def seed_equipment_and_environments(db: Session) -> dict:
    created_equipment = 0
    created_environments = 0
    created_sport_equipment = 0
    created_sport_environment = 0

    for item in EQUIPMENT:
        equipment = db.execute(select(Equipment).where(Equipment.slug == item["slug"])).scalar_one_or_none()
        if equipment is None:
            equipment = Equipment(slug=item["slug"], category=item["category"], is_active=True)
            db.add(equipment)
            db.flush()
            created_equipment += 1

        for language_code, payload in item["translations"].items():
            existing = db.execute(
                select(EquipmentTranslation).where(
                    EquipmentTranslation.equipment_id == equipment.id,
                    EquipmentTranslation.language_code == language_code,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    EquipmentTranslation(
                        equipment_id=equipment.id,
                        language_code=language_code,
                        name=payload["name"],
                        description=payload["description"],
                    )
                )

    for item in ENVIRONMENT:
        environment = db.execute(select(Environment).where(Environment.slug == item["slug"])).scalar_one_or_none()
        if environment is None:
            environment = Environment(slug=item["slug"], category=item["category"], is_active=True)
            db.add(environment)
            db.flush()
            created_environments += 1

        for language_code, payload in item["translations"].items():
            existing = db.execute(
                select(EnvironmentTranslation).where(
                    EnvironmentTranslation.environment_id == environment.id,
                    EnvironmentTranslation.language_code == language_code,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    EnvironmentTranslation(
                        environment_id=environment.id,
                        language_code=language_code,
                        name=payload["name"],
                        description=payload["description"],
                    )
                )

    # sport -> equipment mapping basics
    sport_mappings = {
        "musculation": ["bodyweight", "dumbbells", "barbell", "bench", "rack", "pull_up_bar"],
        "course": ["bodyweight", "treadmill", "jump_rope", "running_shoes"],
        "football": ["football", "bodyweight", "jump_rope"],
        "basketball": ["basketball", "bodyweight", "jump_rope"],
        "cyclisme": ["bike", "stationary_bike", "bodyweight"],
        "natation": ["swimming_pool", "bodyweight", "resistance_band"],
        "boxe": ["boxing_bag", "gloves", "jump_rope", "bodyweight"],
        "fitness": ["bodyweight", "dumbbells", "mat", "resistance_band"],
        "cardio": ["bodyweight", "jump_rope", "treadmill", "elliptical"],
        "arts_martiaux": ["mat", "bodyweight", "boxing_bag", "resistance_band"],
    }

    sport_environment_map = {
        "musculation": ["home", "gym"],
        "course": ["outdoor", "track", "road", "trail", "home"],
        "football": ["football_field", "stadium", "outdoor"],
        "basketball": ["basketball_court", "outdoor", "gym"],
        "cyclisme": ["road", "trail", "outdoor"],
        "natation": ["pool"],
        "boxe": ["combat_gym", "home", "gym"],
        "fitness": ["home", "gym"],
        "cardio": ["home", "gym", "outdoor"],
        "arts_martiaux": ["combat_gym", "home", "gym"],
    }

    for sport_slug, equipment_slugs in sport_mappings.items():
        sport = db.execute(select(Sport).where(Sport.slug == sport_slug)).scalar_one_or_none()
        if sport is None:
            continue

        for equipment_slug in equipment_slugs:
            equipment = db.execute(select(Equipment).where(Equipment.slug == equipment_slug)).scalar_one_or_none()
            if equipment is None:
                continue
            existing = db.execute(
                select(SportEquipment).where(
                    SportEquipment.sport_id == sport.id,
                    SportEquipment.equipment_id == equipment.id,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    SportEquipment(
                        sport_id=sport.id,
                        equipment_id=equipment.id,
                        required=equipment_slug in {"football", "basketball", "swimming_pool", "boxing_bag", "gloves", "bike", "treadmill"},
                        priority=1,
                    )
                )
                created_sport_equipment += 1

    for sport_slug, environment_slugs in sport_environment_map.items():
        sport = db.execute(select(Sport).where(Sport.slug == sport_slug)).scalar_one_or_none()
        if sport is None:
            continue

        for environment_slug in environment_slugs:
            environment = db.execute(select(Environment).where(Environment.slug == environment_slug)).scalar_one_or_none()
            if environment is None:
                continue
            existing = db.execute(
                select(SportEnvironment).where(
                    SportEnvironment.sport_id == sport.id,
                    SportEnvironment.environment_id == environment.id,
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    SportEnvironment(
                        sport_id=sport.id,
                        environment_id=environment.id,
                        supported=True,
                        priority=1,
                    )
                )
                created_sport_environment += 1

    db.commit()
    return {
        "created_equipment": created_equipment,
        "created_environments": created_environments,
        "created_sport_equipment": created_sport_equipment,
        "created_sport_environment": created_sport_environment,
    }
