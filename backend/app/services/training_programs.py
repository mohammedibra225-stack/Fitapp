"""
Programmes hebdomadaires par profil (module Sport).

Chaque seance porte maintenant la LISTE CANONIQUE d'exercices (slugs +
prescriptions) fournie pour toutes les combinaisons profil x sport x
niveau x frequence. weekly_scheduler.py et training_recommender.py
consomment ces listes telles quelles, puis appliquent les adaptations
d'objectif (lose-fat, build-muscle, improve-performance, healthy-lifestyle).

IMPORTANT (slugs) : branches indexees par les slugs CANONIQUES
("musculation", "arts_martiaux", "course", "cyclisme", "natation",
"football"). Correspondance onboarding : weight -> musculation,
combat -> arts_martiaux, running -> course, cycling -> cyclisme,
swimming -> natation (routes/onboarding.py).
"""

from __future__ import annotations

from typing import Optional

from app.models.enums import ActivityLevel, GoalType, SportLevel, TrainingType


def _frequency_bracket(frequency_per_week: int) -> str:
    if frequency_per_week <= 2:
        return "low"
    if frequency_per_week <= 4:
        return "moderate"
    return "high"


def _level_bracket(level: Optional[SportLevel]) -> str:
    if level in (SportLevel.EXPERT, SportLevel.PROFESSIONAL):
        return "expert"
    if level == SportLevel.ADVANCED:
        return "advanced"
    if level == SportLevel.INTERMEDIATE:
        return "intermediate"
    return "beginner"


def _ex(slug, sets=None, reps=None, duration_seconds=None, note=None):
    item = {"slug": slug}
    if sets is not None:
        item["sets"] = sets
    if reps is not None:
        item["reps"] = reps
    if duration_seconds is not None:
        item["duration_seconds"] = duration_seconds
    if note:
        item["note"] = note
    return item


def _session(name, categories, types, exercises, warmup=None, cooldown=None, power=None, exercises_by_sport=None):
    return {
        "name": name,
        "categories": categories,
        "types": types,
        "exercises": exercises,
        "warmup": warmup or [],
        "cooldown": cooldown or [],
        "power_exercises": power or [],
        "exercises_by_sport": exercises_by_sport or {},
    }


def theme_exercise_items(theme: dict, sport_slug: Optional[str]) -> list[dict]:
    """Liste d'exercices du theme, eventuellement specialisee par sport
    (endurance : course / velo / natation)."""
    by_sport = theme.get("exercises_by_sport") or {}
    if sport_slug and by_sport.get(sport_slug):
        return by_sport[sport_slug]
    return theme.get("exercises") or []


# ============================================================
# BRANCHE 1 : SEDENTAIRE
# ============================================================

_S_MOBILITE = _session(
    "Mobilité & mouvement doux",
    ["cardio", "mobility"],
    [TrainingType.MOBILITY, TrainingType.CARDIO],
    [
        _ex("cat_cow", duration_seconds=120),
        _ex("rotations_bras_epaules", duration_seconds=120),
        _ex("marche_rapide", duration_seconds=25 * 60, note="Marche rapide en plein air ou sur tapis (20 à 30 min)"),
        _ex("etirements_doux_ischios_pecs", duration_seconds=8 * 60),
    ],
    warmup=[_ex("cat_cow", duration_seconds=120), _ex("rotations_bras_epaules", duration_seconds=60)],
    cooldown=[_ex("etirements_doux_ischios_pecs", duration_seconds=8 * 60)],
)
_S_RENFO_DOUX = _session(
    "Renforcement au poids du corps (adapté)",
    ["full_body", "core"],
    [TrainingType.STRENGTH, TrainingType.MOBILITY],
    [
        _ex("squats_chaise", 3, 10),
        _ex("pompes_inclinees", 3, 10),
        _ex("birddog", 3, 8),
        _ex("glute_bridge", 3, 12),
        _ex("marche_active", duration_seconds=15 * 60),
    ],
    cooldown=[_ex("etirements")],
)
_S_FULL_ELASTIQUES = _session(
    "Full-body élastiques / léger",
    ["full_body", "legs", "chest"],
    [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
    [
        _ex("squats_poids_corps", 3, 12, note="Pause en bas"),
        _ex("pompes_genoux", 3, 10),
        _ex("rowing_elastique", 3, 12),
        _ex("developpe_epaules_leger", 3, 12),
        _ex("gainage_genoux", 3, duration_seconds=30),
    ],
    cooldown=[_ex("etirements")],
)

SEDENTARY_SEQUENCES: dict[GoalType, list[dict]] = {
    GoalType.WEIGHT_LOSS: [_S_MOBILITE, _S_RENFO_DOUX],
    GoalType.MAINTENANCE: [_S_MOBILITE, _S_RENFO_DOUX],
    GoalType.GENERAL_HEALTH: [_S_MOBILITE, _S_RENFO_DOUX],
    GoalType.ENDURANCE: [_S_MOBILITE, _S_RENFO_DOUX],
    GoalType.MUSCLE_GAIN: [_S_FULL_ELASTIQUES, _S_RENFO_DOUX],
    GoalType.BODY_RECOMPOSITION: [_S_FULL_ELASTIQUES, _S_RENFO_DOUX],
    GoalType.STRENGTH: [_S_FULL_ELASTIQUES, _S_RENFO_DOUX],
    GoalType.PERFORMANCE: [_S_RENFO_DOUX, _S_MOBILITE],
}
DEFAULT_SEDENTARY_SEQUENCE = SEDENTARY_SEQUENCES[GoalType.GENERAL_HEALTH]


# ============================================================
# BRANCHE 2 : MUSCULATION
# ============================================================

_M_FULL_BODY_A = _session(
    "Full-Body A",
    ["legs", "chest", "back"],
    [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
    [
        _ex("squat", 3, 8),
        _ex("developpe_couche", 3, 8),
        _ex("rowing_barre", 3, 10),
        _ex("developpe_militaire_halteres", 3, 10),
        _ex("gainage", 3, duration_seconds=45),
    ],
)
_M_FULL_BODY_B = _session(
    "Full-Body B",
    ["back", "shoulders", "legs", "core"],
    [TrainingType.STRENGTH, TrainingType.HYPERTROPHY],
    [
        _ex("souleve_de_terre", 3, 6),
        _ex("dips_lestes", 3, 10, note="Dips ou pompes lestées"),
        _ex("traction", 3, note="Max reps pronation"),
        _ex("fentes_bulgares", 3, 10),
        _ex("russian_twists", 3, 20),
    ],
)
_M_FULL_BODY_C = _session(
    "Full-Body C",
    ["chest", "arms", "core", "legs"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("presse_a_cuisses", 3, 12),
        _ex("developpe_incline_halteres", 3, 10),
        _ex("tirage_vertical", 3, 10),
        _ex("elevations_laterales", 3, 15),
        _ex("curl_biceps_barre", 3, 12, note="Superset avec extensions triceps"),
        _ex("extension_triceps_poulie", 3, 12),
    ],
)
_M_UPPER = _session(
    "Upper (haut du corps)",
    ["chest", "back", "shoulders", "arms"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("developpe_couche", 4, 8),
        _ex("rowing_barre", 4, 8),
        _ex("developpe_incline_halteres", 3, 10),
        _ex("tractions_supination", 3, note="Max reps"),
        _ex("elevations_laterales", 3, 15),
        _ex("extension_triceps_poulie", 3, 12),
    ],
)
_M_LOWER = _session(
    "Lower (bas du corps)",
    ["legs", "core"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("squat", 4, 8),
        _ex("souleve_terre_jambes_tendues", 3, 10),
        _ex("fentes_marchees", 3, 10),
        _ex("leg_extension", 3, 12),
        _ex("leg_curl", 3, 12),
        _ex("mollets_debout", 3, 15),
        _ex("gainage_dynamique", 3, 15),
    ],
)
_M_PUSH = _session(
    "Push (poussée)",
    ["chest", "shoulders", "arms"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("developpe_couche", 4, 8),
        _ex("developpe_militaire", 4, 8),
        _ex("ecartes_poulie", 3, 12),
        _ex("elevations_laterales_cable", 3, 15),
        _ex("dips", 3, 10),
        _ex("extension_triceps_overhead", 3, 12),
    ],
)
_M_PULL = _session(
    "Pull (tirage)",
    ["back", "arms"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("souleve_de_terre", 3, 5),
        _ex("tractions_lestees", 4, 6),
        _ex("rowing_unilateral", 3, 10),
        _ex("tirage_poitrine_prise_serree", 3, 12),
        _ex("oiseau_halteres", 3, 15),
        _ex("curl_ez", 3, 10),
        _ex("curl_marteau", 3, 12),
    ],
)
_M_LEGS = _session(
    "Legs (jambes)",
    ["legs", "core"],
    [TrainingType.HYPERTROPHY, TrainingType.STRENGTH],
    [
        _ex("squat_profond", 4, 8),
        _ex("fentes_bulgares", 3, 10),
        _ex("rdl_roumain", 3, 10),
        _ex("hip_thrust", 3, 10),
        _ex("leg_curl_assis", 3, 12),
        _ex("mollets_presse", 3, 15),
        _ex("releves_jambes_suspendu", 3, 12),
    ],
)
_M_LIGHT_CARDIO = _session(
    "Cardio / mobilité légère",
    ["cardio", "core"],
    [TrainingType.CARDIO, TrainingType.MOBILITY],
    [_ex("corde_a_sauter", duration_seconds=10 * 60), _ex("etirements", duration_seconds=8 * 60)],
)

MUSCULATION_SEQUENCES: dict[str, dict[str, list[dict]]] = {
    "low": {
        "beginner": [_M_FULL_BODY_A, _M_FULL_BODY_B],
        "intermediate": [_M_FULL_BODY_A, _M_FULL_BODY_B],
        "advanced": [_M_FULL_BODY_A, _M_FULL_BODY_C],
        "expert": [_M_FULL_BODY_A, _M_FULL_BODY_C],
    },
    "moderate": {
        "beginner": [_M_FULL_BODY_A, _M_FULL_BODY_B, _M_FULL_BODY_C],
        "intermediate": [_M_UPPER, _M_LOWER, _M_UPPER, _M_LOWER],
        "advanced": [_M_PUSH, _M_PULL, _M_LEGS, _M_UPPER],
        "expert": [_M_PUSH, _M_PULL, _M_LEGS, _M_UPPER],
    },
    "high": {
        "beginner": [_M_FULL_BODY_A, _M_LIGHT_CARDIO, _M_FULL_BODY_B, _M_LIGHT_CARDIO, _M_FULL_BODY_C],
        "intermediate": [_M_UPPER, _M_LOWER, _M_PUSH, _M_PULL, _M_LEGS],
        "advanced": [_M_PUSH, _M_PULL, _M_LEGS, _M_PUSH, _M_PULL, _M_LEGS],
        "expert": [_M_PUSH, _M_PULL, _M_LEGS, _M_PUSH, _M_PULL, _M_LEGS],
    },
}


# ============================================================
# BRANCHE 3 : COMBAT
# ============================================================

_C_INITIATION = _session(
    "Initiation & conditionnement de base",
    ["technique", "full_body", "core"],
    [TrainingType.TECHNIQUE, TrainingType.STRENGTH],
    [
        _ex("directs_jab_cross", 4, duration_seconds=120),
        _ex("pompes_genoux", 3, 10),
        _ex("squats_poids_corps", 3, 15),
        _ex("gainage_coudes", 3, duration_seconds=30),
    ],
    warmup=[_ex("corde_a_sauter", 3, duration_seconds=120), _ex("rotations_poignets_chevilles")],
    cooldown=[_ex("etirements", note="Fessiers et épaules")],
)
_C_AGILITE_CARDIO = _session(
    "Agilité & cardio doux",
    ["agility", "technique"],
    [TrainingType.AGILITY, TrainingType.MOBILITY],
    [
        _ex("pas_chasses_croises", 4, duration_seconds=45),
        _ex("shadow_boxing", 3, duration_seconds=180),
        _ex("mountain_climbers", 3, duration_seconds=30),
        _ex("birddog", 3, 10),
    ],
    cooldown=[_ex("etirements")],
)
_C_CARDIO_MUSCU = _session(
    "Cardio-musculaire & light sparring",
    ["full_body", "core"],
    [TrainingType.CARDIO, TrainingType.STRENGTH],
    [
        _ex("burpees_cardio", 4, 8),
        _ex("kettlebell_swings", 4, 12),
        _ex("thrusters", 4, 8),
        _ex("slam_ball", 4, 10),
        _ex("pompes_explosives", 3, 8),
        _ex("gainage_dynamique", 3, 12),
        _ex("light_sparring_paos", 4, duration_seconds=120),
    ],
    power=["pompes_explosives", "slam_ball", "thrusters"],
)
_C_LOWER_COMBAT = _session(
    "Lower body & simulation combat",
    ["legs", "technique"],
    [TrainingType.STRENGTH, TrainingType.TECHNIQUE],
    [
        _ex("goblet_squat", 4, 10, note="Superset sauts verticaux"),
        _ex("sauts_verticaux", 4, 8),
        _ex("fentes_marchees", 3, 10, note="Superset broad jumps"),
        _ex("broad_jumps", 3, 6),
        _ex("rdl_roumain", 3, 10, note="Superset glute bridge"),
        _ex("glute_bridge", 3, 12),
        _ex("rounds_shadow_lutte_sac", 4, duration_seconds=180),
    ],
    power=["sauts_verticaux", "broad_jumps"],
)
_C_MUSCU_AGILITE = _session(
    "Musculation, agilité & flexibilité",
    ["full_body", "agility"],
    [TrainingType.STRENGTH, TrainingType.AGILITY, TrainingType.MOBILITY],
    [
        _ex("developpe_militaire", 4, 8),
        _ex("traction", 4, 8),
        _ex("agilite_ladder_deplacements", 5, duration_seconds=45),
        _ex("box_jumps", 4, 6),
        _ex("grand_ecart_mobilite_combat", duration_seconds=10 * 60, note="Fente basse, pigeon, grenouille, half split"),
    ],
    power=["box_jumps"],
    cooldown=[_ex("grand_ecart_mobilite_combat")],
)
_C_PLYO = _session(
    "Pliométrie & puissance",
    ["power", "legs"],
    [TrainingType.POWER],
    [
        _ex("depth_jumps", 4, 5),
        _ex("medball_chest_pass", 4, 8),
        _ex("pompes_clappees", 4, 6),
        _ex("landmine_press", 4, 6),
    ],
    power=["depth_jumps", "medball_chest_pass", "pompes_clappees", "landmine_press"],
)
_C_FORCE_LOURDE = _session(
    "Force lourde",
    ["full_body", "legs", "back"],
    [TrainingType.STRENGTH],
    [
        _ex("souleve_de_terre", 4, 5),
        _ex("landmine_rotations", 4, 8),
        _ex("tractions_lestees", 4, 6),
        _ex("dips_lestes", 4, 6),
    ],
)
_C_SPARRING_HIIT = _session(
    "Sparring & haute intensité",
    ["technique", "agility"],
    [TrainingType.TECHNIQUE, TrainingType.AGILITY, TrainingType.SPEED],
    [
        _ex("sparring_intensif", 5, duration_seconds=180),
        _ex("sprawls_burpees", duration_seconds=5 * 60, note="Finisseur à épuisement"),
    ],
)
_C_MOBILITE_PROFONDE = _session(
    "Mobilité profonde & prévention",
    ["recovery", "mobility"],
    [TrainingType.MOBILITY, TrainingType.RECOVERY],
    [
        _ex("isometrie_grand_ecart", duration_seconds=8 * 60),
        _ex("t_spine_mobility", duration_seconds=6 * 60),
        _ex("cervicales_bande", 3, 12),
        _ex("coiffe_rotateurs", 3, 15),
    ],
    cooldown=[_ex("etirements")],
)
_C_RECUP_ACTIVE = _session(
    "Récupération active",
    ["recovery", "mobility"],
    [TrainingType.RECOVERY, TrainingType.MOBILITY],
    [_ex("piscine_recup_active", duration_seconds=20 * 60), _ex("etirements", duration_seconds=10 * 60)],
)

ARTS_MARTIAUX_SEQUENCES: dict[str, dict[str, list[dict]]] = {
    "low": {
        "beginner": [_C_INITIATION, _C_AGILITE_CARDIO],
        "intermediate": [_C_INITIATION, _C_AGILITE_CARDIO],
        "advanced": [_C_CARDIO_MUSCU, _C_LOWER_COMBAT],
        "expert": [_C_CARDIO_MUSCU, _C_LOWER_COMBAT],
    },
    "moderate": {
        "beginner": [_C_INITIATION, _C_AGILITE_CARDIO, _C_MUSCU_AGILITE],
        "intermediate": [_C_CARDIO_MUSCU, _C_LOWER_COMBAT, _C_MUSCU_AGILITE],
        "advanced": [_C_CARDIO_MUSCU, _C_LOWER_COMBAT, _C_MUSCU_AGILITE, _C_PLYO],
        "expert": [_C_PLYO, _C_FORCE_LOURDE, _C_SPARRING_HIIT, _C_MOBILITE_PROFONDE],
    },
    "high": {
        "beginner": [_C_INITIATION, _C_RECUP_ACTIVE, _C_AGILITE_CARDIO, _C_MUSCU_AGILITE, _C_RECUP_ACTIVE],
        "intermediate": [_C_PLYO, _C_FORCE_LOURDE, _C_SPARRING_HIIT, _C_MOBILITE_PROFONDE, _C_RECUP_ACTIVE],
        "advanced": [_C_PLYO, _C_FORCE_LOURDE, _C_SPARRING_HIIT, _C_MOBILITE_PROFONDE, _C_CARDIO_MUSCU, _C_RECUP_ACTIVE],
        "expert": [_C_PLYO, _C_FORCE_LOURDE, _C_SPARRING_HIIT, _C_MOBILITE_PROFONDE, _C_CARDIO_MUSCU, _C_RECUP_ACTIVE],
    },
}


# ============================================================
# BRANCHE 4 : ENDURANCE
# ============================================================

_E_VMA = _session(
    "VMA / fractionné (HIIT)",
    ["cardio"],
    [TrainingType.INTERVAL, TrainingType.SPEED],
    [_ex("course_fractionnee", note="10 min échauffement + 10-12x 30/30 + 5 min retour au calme")],
    warmup=[_ex("marche", duration_seconds=10 * 60)],
    cooldown=[_ex("etirements")],
    exercises_by_sport={
        "course": [_ex("course_fractionnee", note="10 min échauffement + 10-12x 30s sprint / 30s footing + 5 min retour au calme")],
        "cyclisme": [_ex("velo_intervalles_puissance", note="10 min échauffement + 8x 1 min résistance max / 1 min fluide")],
        "natation": [_ex("intervalles_sprint_natation", note="200 m échauffement + 8x50 m sprint crawl, 30 s repos")],
    },
)
_E_PPG = _session(
    "PPG & renforcement spécifique endurance",
    ["core", "legs"],
    [TrainingType.STRENGTH, TrainingType.MOBILITY],
    [
        _ex("fentes_sautees", 3, 12),
        _ex("mollets_une_jambe", 3, 15, note="Pause en haut"),
        _ex("step_ups_charges", 3, 10),
        _ex("gainage", 3, duration_seconds=60),
        _ex("gainage_lateral", 3, duration_seconds=60),
        _ex("bridge_une_jambe", 3, 12),
    ],
    power=["fentes_sautees"],
)
_E_ZONE2 = _session(
    "Sortie longue (Zone 2)",
    ["cardio"],
    [TrainingType.ENDURANCE, TrainingType.CARDIO],
    [_ex("course_endurance", duration_seconds=60 * 60, note="Allure conversationnelle 45-90 min")],
    exercises_by_sport={
        "course": [_ex("course_endurance", duration_seconds=60 * 60, note="Allure modérée 45-90 min")],
        "cyclisme": [_ex("velo_route", duration_seconds=75 * 60, note="Allure modérée 45-90 min")],
        "natation": [_ex("natation_crawl", duration_seconds=45 * 60, note="Nage continue aisance respiratoire")],
    },
)
_E_SEUIL = _session(
    "Sortie au seuil",
    ["cardio"],
    [TrainingType.ENDURANCE, TrainingType.CARDIO],
    [_ex("course_endurance", duration_seconds=50 * 60, note="Allure spécifique compétition")],
    exercises_by_sport={
        "course": [_ex("course_endurance", duration_seconds=50 * 60)],
        "cyclisme": [_ex("velo_route", duration_seconds=55 * 60)],
        "natation": [_ex("natation_crawl", duration_seconds=40 * 60)],
    },
)
_E_RECUP = _session(
    "Récupération active",
    ["cardio"],
    [TrainingType.RECOVERY, TrainingType.CARDIO],
    [_ex("footing_recuperation", duration_seconds=30 * 60)],
    exercises_by_sport={
        "course": [_ex("footing_recuperation", duration_seconds=30 * 60)],
        "cyclisme": [_ex("velo_route", duration_seconds=35 * 60, note="Cadence fluide Zone 1")],
        "natation": [_ex("piscine_recup_active", duration_seconds=25 * 60)],
    },
)
_E_MOBILITE = _session(
    "Mobilité & étirements profonds",
    ["mobility"],
    [TrainingType.MOBILITY, TrainingType.RECOVERY],
    [_ex("t_spine_mobility"), _ex("etirements"), _ex("mobilite_hanches_chevilles")],
)

ENDURANCE_SEQUENCES: dict[str, dict[str, list[dict]]] = {
    "low": {
        "beginner": [_E_ZONE2, _E_PPG],
        "intermediate": [_E_VMA, _E_PPG],
        "advanced": [_E_VMA, _E_ZONE2],
        "expert": [_E_VMA, _E_ZONE2],
    },
    "moderate": {
        "beginner": [_E_VMA, _E_PPG, _E_ZONE2],
        "intermediate": [_E_VMA, _E_PPG, _E_ZONE2],
        "advanced": [_E_VMA, _E_SEUIL, _E_PPG, _E_ZONE2],
        "expert": [_E_VMA, _E_SEUIL, _E_PPG, _E_ZONE2],
    },
    "high": {
        "beginner": [_E_VMA, _E_PPG, _E_ZONE2, _E_RECUP],
        "intermediate": [_E_VMA, _E_SEUIL, _E_ZONE2, _E_RECUP, _E_PPG],
        "advanced": [_E_VMA, _E_SEUIL, _E_ZONE2, _E_RECUP, _E_PPG],
        "expert": [_E_VMA, _E_SEUIL, _E_ZONE2, _E_RECUP, _E_PPG, _E_RECUP, _E_MOBILITE],
    },
}


# ============================================================
# BRANCHE 5 : FOOTBALL
# ============================================================

_F_PMA = _session(
    "Vitesse, explosivité & agilité (PMA)",
    ["speed", "agility", "technique"],
    [TrainingType.SPEED, TrainingType.AGILITY, TrainingType.TECHNIQUE],
    [
        _ex("echelle_agilite_footwork", 5, duration_seconds=45),
        _ex("sprints_en_v", 6, note="Repos complet entre passages"),
        _ex("sprints_navette_football", 6, note="Navettes 5-10-15 m"),
        _ex("sauts_lateraux_haies", 4, 10),
    ],
    power=["sauts_lateraux_haies", "sprints_en_v"],
)
_F_PREVENTION = _session(
    "Musculation de prévention des blessures",
    ["legs", "core"],
    [TrainingType.STRENGTH, TrainingType.MOBILITY],
    [
        _ex("nordics_hamstring", 4, 6),
        _ex("copenhagen_plank", 3, duration_seconds=30),
        _ex("proprio_bosu", 3, duration_seconds=45),
        _ex("gainage_rotations_buste", 3, 15),
    ],
)
_F_MATCH = _session(
    "Match ou simulation haute intensité",
    ["cardio", "technique"],
    [TrainingType.ENDURANCE, TrainingType.SPEED, TrainingType.AGILITY],
    [_ex("match_football"), _ex("passes_courtes_une_touche"), _ex("frappes_et_tirs_au_but")],
)
_F_TERRAIN = _session(
    "Entraînement terrain / tactique",
    ["technique", "agility"],
    [TrainingType.TECHNIQUE, TrainingType.AGILITY],
    [_ex("slalom_plots_agilite"), _ex("passes_courtes_une_touche"), _ex("frappes_et_tirs_au_but")],
)

FOOTBALL_SEQUENCES: dict[str, dict[str, list[dict]]] = {
    "low": {
        "beginner": [_F_PMA, _F_PREVENTION],
        "intermediate": [_F_PMA, _F_PREVENTION],
        "advanced": [_F_PMA, _F_PREVENTION],
        "expert": [_F_PMA, _F_PREVENTION],
    },
    "moderate": {
        "beginner": [_F_PMA, _F_PREVENTION, _F_MATCH],
        "intermediate": [_F_PMA, _F_PREVENTION, _F_MATCH],
        "advanced": [_F_PMA, _F_PREVENTION, _F_MATCH],
        "expert": [_F_PMA, _F_PREVENTION, _F_MATCH],
    },
    "high": {
        "beginner": [_F_PMA, _F_PREVENTION, _F_MATCH],
        "intermediate": [_F_TERRAIN, _F_PMA, _F_PREVENTION, _E_RECUP],
        "advanced": [_F_TERRAIN, _F_PMA, _F_PREVENTION, _E_RECUP],
        "expert": [_F_TERRAIN, _F_PMA, _F_PREVENTION, _E_RECUP],
    },
}


# ============================================================
# BRANCHE 6 : AUTRES SPORTS
# ============================================================

_O_RENFO = _session(
    "Renforcement fonctionnel poids du corps",
    ["full_body", "core"],
    [TrainingType.STRENGTH, TrainingType.MOBILITY],
    [
        _ex("squats_poids_corps", 3, 12),
        _ex("pompes", 3, 10),
        _ex("birddog", 3, 8),
        _ex("gainage", 3, duration_seconds=40),
    ],
)
_O_CARDIO = _session(
    "Cardio polyvalent",
    ["cardio"],
    [TrainingType.CARDIO, TrainingType.ENDURANCE],
    [_ex("corde_a_sauter", duration_seconds=12 * 60), _ex("marche", duration_seconds=20 * 60)],
)
_O_MOBILITE = _session(
    "Mobilité & étirements",
    ["core", "full_body"],
    [TrainingType.MOBILITY, TrainingType.RECOVERY],
    [_ex("cat_cow"), _ex("mobilite_hanches_chevilles"), _ex("etirements")],
)

_OTHER_SEQUENCE = [_O_RENFO, _O_CARDIO, _O_MOBILITE]
OTHER_SEQUENCES: dict[str, dict[str, list[dict]]] = {
    bracket: {level: _OTHER_SEQUENCE for level in ("beginner", "intermediate", "advanced", "expert")}
    for bracket in ("low", "moderate", "high")
}


SPORT_PROGRAM_BRANCHES: dict[str, dict[str, dict[str, list[dict]]]] = {
    "musculation": MUSCULATION_SEQUENCES,
    "arts_martiaux": ARTS_MARTIAUX_SEQUENCES,
    "boxe": ARTS_MARTIAUX_SEQUENCES,
    "course": ENDURANCE_SEQUENCES,
    "cyclisme": ENDURANCE_SEQUENCES,
    "natation": ENDURANCE_SEQUENCES,
    "football": FOOTBALL_SEQUENCES,
}

ACTIVITY_TRAINING_DEFAULTS: dict[ActivityLevel, tuple[SportLevel, int]] = {
    ActivityLevel.LIGHT: (SportLevel.BEGINNER, 2),
    ActivityLevel.MODERATE: (SportLevel.INTERMEDIATE, 3),
    ActivityLevel.ACTIVE: (SportLevel.ADVANCED, 4),
    ActivityLevel.VERY_ACTIVE: (SportLevel.EXPERT, 5),
}


def resolve_training_volume(
    activity_level: Optional[ActivityLevel],
    level: Optional[SportLevel],
    frequency_per_week: Optional[int],
) -> tuple[Optional[SportLevel], int]:
    """Si le niveau / la frequence sport n'ont pas ete renseignes, on
    les deduit du niveau d'activite (actif -> 3x intermediaire, etc.)."""
    defaults = ACTIVITY_TRAINING_DEFAULTS.get(activity_level) if activity_level else None
    if frequency_per_week is None or frequency_per_week <= 0:
        frequency_per_week = defaults[1] if defaults else 3
    if level is None and defaults:
        level = defaults[0]
    return level, max(1, min(7, frequency_per_week))


def build_training_day_sequence(
    sport_slug: Optional[str],
    activity_level: Optional[ActivityLevel],
    level: Optional[SportLevel],
    frequency_per_week: int,
    goal: Optional[GoalType],
) -> list[dict]:
    level, frequency_per_week = resolve_training_volume(activity_level, level, frequency_per_week)

    if activity_level == ActivityLevel.SEDENTARY or sport_slug is None:
        pattern = SEDENTARY_SEQUENCES.get(goal, DEFAULT_SEDENTARY_SEQUENCE)
    else:
        freq_bracket = _frequency_bracket(frequency_per_week)
        lvl_bracket = _level_bracket(level)
        branch = SPORT_PROGRAM_BRANCHES.get(sport_slug, OTHER_SEQUENCES)
        pattern = branch.get(freq_bracket, branch.get("moderate", {})).get(lvl_bracket)
        if not pattern:
            pattern = _OTHER_SEQUENCE

    if not pattern:
        pattern = _OTHER_SEQUENCE

    return [pattern[i % len(pattern)] for i in range(frequency_per_week)]


def get_sport_session_theme(
    sport_slug: Optional[str],
    activity_level: Optional[ActivityLevel],
    level: Optional[SportLevel],
    frequency_per_week: int,
    goal: Optional[GoalType],
    session_index: int = 0,
) -> Optional[dict]:
    sequence = build_training_day_sequence(
        sport_slug, activity_level, level, frequency_per_week, goal
    )
    if not sequence:
        return None
    return sequence[session_index % len(sequence)]
