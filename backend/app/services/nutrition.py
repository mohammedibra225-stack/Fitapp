from app.models.enums import ActivityLevel, GoalType, Sex


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.20,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.90,
}


GOAL_CALORIE_ADJUSTMENTS = {
    GoalType.WEIGHT_LOSS: -0.15,
    GoalType.MAINTENANCE: 0.00,
    GoalType.MUSCLE_GAIN: 0.10,
    GoalType.PERFORMANCE: 0.05,
    GoalType.ENDURANCE: 0.05,
    GoalType.STRENGTH: 0.10,
    GoalType.GENERAL_HEALTH: 0.00,
    GoalType.BODY_RECOMPOSITION: -0.05,
}


# Protéines en grammes / kg de poids corporel
PROTEIN_PER_KG = {
    GoalType.WEIGHT_LOSS: 2.0,
    GoalType.MAINTENANCE: 1.6,
    GoalType.MUSCLE_GAIN: 2.0,
    GoalType.PERFORMANCE: 1.8,
    GoalType.ENDURANCE: 1.6,
    GoalType.STRENGTH: 1.8,
    GoalType.GENERAL_HEALTH: 1.4,
    GoalType.BODY_RECOMPOSITION: 2.0,
}


# Lipides en grammes / kg de poids corporel
FAT_PER_KG = {
    GoalType.WEIGHT_LOSS: 0.8,
    GoalType.MAINTENANCE: 0.9,
    GoalType.MUSCLE_GAIN: 0.9,
    GoalType.PERFORMANCE: 0.9,
    GoalType.ENDURANCE: 1.0,
    GoalType.STRENGTH: 0.9,
    GoalType.GENERAL_HEALTH: 1.0,
    GoalType.BODY_RECOMPOSITION: 0.9,
}


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
) -> float:

    if sex == Sex.MALE:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    elif sex == Sex.FEMALE:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    else:
        raise ValueError("Sex must be MALE or FEMALE")

    return round(bmr, 2)


def calculate_tdee(
    bmr: float,
    activity_level: ActivityLevel,
) -> float:

    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level)

    if multiplier is None:
        raise ValueError(
            f"Unsupported activity level: {activity_level}"
        )

    return round(bmr * multiplier, 2)


def calculate_daily_calories(
    tdee: float,
    goal: GoalType,
) -> float:

    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal)

    if adjustment is None:
        raise ValueError(
            f"Unsupported goal: {goal}"
        )

    calories = tdee * (1 + adjustment)

    return round(calories, 2)


def calculate_macros(
    weight_kg: float,
    daily_calories: float,
    goal: GoalType,
) -> dict:

    protein_per_kg = PROTEIN_PER_KG.get(goal)
    fat_per_kg = FAT_PER_KG.get(goal)

    if protein_per_kg is None:
        raise ValueError(
            f"Unsupported goal: {goal}"
        )

    if fat_per_kg is None:
        raise ValueError(
            f"Unsupported goal: {goal}"
        )

    # Protéines
    protein_g = weight_kg * protein_per_kg

    # Lipides
    fat_g = weight_kg * fat_per_kg

    # Calories provenant des protéines et lipides
    protein_calories = protein_g * 4
    fat_calories = fat_g * 9

    # Le reste des calories vient des glucides
    remaining_calories = (
        daily_calories
        - protein_calories
        - fat_calories
    )

    carbs_g = remaining_calories / 4

    # Sécurité : éviter une valeur négative
    if carbs_g < 0:
        carbs_g = 0

    return {
        "protein_g": round(protein_g, 2),
        "carbs_g": round(carbs_g, 2),
        "fat_g": round(fat_g, 2),
    }


def calculate_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
    activity_level: ActivityLevel,
    goal: GoalType,
) -> dict:

    bmr = calculate_bmr(
        weight_kg,
        height_cm,
        age,
        sex,
    )

    tdee = calculate_tdee(
        bmr,
        activity_level,
    )

    daily_calories = calculate_daily_calories(
        tdee,
        goal,
    )

    macros = calculate_macros(
        weight_kg,
        daily_calories,
        goal,
    )

    return {
        "bmr": bmr,
        "tdee": tdee,
        "daily_calories": daily_calories,
        "protein_g": macros["protein_g"],
        "carbs_g": macros["carbs_g"],
        "fat_g": macros["fat_g"],
    }