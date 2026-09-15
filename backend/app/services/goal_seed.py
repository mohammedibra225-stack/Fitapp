from app.models.enums import GoalCategory


GOAL_SEED = [
    {
        "slug": "muscle_gain",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Prise de masse", "description": "Augmenter la masse musculaire et la force."},
            "en": {"name": "Muscle gain", "description": "Increase muscle mass and strength."},
        },
    },
    {
        "slug": "hypertrophy",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Hypertrophie", "description": "Développement musculaire et volume."},
            "en": {"name": "Hypertrophy", "description": "Muscle growth and volume."},
        },
    },
    {
        "slug": "strength",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Force", "description": "Améliorer la force maximale."},
            "en": {"name": "Strength", "description": "Improve maximal strength."},
        },
    },
    {
        "slug": "fat_loss",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Minceur", "description": "Perdre du gras tout en préservant la masse."},
            "en": {"name": "Fat loss", "description": "Lose fat while preserving lean mass."},
        },
    },
    {
        "slug": "weight_loss",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Perte de poids", "description": "Réduire le poids corporel."},
            "en": {"name": "Weight loss", "description": "Reduce total body weight."},
        },
    },
    {
        "slug": "body_recomposition",
        "category": GoalCategory.BODY_COMPOSITION,
        "translations": {
            "fr": {"name": "Recomposition", "description": "Transformer le physique globalement."},
            "en": {"name": "Body recomposition", "description": "Improve body composition overall."},
        },
    },
    {
        "slug": "performance",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Performance", "description": "Améliorer la performance globale sportive."},
            "en": {"name": "Performance", "description": "Improve overall athletic performance."},
        },
    },
    {
        "slug": "speed",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Vitesse", "description": "Accélérer les déplacements et la cadence."},
            "en": {"name": "Speed", "description": "Improve movement speed and cadence."},
        },
    },
    {
        "slug": "acceleration",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Accélération", "description": "Optimiser la sortie de départ et l'accélération."},
            "en": {"name": "Acceleration", "description": "Improve starting acceleration and quickness."},
        },
    },
    {
        "slug": "agility",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Agilité", "description": "Améliorer la coordination et les changements de direction."},
            "en": {"name": "Agility", "description": "Improve coordination and directional changes."},
        },
    },
    {
        "slug": "power",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Puissance", "description": "Développer la force explosive."},
            "en": {"name": "Power", "description": "Develop explosive power."},
        },
    },
    {
        "slug": "endurance",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Endurance", "description": "Soutenir un effort plus longtemps."},
            "en": {"name": "Endurance", "description": "Sustain effort for longer durations."},
        },
    },
    {
        "slug": "aerobic_capacity",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Capacité aérobie", "description": "Améliorer la capacité d'effort continu."},
            "en": {"name": "Aerobic capacity", "description": "Improve continuous effort capacity."},
        },
    },
    {
        "slug": "anaerobic_capacity",
        "category": GoalCategory.PERFORMANCE,
        "translations": {
            "fr": {"name": "Capacité anaérobie", "description": "Gérer les efforts intenses courts."},
            "en": {"name": "Anaerobic capacity", "description": "Handle short high-intensity efforts."},
        },
    },
    {
        "slug": "general_fitness",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Fitness général", "description": "Améliorer l'état général de forme."},
            "en": {"name": "General fitness", "description": "Improve overall fitness."},
        },
    },
    {
        "slug": "healthy_lifestyle",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Mode de vie sain", "description": "Mieux intégrer l'activité physique dans la vie."},
            "en": {"name": "Healthy lifestyle", "description": "Integrate physical activity into daily life."},
        },
    },
    {
        "slug": "mobility",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Mobilité", "description": "Améliorer les amplitudes et la mobilité."},
            "en": {"name": "Mobility", "description": "Improve range of motion."},
        },
    },
    {
        "slug": "flexibility",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Souplesse", "description": "Développer la souplesse générale."},
            "en": {"name": "Flexibility", "description": "Improve overall flexibility."},
        },
    },
    {
        "slug": "conditioning",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Conditionnement", "description": "Améliorer la forme cardio et la résistance."},
            "en": {"name": "Conditioning", "description": "Improve cardio and work capacity."},
        },
    },
    {
        "slug": "daily_activity",
        "category": GoalCategory.FITNESS_HEALTH,
        "translations": {
            "fr": {"name": "Activité quotidienne", "description": "Augmenter l'activité globale de la journée."},
            "en": {"name": "Daily activity", "description": "Increase daily movement and activity."},
        },
    },
    {
        "slug": "recovery",
        "category": GoalCategory.RECOVERY,
        "translations": {
            "fr": {"name": "Récupération", "description": "Optimiser la récupération et le repos."},
            "en": {"name": "Recovery", "description": "Optimize rest and recovery."},
        },
    },
    {
        "slug": "active_recovery",
        "category": GoalCategory.RECOVERY,
        "translations": {
            "fr": {"name": "Récupération active", "description": "Maintenir l'activité sans surcharge."},
            "en": {"name": "Active recovery", "description": "Stay active while reducing stress."},
        },
    },
    {
        "slug": "deload",
        "category": GoalCategory.RECOVERY,
        "translations": {
            "fr": {"name": "Deload", "description": "Réduire la charge pour récupérer."},
            "en": {"name": "Deload", "description": "Reduce training stress to recover."},
        },
    },
    {
        "slug": "return_to_training",
        "category": GoalCategory.RECOVERY,
        "translations": {
            "fr": {"name": "Retour à l'entraînement", "description": "Reprendre progressivement l'effort."},
            "en": {"name": "Return to training", "description": "Resume training gradually."},
        },
    },
]
