"""
Point d'entree unique des modeles.

CRITIQUE pour Alembic : `env.py` importe `app.models` (ce fichier) afin
que tous les modeles soient enregistres sur `Base.metadata` avant tout
`alembic revision --autogenerate`. Tout nouveau fichier de modele doit
etre importe ici, sinon Alembic ne le verra jamais.
"""

from app.database.base import Base  # noqa: F401

# --- Utilisateur / profil ---
from app.models.user import User  # noqa: F401
from app.models.profile import Profile, BodyMeasurement  # noqa: F401

# --- Sports ---
from app.models.sport import Sport, SportTranslation, UserSport  # noqa: F401
from app.models.goals import Goal, GoalTranslation, SportGoalMatrix  # noqa: F401
from app.models.equipment import (  # noqa: F401
    Equipment,
    EquipmentTranslation,
    Environment,
    EnvironmentTranslation,
    SportEquipment,
    SportEnvironment,
)
from app.models.training_constraints import TrainingConstraint  # noqa: F401
from app.models.training_preferences import TrainingPreference  # noqa: F401

# --- Nutrition ---
from app.models.food import Food, FoodTranslation, FoodPrice  # noqa: F401
from app.models.meal import Meal, MealItem  # noqa: F401
from app.models.meal_plan import (  # noqa: F401
    MealPlan,
    MealPlanDay,
    MealPlanMeal,
    MealPlanMealItem,
)
from app.models.hydration import WaterLog  # noqa: F401
from app.models.inventory import Inventory, InventoryItem  # noqa: F401
from app.models.lifestyle import LifestyleProfile, DailyActivityLog  # noqa: F401

# --- Recettes ---
from app.models.recipe import (  # noqa: F401
    Recipe,
    RecipeTranslation,
    RecipeIngredient,
    RecipeStep,
    RecipeStepTranslation,
    RecipeVideo,
)

# --- Entrainement ---
from app.models.training import (  # noqa: F401
    Exercise,
    ExerciseTranslation,
    TrainingProgram,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)
from app.models.training_log import (  # noqa: F401
    WorkoutLog,
    WorkoutLogExercise,
    WorkoutLogSet,
    PersonalRecord,
)

# --- Recuperation ---
from app.models.recovery import SleepLog  # noqa: F401

# --- IA ---
from app.models.ai import (  # noqa: F401
    MealPhotoAnalysis,
    MealPhotoAnalysisItem,
    Conversation,
    Message,
)

# --- Notifications ---
from app.models.notification import NotificationSetting, NotificationLog  # noqa: F401

# --- Audit ---
from app.models.audit import AuditLog  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Profile",
    "BodyMeasurement",
    "Sport",
    "SportTranslation",
    "UserSport",
    "Goal",
    "GoalTranslation",
    "SportGoalMatrix",
    "Equipment",
    "EquipmentTranslation",
    "Environment",
    "EnvironmentTranslation",
    "SportEquipment",
    "SportEnvironment",
    "TrainingConstraint",
    "TrainingPreference",
    "Food",
    "FoodTranslation",
    "FoodPrice",
    "Meal",
    "MealItem",
    "MealPlan",
    "MealPlanDay",
    "MealPlanMeal",
    "MealPlanMealItem",
    "WaterLog",
    "Inventory",
    "InventoryItem",
    "LifestyleProfile",
    "DailyActivityLog",
    "Recipe",
    "RecipeTranslation",
    "RecipeIngredient",
    "RecipeStep",
    "RecipeStepTranslation",
    "RecipeVideo",
    "Exercise",
    "ExerciseTranslation",
    "TrainingProgram",
    "Workout",
    "WorkoutExercise",
    "WorkoutSet",
    "WorkoutLog",
    "WorkoutLogExercise",
    "WorkoutLogSet",
    "PersonalRecord",
    "SleepLog",
    "MealPhotoAnalysis",
    "MealPhotoAnalysisItem",
    "Conversation",
    "Message",
    "NotificationSetting",
    "NotificationLog",
    "AuditLog",
]
