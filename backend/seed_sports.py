

from app.database.connection import SessionLocal
from app.models.enums import DifficultyLevel, TrainingType
from app.models.sport import Sport, SportTranslation
from app.models.training import Exercise, ExerciseTranslation
from app.services.exercises_catalog import EXERCISES_CATALOG
from app.services.program_exercises_i18n import EXERCISE_I18N

# ============================================================
# SPORTS
# ============================================================

SPORTS = [
    {
        "slug": "musculation",
        "translations": {
            "fr": "Musculation",
            "en": "Strength training",
            "es": "Musculación",
            "ar": "تمارين القوة",
        },
    },
    {
        "slug": "course",
        "translations": {
            "fr": "Course à pied",
            "en": "Running",
            "es": "Running",
            "ar": "الجري",
        },
    },
    {
        "slug": "football",
        "translations": {
            "fr": "Football",
            "en": "Football",
            "es": "Fútbol",
            "ar": "كرة القدم",
        },
    },
    {
        "slug": "basketball",
        "translations": {
            "fr": "Basketball",
            "en": "Basketball",
            "es": "Baloncesto",
            "ar": "كرة السلة",
        },
    },
    {
        "slug": "cyclisme",
        "translations": {
            "fr": "Cyclisme",
            "en": "Cycling",
            "es": "Ciclismo",
            "ar": "ركوب الدراجات",
        },
    },
    {
        "slug": "natation",
        "translations": {
            "fr": "Natation",
            "en": "Swimming",
            "es": "Natación",
            "ar": "السباحة",
        },
    },
    {
        "slug": "boxe",
        "translations": {
            "fr": "Boxe",
            "en": "Boxing",
            "es": "Boxeo",
            "ar": "الملاكمة",
        },
    },
    {
        "slug": "fitness",
        "translations": {
            "fr": "Fitness",
            "en": "Fitness",
            "es": "Fitness",
            "ar": "اللياقة البدنية",
        },
    },
    {
        "slug": "cardio",
        "translations": {
            "fr": "Cardio",
            "en": "Cardio",
            "es": "Cardio",
            "ar": "تمارين الكارديو",
        },
    },
    {
        "slug": "arts_martiaux",
        "translations": {
            "fr": "Sports de combat",
            "en": "Combat sports",
            "es": "Deportes de combate",
            "ar": "الرياضات القتالية",
        },
    },
]

EXERCISES = EXERCISES_CATALOG


def seed_sports():

    db = SessionLocal()

    created_sports = 0
    updated_sports = 0
    created_sport_translations = 0
    updated_sport_translations = 0
    created_exercises = 0
    updated_exercises = 0
    created_exercise_translations = 0
    updated_exercise_translations = 0

    try:

        # ============================================================
        # 1. SPORTS
        # ============================================================

        sports_by_slug = {}

        for data in SPORTS:

            sport = (
                db.query(Sport)
                .filter(Sport.slug == data["slug"])
                .first()
            )

            if sport is None:
                sport = Sport(slug=data["slug"])
                db.add(sport)
                db.flush()
                created_sports += 1
            else:
                updated_sports += 1

            sports_by_slug[data["slug"]] = sport

            for language_code, name in data["translations"].items():

                translation = (
                    db.query(SportTranslation)
                    .filter(
                        SportTranslation.sport_id == sport.id,
                        SportTranslation.language_code == language_code,
                    )
                    .first()
                )

                if translation is None:
                    db.add(
                        SportTranslation(
                            sport_id=sport.id,
                            language_code=language_code,
                            name=name,
                        )
                    )
                    created_sport_translations += 1
                else:
                    translation.name = name
                    updated_sport_translations += 1

        db.flush()

        # ============================================================
        # 2. EXERCICES
        # ============================================================

        for data in EXERCISES:

            exercise = (
                db.query(Exercise)
                .filter(Exercise.slug == data["slug"])
                .first()
            )

            sport = (
                sports_by_slug.get(data["sport_slug"])
                if data.get("sport_slug")
                else None
            )

            if exercise is None:
                exercise = Exercise(slug=data["slug"])
                db.add(exercise)
                created_exercises += 1
            else:
                updated_exercises += 1

            exercise.sport_id = sport.id if sport else None
            exercise.category = data.get("category")
            exercise.equipment = data.get("equipment")
            exercise.training_types = [t for t in data.get("training_types", [])] or None
            exercise.difficulty = data.get("difficulty")
            exercise.is_active = True

            db.flush()

            # Dictionnaire complet de traductions (fusion du catalogue et du dictionnaire 4 langues)
            combined_translations = dict(data.get("translations", {}))
            if data["slug"] in EXERCISE_I18N:
                for lang_k, (n, d) in EXERCISE_I18N[data["slug"]].items():
                    combined_translations[lang_k] = {"name": n, "description": d}

            for language_code, content in combined_translations.items():

                translation = (
                    db.query(ExerciseTranslation)
                    .filter(
                        ExerciseTranslation.exercise_id == exercise.id,
                        ExerciseTranslation.language_code == language_code,
                    )
                    .first()
                )

                if translation is None:
                    db.add(
                        ExerciseTranslation(
                            exercise_id=exercise.id,
                            language_code=language_code,
                            name=content["name"],
                            description=content.get("description"),
                        )
                    )
                    created_exercise_translations += 1
                else:
                    translation.name = content["name"]
                    translation.description = content.get("description")
                    updated_exercise_translations += 1

        db.commit()

        print("=" * 60)
        print("SEED SPORTS TERMINE")
        print("=" * 60)
        print(f"Sports créés               : {created_sports}")
        print(f"Sports mis à jour          : {updated_sports}")
        print(f"Traductions sport créées   : {created_sport_translations}")
        print(f"Traductions sport màj      : {updated_sport_translations}")
        print(f"Exercices créés            : {created_exercises}")
        print(f"Exercices mis à jour       : {updated_exercises}")
        print(f"Traductions exercice créées: {created_exercise_translations}")
        print(f"Traductions exercice màj   : {updated_exercise_translations}")
        print("=" * 60)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_sports()
