from app.models.enums import DifficultyLevel, TrainingType
from app.services.program_exercises import PROGRAM_EXERCISES_CATALOG

# Catalogue riche et diversifié d'exercices par sport et par type d'effort
EXERCISES_CATALOG = []
EXERCISES_CATALOG.extend([
    # ------------------------------------------------------------
    # MUSCULATION : PUSH / PULL / LEGS / FULL BODY / CORE
    # ------------------------------------------------------------
    {
        "slug": "squat",
        "sport_slug": "musculation",
        "category": "legs",
        "equipment": "barbell",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Squat", "description": "Flexion des jambes avec charge sur les épaules."},
            "en": {"name": "Squat", "description": "Leg flexion with a barbell on the shoulders."},
        },
    },
    {
        "slug": "developpe_couche",
        "sport_slug": "musculation",
        "category": "chest",
        "equipment": "barbell",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Développé couché", "description": "Poussée de la barre en position allongée."},
            "en": {"name": "Bench press", "description": "Barbell press performed lying down."},
        },
    },
    {
        "slug": "developpe_incline_halteres",
        "sport_slug": "musculation",
        "category": "chest",
        "equipment": "dumbbells",
        "training_types": [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Développé incliné haltères", "description": "Cible le haut des pectoraux et l'avant des épaules."},
            "en": {"name": "Incline dumbbell press", "description": "Targets upper chest and front delts."},
        },
    },
    {
        "slug": "souleve_de_terre",
        "sport_slug": "musculation",
        "category": "back",
        "equipment": "barbell",
        "training_types": [TrainingType.STRENGTH, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Soulevé de terre", "description": "Souleve la barre du sol jusqu'aux hanches."},
            "en": {"name": "Deadlift", "description": "Lifts the barbell from the floor to hip level."},
        },
    },
    {
        "slug": "traction",
        "sport_slug": "musculation",
        "category": "back",
        "equipment": "pull_up_bar",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Traction", "description": "Tire le corps vers une barre fixe."},
            "en": {"name": "Pull-up", "description": "Pulls the body up to a fixed bar."},
        },
    },
    {
        "slug": "rowing_barre",
        "sport_slug": "musculation",
        "category": "back",
        "equipment": "barbell",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Rowing barre", "description": "Tirage buste penché pour l'épaisseur du dos."},
            "en": {"name": "Barbell bent-over row", "description": "Bent-over pull for back thickness."},
        },
    },
    {
        "slug": "developpe_militaire",
        "sport_slug": "musculation",
        "category": "shoulders",
        "equipment": "barbell",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY, TrainingType.POWER],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Développé militaire", "description": "Poussée verticale au-dessus de la tête pour les épaules."},
            "en": {"name": "Overhead press", "description": "Vertical press overhead for shoulder development."},
        },
    },
    {
        "slug": "elevations_laterales",
        "sport_slug": "musculation",
        "category": "shoulders",
        "equipment": "dumbbells",
        "training_types": [TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Élévations latérales", "description": "Isolation du faisceau latéral des épaules."},
            "en": {"name": "Lateral raises", "description": "Isolation for the lateral deltoids."},
        },
    },
    {
        "slug": "dips",
        "sport_slug": "musculation",
        "category": "chest",
        "equipment": "dip_bar",
        "training_types": [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Dips", "description": "Répulsions aux barres parallèles pour triceps et pectoraux."},
            "en": {"name": "Dips", "description": "Parallel bar dips for triceps and chest."},
        },
    },
    {
        "slug": "fentes_halteres",
        "sport_slug": "musculation",
        "category": "legs",
        "equipment": "dumbbells",
        "training_types": [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Fentes marchées avec haltères", "description": "Travail unilatéral des quadriceps, fessiers et équilibre."},
            "en": {"name": "Walking dumbbell lunges", "description": "Unilateral work for quads, glutes, and stability."},
        },
    },
    {
        "slug": "presse_a_cuisses",
        "sport_slug": "musculation",
        "category": "legs",
        "equipment": "smith_machine",
        "training_types": [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Presse à cuisses", "description": "Volume intense sur les quadriceps en sécurité."},
            "en": {"name": "Leg press", "description": "Intense quad volume with stability."},
        },
    },
    {
        "slug": "leg_curl",
        "sport_slug": "musculation",
        "category": "legs",
        "equipment": "smith_machine",
        "training_types": [TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Leg curl ischio-jambiers", "description": "Isolation des ischio-jambiers pour l'équilibre musculaire."},
            "en": {"name": "Hamstring leg curl", "description": "Isolation for hamstrings balance."},
        },
    },
    {
        "slug": "curl_biceps_barre",
        "sport_slug": "musculation",
        "category": "arms",
        "equipment": "barbell",
        "training_types": [TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Curl biceps à la barre", "description": "Flexion des coudes pour le pic du biceps."},
            "en": {"name": "Barbell biceps curl", "description": "Elbow flexion for biceps peak."},
        },
    },
    {
        "slug": "extension_triceps_poulie",
        "sport_slug": "musculation",
        "category": "arms",
        "equipment": "cable_machine",
        "training_types": [TrainingType.HYPERTROPHY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Extension triceps à la poulie", "description": "Isolation triceps avec tension continue."},
            "en": {"name": "Cable triceps pushdown", "description": "Triceps isolation with continuous tension."},
        },
    },
    {
        "slug": "pompes",
        "sport_slug": "musculation",
        "category": "chest",
        "equipment": None,
        "training_types": [TrainingType.STRENGTH, TrainingType.ENDURANCE],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Pompes", "description": "Poussée du corps au sol, sans matériel."},
            "en": {"name": "Push-up", "description": "Bodyweight push performed on the floor."},
        },
    },
    {
        "slug": "gainage",
        "sport_slug": "musculation",
        "category": "core",
        "equipment": None,
        "training_types": [TrainingType.MOBILITY, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Gainage", "description": "Maintien statique en appui, sollicite la sangle abdominale."},
            "en": {"name": "Plank", "description": "Static hold that engages the core."},
        },
    },
])
EXERCISES_CATALOG.extend([
    # ------------------------------------------------------------
    # FOOTBALL : VITESSE, AGILITÉ, PUISSANCE, CONDITIONING, TECHNIQUE
    # ------------------------------------------------------------
    {
        "slug": "match_football",
        "sport_slug": "football",
        "category": "cardio",
        "equipment": "football",
        "training_types": [TrainingType.ENDURANCE, TrainingType.SPEED, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Match de football", "description": "Séance de jeu collectif en conditions réelles."},
            "en": {"name": "Football match", "description": "Team play session under match conditions."},
        },
    },
    {
        "slug": "sprints_navette_football",
        "sport_slug": "football",
        "category": "speed",
        "equipment": None,
        "training_types": [TrainingType.SPEED, TrainingType.INTERVAL, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sprints navettes 5-10-15m", "description": "Accélérations courtes et freinages répétés typiques des phases de jeu."},
            "en": {"name": "Shuttle sprints 5-10-15m", "description": "Short bursts and rapid decelerations typical of match play."},
        },
    },
    {
        "slug": "slalom_plots_agilite",
        "sport_slug": "football",
        "category": "agility",
        "equipment": "football",
        "training_types": [TrainingType.AGILITY, TrainingType.SPEED, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Slalom avec ballon entre les plots", "description": "Changements de direction rapides et conduite de balle précise."},
            "en": {"name": "Cone dribbling slalom", "description": "Rapid changes of direction and precise ball handling."},
        },
    },
    {
        "slug": "frappes_et_tirs_au_but",
        "sport_slug": "football",
        "category": "technique",
        "equipment": "football",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.POWER],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Frappes et finition au but", "description": "Répétition de tirs variés (placé, puissant, reprise de volée)."},
            "en": {"name": "Finishing and shooting drills", "description": "Varied shooting repetitions (placed, power, volleys)."},
        },
    },
    {
        "slug": "passes_courtes_une_touche",
        "sport_slug": "football",
        "category": "technique",
        "equipment": "football",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Passes courtes et une touche (Rondo)", "description": "Circulation rapide du ballon et vivacité d'appui."},
            "en": {"name": "One-touch passing rondo", "description": "Fast ball circulation and quick footwork."},
        },
    },
    {
        "slug": "bip_test_intermittent",
        "sport_slug": "football",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.INTERVAL, TrainingType.ENDURANCE],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Course intermittente fractionnée 15-15", "description": "15s d'effort intense / 15s de trot pour simuler l'effort footballistique."},
            "en": {"name": "Intermittent 15-15 running", "description": "15s high-intensity effort / 15s jog to mimic match demands."},
        },
    },
    {
        "slug": "sauts_de_haies_plyometrie",
        "sport_slug": "football",
        "category": "power",
        "equipment": "plyo_box",
        "training_types": [TrainingType.POWER, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sauts pliométriques et détente", "description": "Amélioration de la détente verticale et de l'explosivité pour les duels aériens."},
            "en": {"name": "Plyometric hurdle jumps", "description": "Vertical jump power and explosive reactive strength for aerial duels."},
        },
    },
    # ------------------------------------------------------------
    # BOXE & COMBAT : TECHNIQUE, POWER, SPEED, CONDITIONING
    # ------------------------------------------------------------
    {
        "slug": "combinaison_boxe",
        "sport_slug": "boxe",
        "category": "full_body",
        "equipment": "gloves",
        "training_types": [TrainingType.CARDIO, TrainingType.SPEED, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Combinaison de boxe aux gants", "description": "Enchaînement jab-cross-crochet-uppercut avec vitesse et fluidité."},
            "en": {"name": "Boxing combo drills", "description": "Punch combinations (jab-cross-hook-uppercut) with speed and flow."},
        },
    },
    {
        "slug": "shadow_boxing",
        "sport_slug": "boxe",
        "category": "technique",
        "equipment": None,
        "training_types": [TrainingType.TECHNIQUE, TrainingType.SPEED, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Shadow boxing face au miroir", "description": "Travail des déplacements, esquives et précision des frappes sans charge."},
            "en": {"name": "Mirror shadow boxing", "description": "Footwork, slipping punches, and strike accuracy without resistance."},
        },
    },
    {
        "slug": "sac_de_frappe_puissance",
        "sport_slug": "boxe",
        "category": "power",
        "equipment": "boxing_bag",
        "training_types": [TrainingType.POWER, TrainingType.INTERVAL, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Rounds lourds au sac de frappe", "description": "Impact maximal et résistance anaérobie sur sac de frappe suspendu."},
            "en": {"name": "Heavy bag power rounds", "description": "Maximal impact and anaerobic endurance on the heavy bag."},
        },
    },
    {
        "slug": "esquives_et_jeu_de_jambes",
        "sport_slug": "boxe",
        "category": "agility",
        "equipment": None,
        "training_types": [TrainingType.AGILITY, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Jeu de jambes et esquives rotatives", "description": "Déplacements latéraux, pivots et désaxements pour éviter les coups."},
            "en": {"name": "Footwork and bob & weave", "description": "Lateral steps, pivots, and slipping to evade punches."},
        },
    },
    {
        "slug": "sparring_technique",
        "sport_slug": "boxe",
        "category": "technique",
        "equipment": "gloves",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.INTERVAL, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sparring thématique contrôlé", "description": "Mise de gants à intensité maîtrisée pour appliquer la tactique."},
            "en": {"name": "Technical controlled sparring", "description": "Controlled sparring round to practice fight strategy."},
        },
    },
    {
        "slug": "katas_formes_techniques",
        "sport_slug": "arts_martiaux",
        "category": "technique",
        "equipment": "mat",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.MOBILITY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Formes et katas martiaux", "description": "Perfectionnement des postures, blocages et frappes avec équilibre."},
            "en": {"name": "Martial forms and katas", "description": "Stance perfection, blocking, and striking balance."},
        },
    },
    {
        "slug": "coups_de_pied_paos",
        "sport_slug": "arts_martiaux",
        "category": "power",
        "equipment": "boxing_bag",
        "training_types": [TrainingType.POWER, TrainingType.SPEED, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Frappes pieds-poings aux paos", "description": "Kicks puissants et enchaînements dynamiques avec cible mobile."},
            "en": {"name": "Pad work kick combinations", "description": "High-impact kicks and dynamic combos on focus mitts/pads."},
        },
    },
    {
        "slug": "travail_au_sol_grappling",
        "sport_slug": "arts_martiaux",
        "category": "full_body",
        "equipment": "mat",
        "training_types": [TrainingType.STRENGTH, TrainingType.ENDURANCE, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Drills de grappling au sol", "description": "Transitions, soumissions et contrôle postural au sol."},
            "en": {"name": "Ground grappling drills", "description": "Ground transitions, positioning, and joint control."},
        },
    },
])
EXERCISES_CATALOG.extend([
    # ------------------------------------------------------------
    # COURSE À PIED & CYCLISME : ENDURANCE, SEUILS, CÔTES, RÉCUPÉRATION
    # ------------------------------------------------------------
    {
        "slug": "course_fractionnee",
        "sport_slug": "course",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.INTERVAL, TrainingType.SPEED, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Course fractionnée (30/30 ou 400m)", "description": "Alternance d'efforts à VMA et de récupération active."},
            "en": {"name": "Interval track repeats", "description": "Alternates VO2max sprint efforts with active recovery jogs."},
        },
    },
    {
        "slug": "course_endurance",
        "sport_slug": "course",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.ENDURANCE, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Sortie longue en endurance fondamentale", "description": "Course continue en aisance respiratoire pour développer le réseau capillaire."},
            "en": {"name": "Long aerobic endurance run", "description": "Continuous easy-pace run to build aerobic foundation."},
        },
    },
    {
        "slug": "sprint",
        "sport_slug": "course",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.SPEED, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sprints courts 60-100m", "description": "Course à vitesse maximale départ arrêté pour la vitesse pure."},
            "en": {"name": "Short maximal sprints 60-100m", "description": "All-out speed development from standing starts."},
        },
    },
    {
        "slug": "cotes_explosives",
        "sport_slug": "course",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.POWER, TrainingType.INTERVAL, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Répétitions en côte", "description": "Montées rapides pour renforcer la poussée des mollets et fessiers."},
            "en": {"name": "Hill running repeats", "description": "Explosive uphill bursts for running power and stride strength."},
        },
    },
    {
        "slug": "footing_recuperation",
        "sport_slug": "course",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.RECOVERY, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Footing de décrassage / récupération", "description": "Course très légère pour activer la circulation sans fatiguer."},
            "en": {"name": "Recovery shakeout jog", "description": "Very low-intensity jog to flush muscles without accumulating fatigue."},
        },
    },
    {
        "slug": "velo_route",
        "sport_slug": "cyclisme",
        "category": "legs",
        "equipment": "bike",
        "training_types": [TrainingType.ENDURANCE, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Sortie vélo endurance", "description": "Sortie sur route à cadence constante de 85-95 rpm."},
            "en": {"name": "Road endurance cycling", "description": "Steady-state road ride at 85-95 rpm cadence."},
        },
    },
    {
        "slug": "velo_intervalles_puissance",
        "sport_slug": "cyclisme",
        "category": "legs",
        "equipment": "stationary_bike",
        "training_types": [TrainingType.INTERVAL, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Intervalles haute intensité vélo", "description": "Sprints sur vélo ou home-trainer avec résistance élevée."},
            "en": {"name": "High-intensity bike sprints", "description": "High-resistance bike intervals for peak power."},
        },
    },
    # ------------------------------------------------------------
    # NATATION & BASKETBALL & FITNESS
    # ------------------------------------------------------------
    {
        "slug": "natation_crawl",
        "sport_slug": "natation",
        "category": "full_body",
        "equipment": "swimming_pool",
        "training_types": [TrainingType.ENDURANCE, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Natation crawl en continu", "description": "Nage fluide avec focus sur la glisse et l'alignement corporel."},
            "en": {"name": "Freestyle continuous swim", "description": "Smooth front crawl focusing on streamline and glide."},
        },
    },
    {
        "slug": "intervalles_sprint_natation",
        "sport_slug": "natation",
        "category": "full_body",
        "equipment": "swimming_pool",
        "training_types": [TrainingType.SPEED, TrainingType.INTERVAL, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sprints 50m natation fractionnés", "description": "Effort maximal sur 50 mètres avec repos complet."},
            "en": {"name": "50m sprint swim repeats", "description": "All-out 50m intervals with full rest."},
        },
    },
    {
        "slug": "dribble_basketball",
        "sport_slug": "basketball",
        "category": "technique",
        "equipment": "basketball",
        "training_types": [TrainingType.AGILITY, TrainingType.TECHNIQUE],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Dribble et changements de main", "description": "Maniement de balle bas et rapide sous pression simulée."},
            "en": {"name": "Crossover and handling drills", "description": "Low, fast ball handling and crossover variations."},
        },
    },
    {
        "slug": "tirs_en_suspension_basket",
        "sport_slug": "basketball",
        "category": "technique",
        "equipment": "basketball",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.POWER],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Tirs en suspension (jump shots)", "description": "Répétition de jump shots à mi-distance et à 3 points."},
            "en": {"name": "Jump shots repetition", "description": "Mid-range and three-point shooting drills under fatigue."},
        },
    },
    {
        "slug": "detente_verticale_basket",
        "sport_slug": "basketball",
        "category": "power",
        "equipment": "plyo_box",
        "training_types": [TrainingType.POWER, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Sauts pliométriques pour rebond", "description": "Exercices de détente pour capter les rebonds et smasher."},
            "en": {"name": "Rebound plyometric jumps", "description": "Explosive jumping work for rim protection and rebounding."},
        },
    },
    {
        "slug": "corde_a_sauter",
        "sport_slug": "fitness",
        "category": "cardio",
        "equipment": "jump_rope",
        "training_types": [TrainingType.CARDIO, TrainingType.AGILITY, TrainingType.INTERVAL],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Corde à sauter rythmée", "description": "Sauts à la corde, cardio, réactivité des chevilles et coordination."},
            "en": {"name": "Rhythmic jump rope", "description": "Rope skipping for cardio conditioning and ankle stiffness."},
        },
    },
    {
        "slug": "burpees_cardio",
        "sport_slug": "fitness",
        "category": "full_body",
        "equipment": None,
        "training_types": [TrainingType.INTERVAL, TrainingType.CARDIO, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Burpees explosifs", "description": "Descente au sol, pompe et saut vertical avec un fort impact métabolique."},
            "en": {"name": "Explosive burpees", "description": "Drop to floor, push-up, and vertical jump for high metabolic rate."},
        },
    },
    {
        "slug": "mountain_climbers",
        "sport_slug": "fitness",
        "category": "core",
        "equipment": None,
        "training_types": [TrainingType.CARDIO, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Mountain climbers", "description": "Montées de genoux rapides en appui facial, sollicite les abdos et le cœur."},
            "en": {"name": "Mountain climbers", "description": "Fast knee drives in pushup plank targeting core and cardio."},
        },
    },
    {
        "slug": "kettlebell_swings",
        "sport_slug": "fitness",
        "category": "power",
        "equipment": "kettlebell",
        "training_types": [TrainingType.POWER, TrainingType.CARDIO, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Kettlebell swings", "description": "Balancement explosif à la hanche pour la chaîne postérieure et le cardio."},
            "en": {"name": "Kettlebell swings", "description": "Explosive hip hinge for posterior chain and conditioning."},
        },
    },
    # ------------------------------------------------------------
    # GÉNÉRIQUES : MOBILITÉ, RÉCUPÉRATION, SANTÉ (ACCESSIBLES À TOUS)
    # ------------------------------------------------------------
    {
        "slug": "marche",
        "sport_slug": None,
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.RECOVERY, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Marche active quotidienne (NEAT)", "description": "Marche à allure dynamique pour stimuler la dépense sans fatigue nerveuse."},
            "en": {"name": "Daily brisk walk (NEAT)", "description": "Brisk walking to increase energy expenditure without nervous fatigue."},
        },
    },
    {
        "slug": "etirements",
        "sport_slug": None,
        "category": "mobility",
        "equipment": None,
        "training_types": [TrainingType.MOBILITY, TrainingType.RECOVERY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Étirements et mobilité globale", "description": "Relâchement musculaire et amplitude articulaire post-effort."},
            "en": {"name": "Full body stretching and mobility", "description": "Muscular relaxation and joint mobility after exertion."},
        },
    },
    {
        "slug": "mobilite_hanches_chevilles",
        "sport_slug": None,
        "category": "mobility",
        "equipment": None,
        "training_types": [TrainingType.MOBILITY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Mobilité des hanches et chevilles", "description": "Rotations articulaires et étirements dynamiques pour la prévention des blessures."},
            "en": {"name": "Hip and ankle mobility", "description": "Joint rotations and dynamic stretches for injury prevention."},
        },
    },
    {
        "slug": "auto_massage_foam_roller",
        "sport_slug": None,
        "category": "recovery",
        "equipment": "foam_roller",
        "training_types": [TrainingType.RECOVERY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Automassage au rouleau en mousse", "description": "Relâchement des tensions fasciales sur quadriceps, mollets et dos."},
            "en": {"name": "Foam rolling myofascial release", "description": "Releasing fascial tightness on quads, calves, and back."},
        },
    },
])
EXERCISES_CATALOG.extend([
    # ------------------------------------------------------------
    # COMBAT SUPPLÉMENTAIRES : SAC, CARDIO-MUSCULAIRE, AGILITÉ, MOBILITÉ
    # ------------------------------------------------------------
    {
        "slug": "sac_de_frappe_hiit",
        "sport_slug": "arts_martiaux",
        "category": "cardio",
        "equipment": "boxing_bag",
        "training_types": [TrainingType.INTERVAL, TrainingType.CARDIO, TrainingType.POWER],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "HIIT sac de frappe (rounds 2-3 min)", "description": "Rounds intenses au sac avec repos courts, spécifique endurance de frappe."},
            "en": {"name": "Heavy bag HIIT (2-3 min rounds)", "description": "Intense bag rounds with short rest, striking-specific conditioning."},
        },
    },
    {
        "slug": "circuit_cardio_musculaire_combat",
        "sport_slug": "arts_martiaux",
        "category": "full_body",
        "equipment": None,
        "training_types": [TrainingType.CARDIO, TrainingType.STRENGTH, TrainingType.ENDURANCE],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Circuit cardio-musculaire (pompes, gainage, squats)", "description": "Enchaînement pompes, gainage, squats et déplacements, façon crossfit combat."},
            "en": {"name": "Cardio-muscular circuit (push-ups, plank, squats)", "description": "Push-ups, plank, squats and footwork chained crossfit-style."},
        },
    },
    {
        "slug": "squats_sauts_pliometrie_combat",
        "sport_slug": "arts_martiaux",
        "category": "legs",
        "equipment": None,
        "training_types": [TrainingType.POWER, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Superset bas du corps explosif (squats, fentes, sauts)", "description": "Superset jambes pour la puissance de déplacement et d'esquive."},
            "en": {"name": "Explosive lower body superset (squats, lunges, jumps)", "description": "Lower body superset for movement and evasion power."},
        },
    },
    {
        "slug": "simulation_combat_situations",
        "sport_slug": "arts_martiaux",
        "category": "technique",
        "equipment": "gloves",
        "training_types": [TrainingType.TECHNIQUE, TrainingType.AGILITY, TrainingType.ENDURANCE],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Simulation de combat en situations", "description": "Scénarios de combat simulés : entrées, sorties, ripostes et gestion du rythme."},
            "en": {"name": "Fight simulation scenarios", "description": "Simulated fight situations: entries, exits, counters, and pace management."},
        },
    },
    {
        "slug": "agilite_ladder_deplacements",
        "sport_slug": "arts_martiaux",
        "category": "agility",
        "equipment": "agility_ladder",
        "training_types": [TrainingType.AGILITY, TrainingType.SPEED],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Échelle d'agilité et déplacements combat", "description": "Jeu de jambes, esquives et déplacements rapides sur échelle de rythme."},
            "en": {"name": "Agility ladder & fight footwork", "description": "Footwork, slips, and fast movement patterns on an agility ladder."},
        },
    },
    {
        "slug": "grand_ecart_mobilite_combat",
        "sport_slug": "arts_martiaux",
        "category": "mobility",
        "equipment": "mat",
        "training_types": [TrainingType.MOBILITY, TrainingType.RECOVERY],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Mobilité & travail du grand écart", "description": "Étirements profonds et progression vers le grand écart, hanche et ischios."},
            "en": {"name": "Mobility & splits progression", "description": "Deep stretching and splits progression, hips and hamstrings."},
        },
    },
    {
        "slug": "piscine_recup_active",
        "sport_slug": None,
        "category": "recovery",
        "equipment": "swimming_pool",
        "training_types": [TrainingType.RECOVERY, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Nage légère en piscine (récupération active)", "description": "Natation douce pour la circulation, la détente musculaire et la récupération."},
            "en": {"name": "Easy pool swim (active recovery)", "description": "Easy swimming for circulation, muscle relaxation, and recovery."},
        },
    },
    {
        "slug": "jogging_recup_legere",
        "sport_slug": None,
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.RECOVERY, TrainingType.CARDIO],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Jogging très léger (Zone 1)", "description": "Footing de décharge, allée conversationnelle, pour évacuer la fatigue."},
            "en": {"name": "Very easy jog (Zone 1)", "description": "Discharge jog at conversational pace to flush fatigue."},
        },
    },
])
EXERCISES_CATALOG.extend([
    # BOXE SUPPLÉMENTAIRES POUR UNE DIVERSITÉ TOTALE
    {
        "slug": "boxe_vitesse_poire",
        "sport_slug": "boxe",
        "category": "speed",
        "equipment": "boxing_bag",
        "training_types": [TrainingType.SPEED, TrainingType.AGILITY],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Poire de vitesse (speed bag)", "description": "Rythme rapide, coordination œil-main et endurance des épaules."},
            "en": {"name": "Speed bag rhythm drill", "description": "Fast rhythm, hand-eye coordination, and shoulder endurance."},
        },
    },
    {
        "slug": "boxe_corde_ondulatoire",
        "sport_slug": "boxe",
        "category": "cardio",
        "equipment": None,
        "training_types": [TrainingType.INTERVAL, TrainingType.POWER],
        "difficulty": DifficultyLevel.HARD,
        "translations": {
            "fr": {"name": "Cordes ondulatoires (Battle ropes)", "description": "Explosion cardio et puissance du haut du corps pour les boxeurs."},
            "en": {"name": "Battle ropes power slam", "description": "Upper body explosive cardio and power for fighters."},
        },
    },
    {
        "slug": "boxe_medball_rotations",
        "sport_slug": "boxe",
        "category": "power",
        "equipment": "medicine_ball",
        "training_types": [TrainingType.POWER, TrainingType.STRENGTH],
        "difficulty": DifficultyLevel.MEDIUM,
        "translations": {
            "fr": {"name": "Lancers rotatifs de médecine-ball", "description": "Puissance du tronc et rotation des hanches pour la frappe."},
            "en": {"name": "Rotational medicine ball slams", "description": "Core rotational power and hip snap for punching force."},
        },
    },
    {
        "slug": "boxe_circuit_abdos_ring",
        "sport_slug": "boxe",
        "category": "core",
        "equipment": None,
        "training_types": [TrainingType.STRENGTH, TrainingType.ENDURANCE],
        "difficulty": DifficultyLevel.EASY,
        "translations": {
            "fr": {"name": "Gainage dynamique et relevés de buste", "description": "Renforcement abdominal complet pour encaisser les coups au corps."},
            "en": {"name": "Fighter core circuit", "description": "Full abdominal conditioning to absorb body punches."},
        },
    },
])
EXERCISES_CATALOG.extend(PROGRAM_EXERCISES_CATALOG)
