
import enum


class Sex(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ActivityLevel(str, enum.Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class GoalCategory(str, enum.Enum):
    BODY_COMPOSITION = "body_composition"
    PERFORMANCE = "performance"
    FITNESS_HEALTH = "fitness_health"
    RECOVERY = "recovery"


class GoalType(str, enum.Enum):
    WEIGHT_LOSS = "weight_loss"
    MAINTENANCE = "maintenance"
    MUSCLE_GAIN = "muscle_gain"
    PERFORMANCE = "performance"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    GENERAL_HEALTH = "general_health"
    BODY_RECOMPOSITION = "body_recomposition"


class SportLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    PROFESSIONAL = "professional"

class SportGoal(str, enum.Enum):
    MUSCLE_GAIN = "muscle_gain"
    STRENGTH = "strength"
    FAT_LOSS = "fat_loss"
    ENDURANCE = "endurance"
    PERFORMANCE = "performance"
    SPEED = "speed"
    POWER = "power"
    GENERAL_FITNESS = "general_fitness"
    HEALTH = "health"

class UnitSystem(str, enum.Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class HalalStatus(str, enum.Enum):
    """Statut halal d'un aliment, base sur les donnees reellement
    fournies par la source (ex: Open Food Facts). Ne jamais deduire
    'halal' a partir du seul nom du produit : par defaut UNKNOWN.
    """

    HALAL = "halal"
    NOT_HALAL = "not_halal"
    UNKNOWN = "unknown"


class FoodDataSource(str, enum.Enum):
    """Origine d'un Food ou d'un FoodPrice (regle 5 : cache/sync)."""

    MANUAL = "manual"
    OPEN_FOOD_FACTS = "open_food_facts"
    OPEN_PRICES = "open_prices"


class RecipeDataSource(str, enum.Enum):
    """Origine d'une Recipe : saisie manuelle (seed) ou import externe.
    Distincte de FoodDataSource pour ne pas mélanger aliments et recettes,
    et rester extensible a d'autres sources de recettes plus tard."""

    MANUAL = "manual"
    WIKIBOOKS_COOKBOOK = "wikibooks_cookbook"


class IngredientMatchStatus(str, enum.Enum):
    """Statut du rapprochement d'un ingredient de recette importee avec
    notre Food DB (regle : ne jamais associer un mauvais aliment)."""

    MATCHED = "matched"
    UNMAPPED = "unmapped"


class RecipeNutritionStatus(str, enum.Enum):
    """Fiabilite du calcul nutritionnel d'une recette (regle 6/26).
    Ne jamais presenter une nutrition partielle comme complete :
    COMPLETE   -> tous les ingredients sont mappes et convertibles
    PARTIAL    -> au moins un ingredient a contribue, mais au moins un
                  autre est unmapped ou dans une unite non convertible
                  (tbsp/tsp/cup/serving, ou piece sans unit_weight_g)
    UNKNOWN    -> aucun ingredient n'a pu contribuer au calcul
    """

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class RecipeCostStatus(str, enum.Enum):
    """Fiabilite du cout estime d'une recette (regle 8 : jamais 0 DA
    pour representer un prix inconnu).
    KNOWN   -> tous les ingredients ont un prix DZD actif connu
    PARTIAL -> au moins un ingredient a un prix connu, au moins un autre non
    UNKNOWN -> aucun prix connu pour aucun ingredient
    """

    KNOWN = "known"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class MeasurementUnit(str, enum.Enum):
    """Unite pour une quantite d'aliment / ingredient."""

    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    PIECE = "piece"
    TBSP = "tbsp"
    TSP = "tsp"
    CUP = "cup"
    SERVING = "serving"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InventoryType(str, enum.Enum):
    FRIDGE = "fridge"
    FREEZER = "freezer"
    PANTRY = "pantry"


class RecordType(str, enum.Enum):
    MAX_WEIGHT = "max_weight"
    MAX_REPS = "max_reps"
    ONE_REP_MAX = "one_rep_max"
    BEST_TIME = "best_time"
    BEST_DISTANCE = "best_distance"
    MAX_DURATION = "max_duration"


class BodyMetricType(str, enum.Enum):
    """Type de mesure historisee pour le suivi de progression (regle 18)."""

    WEIGHT = "weight"
    HEIGHT = "height"
    BODY_FAT_PERCENTAGE = "body_fat_percentage"
    CHEST = "chest"
    WAIST = "waist"
    HIPS = "hips"
    ARM = "arm"
    THIGH = "thigh"
    CALF = "calf"
    NECK = "neck"


class SleepQuality(str, enum.Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    CORRECTED = "corrected"
    FAILED = "failed"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class NotificationType(str, enum.Enum):
    MEAL_REMINDER = "meal_reminder"
    WATER_REMINDER = "water_reminder"
    TRAINING_REMINDER = "training_reminder"
    RECOVERY_REMINDER = "recovery_reminder"
    DAILY_GOAL = "daily_goal"
    MEAL_PLAN = "meal_plan"
    PROGRESS_ALERT = "progress_alert"
    CUSTOM = "custom"
    GENERAL = "general"


class VideoPlatform(str, enum.Enum):
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    INTERNAL = "internal"


class TrainingType(str, enum.Enum):
    """Type d'entrainement d'une seance/exercice (module Sport, partie 2).
    Enum Python fixe (choix valide) plutot qu'une table extensible comme
    Sport : la liste des types d'effort est stable et connue a l'avance.
    """

    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    CARDIO = "cardio"
    INTERVAL = "interval"
    SPEED = "speed"
    AGILITY = "agility"
    POWER = "power"
    MOBILITY = "mobility"
    TECHNIQUE = "technique"
    RECOVERY = "recovery"
    MIXED = "mixed"


class LifestyleGoal(str, enum.Enum):
    """Objectif d'un utilisateur non-sportif ou complementaire au sport
    (module Sport, partie 11). Distinct de GoalType (nutrition/entrainement)
    pour ne jamais forcer un objectif sportif a un utilisateur qui n'en a pas.
    """

    EAT_HEALTHIER = "eat_healthier"
    MAINTAIN_WEIGHT = "maintain_weight"
    LOSE_WEIGHT = "lose_weight"
    HEALTHY_LIFESTYLE = "healthy_lifestyle"
    BETTER_HABITS = "better_habits"
    MORE_ENERGY = "more_energy"
    BETTER_HYDRATION = "better_hydration"
    BETTER_SLEEP = "better_sleep"


class RecoveryLevel(str, enum.Enum):
    """Classification du Recovery Score (module Sport, partie 10).
    NORMAL      -> 80-100
    MODERATE    -> 60-79
    REDUCE      -> 40-59 (reduire l'intensite)
    REST_NEEDED -> 0-39 (recuperation / repos)
    """

    NORMAL = "normal"
    MODERATE = "moderate"
    REDUCE = "reduce"
    REST_NEEDED = "rest_needed"


class ActivityDataSource(str, enum.Enum):
    """Origine d'un DailyActivityLog (pas, marche...)."""

    MANUAL = "manual"
    DEVICE = "device"
