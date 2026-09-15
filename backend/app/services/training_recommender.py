"""
Moteur de recommandation d'entrainement (module Sport, partie 7).

Premier moteur DETERMINISTE base sur un score, pas d'IA complexe (regle
explicite du cahier des charges). Les poids sont configurables ci-dessous.

    Score = objectif      x 30%
          + sport         x 25%
          + niveau        x 20%
          + disponibilite x 10%
          + historique    x 10%
          + recuperation  x  5%

Chaque sous-score est normalise dans [0, 1] avant ponderation. Le score
final est donc lui aussi dans [0, 1].

Le parametre `recovery_score` (0-1) est un PLACEHOLDER en attendant le
vrai Recovery Score de l'etape 8 : sans valeur fournie, on utilise une
valeur neutre plutot que de faire echouer la recommandation (regle :
Fitapp doit continuer a fonctionner avec les donnees deja presentes).
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DifficultyLevel, GoalType, SportLevel, TrainingType
from app.models.profile import Profile
from app.models.training import Exercise
from app.services.training_programs import get_sport_session_theme, theme_exercise_items
from app.services.training_service import (
    get_exercises_by_slugs,
    get_primary_sport,
    get_recent_training_load,
    get_recent_workout_logs,
    get_sport_goal_relevance,
    list_exercises,
)


# ============================================================
# POIDS DU SCORE (configurables, doivent totaliser 1.0)
# ============================================================

SCORE_WEIGHTS = {
    "goal": 0.30,
    "sport": 0.25,
    "level": 0.20,
    "availability": 0.10,
    "history": 0.10,
    "recovery": 0.05,
}

# Valeur neutre utilisee quand une information manque (profil incomplet,
# recovery score pas encore disponible...) : ni penalisant ni favorisant.
NEUTRAL_SCORE = 0.5


# ============================================================
# OBJECTIF -> TYPES D'ENTRAINEMENT PERTINENTS
# ============================================================
# Poids de pertinence de chaque TrainingType pour un GoalType donne.
# Un type absent du dict d'un objectif vaut 0 (non pertinent pour ce but).
#
# Strategie par objectif (revu suite a un retour utilisateur : l'ancienne
# version reduisait chaque objectif a 2-3 types trop simplistes, ex.
# WEIGHT_LOSS = cardio uniquement, sans aucune musculation alors qu'elle
# est essentielle pour preserver la masse maigre pendant un deficit) :
#
#   MUSCLE_GAIN         hypertrophie prioritaire, force en soutien
#                        (progressive overload), un peu de power.
#   STRENGTH             force maximale prioritaire, mouvements composes ;
#                        volume/cardio volontairement bas (repos longs,
#                        pas de dilution de l'effort par du cardio).
#   WEIGHT_LOSS          cardio + intervalles (HIIT) pour la depense,
#                        MAIS musculation quasi aussi importante pour
#                        preserver le muscle pendant le deficit -- c'est
#                        le point que l'ancienne version manquait
#                        completement.
#   ENDURANCE            volume aerobie prioritaire, intervalles en
#                        complement, un peu de recuperation active.
#   PERFORMANCE           qualites specifiques au sport (vitesse, power,
#                        agilite, technique) plutot que du cardio generique --
#                        "performance" ne veut jamais dire "fais du cardio".
#   BODY_RECOMPOSITION    hypertrophie + force pour construire du muscle,
#                        cardio/intervalles pour la depense, en parallele.
#   GENERAL_HEALTH        mobilite et cardio modere prioritaires (healthy
#                        lifestyle), force et endurance en soutien.
#   MAINTENANCE            entrainement mixte equilibre, rien de dominant.

GOAL_TRAINING_TYPE_WEIGHTS: dict[GoalType, dict[TrainingType, float]] = {
    GoalType.MUSCLE_GAIN: {
        TrainingType.HYPERTROPHY: 1.0,
        TrainingType.STRENGTH: 0.75,
        TrainingType.POWER: 0.35,
        TrainingType.RECOVERY: 0.25,
    },
    GoalType.STRENGTH: {
        TrainingType.STRENGTH: 1.0,
        TrainingType.POWER: 0.6,
        TrainingType.HYPERTROPHY: 0.35,
        TrainingType.RECOVERY: 0.25,
    },
    GoalType.WEIGHT_LOSS: {
        TrainingType.CARDIO: 0.9,
        TrainingType.INTERVAL: 0.85,
        TrainingType.STRENGTH: 0.75,
        TrainingType.HYPERTROPHY: 0.6,
        TrainingType.ENDURANCE: 0.5,
        TrainingType.RECOVERY: 0.4,
    },
    GoalType.ENDURANCE: {
        TrainingType.ENDURANCE: 1.0,
        TrainingType.CARDIO: 0.75,
        TrainingType.INTERVAL: 0.6,
        TrainingType.RECOVERY: 0.3,
    },
    GoalType.PERFORMANCE: {
        TrainingType.SPEED: 0.9,
        TrainingType.POWER: 0.85,
        TrainingType.AGILITY: 0.75,
        TrainingType.TECHNIQUE: 0.7,
        TrainingType.INTERVAL: 0.55,
        TrainingType.STRENGTH: 0.3,
    },
    GoalType.BODY_RECOMPOSITION: {
        TrainingType.HYPERTROPHY: 0.85,
        TrainingType.STRENGTH: 0.6,
        TrainingType.CARDIO: 0.6,
        TrainingType.INTERVAL: 0.4,
        TrainingType.RECOVERY: 0.3,
    },
    GoalType.GENERAL_HEALTH: {
        TrainingType.MOBILITY: 0.75,
        TrainingType.CARDIO: 0.65,
        TrainingType.ENDURANCE: 0.45,
        TrainingType.STRENGTH: 0.45,
        TrainingType.RECOVERY: 0.5,
    },
    GoalType.MAINTENANCE: {
        TrainingType.MIXED: 0.75,
        TrainingType.MOBILITY: 0.55,
        TrainingType.CARDIO: 0.45,
        TrainingType.STRENGTH: 0.45,
        TrainingType.RECOVERY: 0.3,
    },
}


# ============================================================
# GOALTYPE (enum interne, 8 valeurs) -> GOAL.slug (catalogue DB, 24
# objectifs granulaires seedes via goal_seed.py/sport_goal_matrix_seed.py)
# ============================================================
# Permet d'interroger SportGoalMatrix (sport x objectif, deja seedee
# pour 10 sports) meme si le moteur raisonne avec l'enum GoalType, plus
# compact. Un GoalType absent d'ici (aucun ne l'est actuellement) se
# rabat simplement sur l'absence de bonus/malus lie au sport pratique.

GOAL_TYPE_TO_GOAL_SLUG: dict[GoalType, str] = {
    GoalType.MUSCLE_GAIN: "muscle_gain",
    GoalType.STRENGTH: "strength",
    GoalType.WEIGHT_LOSS: "fat_loss",
    GoalType.ENDURANCE: "endurance",
    GoalType.PERFORMANCE: "performance",
    GoalType.BODY_RECOMPOSITION: "body_recomposition",
    GoalType.GENERAL_HEALTH: "general_fitness",
    GoalType.MAINTENANCE: "healthy_lifestyle",
}


# ============================================================
# SPORT -> TYPES D'ENTRAINEMENT PERTINENTS
# ============================================================
# Reprend les associations donnees en exemple dans le cahier des charges
# (module Sport, partie 2).

SPORT_TRAINING_TYPE_WEIGHTS: dict[str, dict[TrainingType, float]] = {
    "musculation": {
        TrainingType.STRENGTH: 1.0,
        TrainingType.HYPERTROPHY: 1.0,
        TrainingType.POWER: 0.6,
        TrainingType.MOBILITY: 0.4,
    },
    "football": {
        TrainingType.ENDURANCE: 0.9,
        TrainingType.SPEED: 0.9,
        TrainingType.INTERVAL: 0.8,
        TrainingType.AGILITY: 0.9,
        TrainingType.STRENGTH: 0.5,
        TrainingType.RECOVERY: 0.3,
    },
    "course": {
        TrainingType.ENDURANCE: 1.0,
        TrainingType.INTERVAL: 0.8,
        TrainingType.SPEED: 0.6,
        TrainingType.RECOVERY: 0.4,
    },
    "boxe": {
        TrainingType.CARDIO: 0.9,
        TrainingType.INTERVAL: 0.8,
        TrainingType.SPEED: 0.8,
        TrainingType.POWER: 0.6,
        TrainingType.TECHNIQUE: 0.9,
        TrainingType.RECOVERY: 0.3,
    },
    "basketball": {
        TrainingType.AGILITY: 0.9,
        TrainingType.SPEED: 0.7,
        TrainingType.ENDURANCE: 0.6,
        TrainingType.TECHNIQUE: 0.8,
        TrainingType.STRENGTH: 0.4,
    },
    "cyclisme": {
        TrainingType.ENDURANCE: 1.0,
        TrainingType.CARDIO: 0.8,
        TrainingType.INTERVAL: 0.5,
    },
    "natation": {
        TrainingType.ENDURANCE: 0.9,
        TrainingType.TECHNIQUE: 0.9,
        TrainingType.CARDIO: 0.6,
    },
    "fitness": {
        TrainingType.CARDIO: 0.8,
        TrainingType.MIXED: 0.8,
        TrainingType.AGILITY: 0.5,
    },
    "cardio": {
        TrainingType.CARDIO: 1.0,
        TrainingType.INTERVAL: 0.6,
    },
    "arts_martiaux": {
        TrainingType.TECHNIQUE: 0.9,
        TrainingType.CARDIO: 0.6,
        TrainingType.POWER: 0.5,
        TrainingType.AGILITY: 0.6,
    },
}


# ============================================================
# NIVEAU -> DIFFICULTE PREFEREE
# ============================================================

LEVEL_DIFFICULTY_WEIGHTS: dict[SportLevel, dict[DifficultyLevel, float]] = {
    SportLevel.BEGINNER: {
        DifficultyLevel.EASY: 1.0,
        DifficultyLevel.MEDIUM: 0.5,
        DifficultyLevel.HARD: 0.1,
    },
    SportLevel.INTERMEDIATE: {
        DifficultyLevel.EASY: 0.6,
        DifficultyLevel.MEDIUM: 1.0,
        DifficultyLevel.HARD: 0.6,
    },
    SportLevel.ADVANCED: {
        DifficultyLevel.EASY: 0.3,
        DifficultyLevel.MEDIUM: 0.8,
        DifficultyLevel.HARD: 1.0,
    },
    SportLevel.EXPERT: {
        DifficultyLevel.EASY: 0.2,
        DifficultyLevel.MEDIUM: 0.6,
        DifficultyLevel.HARD: 1.0,
    },
}


# ============================================================
# SOUS-SCORES
# ============================================================

def _goal_score(
    exercise: Exercise,
    goal: Optional[GoalType],
    sport_goal_relevance: Optional[float] = None,
) -> float:
    """Meilleure correspondance entre les training_types de l'exercice
    et ceux valorises pour l'objectif. NEUTRAL_SCORE si l'objectif ou les
    training_types manquent (ne jamais bloquer une recommandation faute
    de donnee).

    Si `sport_goal_relevance` est fourni (SportGoalMatrix : a quel point
    cet objectif est pertinent pour le sport pratique, ex. "endurance"
    n'a que 0.20 de pertinence pour "musculation"), le score de base est
    module par cette pertinence -- un objectif mal adapte au sport
    pratique ne doit pas peser autant qu'un objectif bien adapte, sans
    pour autant tomber a 0 (l'utilisateur reste libre de viser un
    objectif atypique pour son sport). Melange multiplicatif borne a
    [0.5, 1.0] : 0.5 + 0.5 x relevance."""

    if goal is None or not exercise.training_types:
        return NEUTRAL_SCORE

    weights = GOAL_TRAINING_TYPE_WEIGHTS.get(goal, {})
    if not weights:
        return NEUTRAL_SCORE

    matches = [weights.get(t, 0.0) for t in exercise.training_types]
    base_score = max(matches) if matches else 0.0

    if sport_goal_relevance is not None:
        base_score *= 0.5 + 0.5 * max(0.0, min(1.0, sport_goal_relevance))

    return base_score


def _sport_score(exercise: Exercise, sport_slug: Optional[str]) -> float:
    """
    1.0 si l'exercice appartient explicitement au sport pratique.
    0.5 si l'exercice est generique (pas de sport associe, ex: marche,
    etirements) : jamais exclu, juste moins specifique.
    Sinon, correspondance via les training_types typiques du sport.
    """

    if exercise.sport is not None and sport_slug is not None:
        if exercise.sport.slug == sport_slug:
            return 1.0

    if exercise.sport_id is None:
        return 0.5

    if sport_slug is None or not exercise.training_types:
        return NEUTRAL_SCORE

    weights = SPORT_TRAINING_TYPE_WEIGHTS.get(sport_slug, {})
    matches = [weights.get(t, 0.0) for t in exercise.training_types]
    return max(matches) if matches else 0.0


def _level_score(exercise: Exercise, level: Optional[SportLevel]) -> float:
    if level is None or exercise.difficulty is None:
        return NEUTRAL_SCORE
    return LEVEL_DIFFICULTY_WEIGHTS.get(level, {}).get(exercise.difficulty, 0.3)


def _availability_score(frequency_per_week: Optional[int], sessions_last_7_days: int) -> float:
    """
    1.0 si l'utilisateur n'a pas encore atteint sa frequence visee cette
    semaine (on doit l'encourager a s'entrainer aujourd'hui), 0.5 s'il
    l'a deja atteinte ou depassee (seance encore possible mais moins
    prioritaire), NEUTRAL_SCORE si aucune frequence n'est definie.
    """

    if frequency_per_week is None or frequency_per_week <= 0:
        return NEUTRAL_SCORE
    return 1.0 if sessions_last_7_days < frequency_per_week else 0.5


def _history_score(exercise: Exercise, recent_exercise_ids: set[uuid.UUID]) -> float:
    """
    Favorise la variete : penalise legerement un exercice deja fait lors
    de la toute derniere seance, pour eviter de repeter systematiquement
    les memes mouvements.
    """

    return 0.6 if exercise.id in recent_exercise_ids else 1.0


def _recovery_score(recovery_score: Optional[float]) -> float:
    """Placeholder en attendant le vrai Recovery Score (etape 8)."""

    if recovery_score is None:
        return NEUTRAL_SCORE
    return max(0.0, min(1.0, recovery_score))


# ============================================================
# SCORE GLOBAL D'UN EXERCICE
# ============================================================

def _activity_level_for_user(db: Session, user_id: uuid.UUID):
    """Niveau d'activite du profil (evite un import circulaire avec
    weekly_scheduler, qui importe ce module)."""
    profile = (
        db.execute(select(Profile).where(Profile.user_id == user_id))
        .scalar_one_or_none()
    )
    return profile.activity_level if profile else None


def score_exercise(
    exercise: Exercise,
    *,
    goal: Optional[GoalType],
    sport_slug: Optional[str],
    level: Optional[SportLevel],
    frequency_per_week: Optional[int],
    sessions_last_7_days: int,
    recent_exercise_ids: set[uuid.UUID],
    recovery_score: Optional[float],
    sport_goal_relevance: Optional[float] = None,
) -> dict:
    """Retourne le score global (0-1) et le detail de chaque sous-score,
    pour permettre au frontend d'expliquer une recommandation."""

    breakdown = {
        "goal": _goal_score(exercise, goal, sport_goal_relevance),
        "sport": _sport_score(exercise, sport_slug),
        "level": _level_score(exercise, level),
        "availability": _availability_score(frequency_per_week, sessions_last_7_days),
        "history": _history_score(exercise, recent_exercise_ids),
        "recovery": _recovery_score(recovery_score),
    }

    total = sum(breakdown[key] * weight for key, weight in SCORE_WEIGHTS.items())

    return {"score": round(total, 4), "breakdown": breakdown}


# ============================================================
# RECOMMANDATION DE SEANCE
# ============================================================

def recommend_exercises(
    db: Session,
    user_id: uuid.UUID,
    goal: Optional[GoalType] = None,
    target_count: int = 6,
    recovery_score: Optional[float] = None,
    preferred_categories: Optional[list[str]] = None,
    preferred_types: Optional[list[TrainingType]] = None,
    exclude_exercise_ids: Optional[set[uuid.UUID]] = None,
) -> list[dict]:
    """
    Recommande jusqu'a `target_count` exercices, tries par score
    decroissant. Fonctionne pour un utilisateur non-sportif (sport_slug
    et level restent None -> uniquement les exercices generiques comme
    marche/etirements remontent avec un bon score via _sport_score,
    aucune erreur n'est levee).
    """

    primary = get_primary_sport(db, user_id)
    sport_slug = primary.sport.slug if primary and primary.sport else None
    level = primary.level if primary else None
    frequency_per_week = primary.frequency_per_week if primary else None

    # Pertinence sport x objectif (SportGoalMatrix), calculee une seule
    # fois par appel puisqu'elle ne depend pas de l'exercice -- voir
    # _goal_score. None si le sport/objectif n'est pas encore dans la
    # matrice (ex. sport hors des 10 seedes) : aucun impact, la
    # recommandation continue de fonctionner comme avant.
    goal_slug = GOAL_TYPE_TO_GOAL_SLUG.get(goal) if goal else None
    sport_goal_relevance = get_sport_goal_relevance(db, sport_slug, goal_slug)

    load = get_recent_training_load(db, user_id, days=7)
    sessions_last_7_days = load["total_sessions"]

    recent_logs = get_recent_workout_logs(db, user_id, days=3)
    recent_exercise_ids = {
        we.exercise_id for log in recent_logs for we in log.exercises
    }
    if exclude_exercise_ids:
        recent_exercise_ids = recent_exercise_ids | exclude_exercise_ids

    candidates = list_exercises(db, sport_slug=sport_slug if sport_slug else None)
    # Si un sport est pratique, on inclut aussi les exercices generiques
    # (sans sport) pour ne pas se limiter aux seuls exercices du catalogue
    # de ce sport (ex: etirements en complement de la musculation).
    if sport_slug is not None:
        candidates = list(candidates) + [
            e for e in list_exercises(db, sport_slug=None) if e.sport_id is None
        ]

    scored = []
    for exercise in candidates:
        result = score_exercise(
            exercise,
            goal=goal,
            sport_slug=sport_slug,
            level=level,
            frequency_per_week=frequency_per_week,
            sessions_last_7_days=sessions_last_7_days,
            recent_exercise_ids=recent_exercise_ids,
            recovery_score=recovery_score,
            sport_goal_relevance=sport_goal_relevance,
        )
        base_score = result["score"]
        # Bonus si l'exercice colle au split/thème du jour (catégories ciblées ou types ciblés)
        if preferred_categories and exercise.category in preferred_categories:
            base_score += 0.25
        if preferred_types and exercise.training_types:
            if any(t in preferred_types for t in exercise.training_types):
                base_score += 0.20

        scored.append({"exercise": exercise, "score": round(base_score, 4), "breakdown": result["breakdown"]})

    scored.sort(key=lambda item: item["score"], reverse=True)

    # Deduplique (un exercice generique peut apparaitre deux fois si le
    # catalogue par sport le retournait deja).
    seen: set[uuid.UUID] = set()
    unique_scored = []
    for item in scored:
        if item["exercise"].id in seen:
            continue
        seen.add(item["exercise"].id)
        unique_scored.append(item)

    return unique_scored[:target_count]


# ============================================================
# ASSEMBLAGE D'UNE SEANCE COMPLETE (echauffement + corps + retour au calme)
# ============================================================
# Module Sport, partie 4 : Workout = Warmup + Exercise 1..N + Cooldown.
# recommend_exercises() classe des exercices individuels ; les fonctions
# ci-dessous les assemblent en une seance structuree et prescrite
# (series/reps/charge ou duree/distance selon le type d'exercice).

# Types consideres "a charge" (series x repetitions x poids). Le reste
# (cardio, technique, mobilite...) se prescrit en duree/distance.
#
# POWER est volontairement absent seul : un mouvement charge type
# souleve de terre a deja STRENGTH/HYPERTROPHY en plus de POWER, donc
# il reste "a charge" via ces types. POWER seul (ex: sprint, plyo)
# decrit un effort explosif mesure en duree/distance, pas en charge --
# l'inclure ici faisait remonter des prescriptions absurdes du type
# "3 x 15-20 reps" pour un sprint (repere en test manuel, etape 6).
LOAD_BASED_TYPES = {TrainingType.STRENGTH, TrainingType.HYPERTROPHY}

# Types recherches en priorite pour l'echauffement / le retour au calme.
WARMUP_TYPES = {TrainingType.MOBILITY}
COOLDOWN_TYPES = {TrainingType.RECOVERY, TrainingType.MOBILITY}

# Plage de repetitions par objectif pour les exercices "a charge" (le
# haut de la plage est retenu par defaut ; l'algorithme de progression
# de l'etape 7 affinera a partir de l'historique reel de l'utilisateur).
REP_RANGE_BY_GOAL: dict[GoalType, tuple[int, int]] = {
    GoalType.STRENGTH: (4, 6),
    GoalType.MUSCLE_GAIN: (8, 12),
    GoalType.BODY_RECOMPOSITION: (8, 12),
    GoalType.WEIGHT_LOSS: (12, 15),
    GoalType.ENDURANCE: (15, 20),
    GoalType.PERFORMANCE: (5, 8),
    GoalType.GENERAL_HEALTH: (10, 15),
    GoalType.MAINTENANCE: (10, 12),
}
DEFAULT_REP_RANGE = (10, 12)

# Nombre de series par defaut, module par le niveau.
SETS_BY_LEVEL: dict[SportLevel, int] = {
    SportLevel.BEGINNER: 2,
    SportLevel.INTERMEDIATE: 3,
    SportLevel.ADVANCED: 4,
    SportLevel.EXPERT: 4,
}
DEFAULT_SETS = 3

# Duree ciblee (secondes) pour un exercice "a duree", modulee par le
# niveau. Grossier mais suffisant tant qu'aucun historique (allure,
# distance passees) n'est disponible pour affiner -- role de l'etape 7.
DURATION_SECONDS_BY_LEVEL: dict[SportLevel, int] = {
    SportLevel.BEGINNER: 5 * 60,
    SportLevel.INTERMEDIATE: 8 * 60,
    SportLevel.ADVANCED: 12 * 60,
    SportLevel.EXPERT: 15 * 60,
}
DEFAULT_DURATION_SECONDS = 8 * 60

REST_SECONDS_BY_TRAINING_TYPE: dict[TrainingType, int] = {
    TrainingType.STRENGTH: 120,
    TrainingType.POWER: 120,
    TrainingType.HYPERTROPHY: 90,
}
DEFAULT_REST_SECONDS = 60

# Ajustement du temps de repos selon l'objectif (regle du cahier des
# charges, module Sport : "lose-fat -> reduction des temps de repos",
# "build-muscle -> temps de repos allonges + focus charge/tension
# mecanique"). Applique en plus de REST_SECONDS_BY_TRAINING_TYPE, jamais
# a la place -- multiplicateur, pas une nouvelle table de valeurs
# absolues, pour ne jamais dupliquer la logique existante.
GOAL_REST_MULTIPLIER: dict[GoalType, float] = {
    GoalType.WEIGHT_LOSS: 0.7,
    GoalType.BODY_RECOMPOSITION: 0.85,
    GoalType.MUSCLE_GAIN: 1.15,
    GoalType.STRENGTH: 1.2,
}
DEFAULT_REST_MULTIPLIER = 1.0

# Objectifs pour lesquels un finisher cardio/HIIT court est ajoute en
# fin de seance a charge (regle : "lose-fat -> ajout de finisseurs
# cardio 5-10 min HIIT").
FINISHER_GOALS = {GoalType.WEIGHT_LOSS, GoalType.BODY_RECOMPOSITION}
FINISHER_DURATION_MINUTES = 6
FINISHER_PREFERRED_SLUGS = ("burpees_cardio", "jumping_jacks", "corde_a_sauter")
PERFORMANCE_POWER_SLUGS = (
    "sauts_verticaux",
    "box_jumps",
    "sprint",
    "medball_chest_pass",
    "pompes_explosives",
    "depth_jumps",
)
HEALTHY_COOLDOWN_SLUGS = ("travail_postural", "respiration_diaphragmatique", "etirements")
MUSCLE_TEMPO = "3s descente / 1s montée"

WARMUP_DURATION_MINUTES = 8
COOLDOWN_DURATION_MINUTES = 6
HEALTHY_COOLDOWN_MINUTES = 12

# RPE cible par niveau (module Sport, partie 8) : point de depart de
# l'algorithme d'intensite complet, que le Recovery Score de l'etape 8
# viendra ensuite moduler plus finement (fatigue, charge recente...).
BASE_RPE_BY_LEVEL: dict[SportLevel, float] = {
    SportLevel.BEGINNER: 5.0,
    SportLevel.INTERMEDIATE: 6.5,
    SportLevel.ADVANCED: 7.5,
    SportLevel.EXPERT: 8.0,
}
DEFAULT_BASE_RPE = 6.0


def is_load_based(exercise: Exercise) -> bool:
    """True si l'exercice se prescrit en series x repetitions x charge,
    False s'il se prescrit en duree/distance (cardio, technique...).
    Sans training_types connus, on prescrit par defaut en duree : c'est
    l'option la plus sure pour un exercice generique (ex: marche)."""

    if not exercise.training_types:
        return False
    return any(t in LOAD_BASED_TYPES for t in exercise.training_types)


def _target_rpe(level: Optional[SportLevel], recovery_score: Optional[float]) -> float:
    """
    RPE cible pour la seance : base sur le niveau, puis ajuste a la
    baisse si la recuperation est mauvaise (module Sport, partie 8 :
    'ne jamais augmenter automatiquement l'intensite de maniere
    dangereuse'). recovery_score reste un placeholder (etape 8) tant
    qu'il n'est pas fourni.
    """

    base = BASE_RPE_BY_LEVEL.get(level, DEFAULT_BASE_RPE) if level else DEFAULT_BASE_RPE

    if recovery_score is None:
        return round(base, 1)

    recovery_score = max(0.0, min(1.0, recovery_score))
    if recovery_score < 0.4:
        base -= 2.0
    elif recovery_score < 0.6:
        base -= 1.0

    return round(max(1.0, min(10.0, base)), 1)


def _prescribe_exercise(
    exercise: Exercise,
    *,
    goal: Optional[GoalType],
    level: Optional[SportLevel],
    session_rpe: float,
    exact_sets: Optional[int] = None,
    exact_reps: Optional[int] = None,
    exact_duration_seconds: Optional[int] = None,
    item_note: Optional[str] = None,
) -> dict:
    """
    Construit la prescription d'un exercice pour la seance, au format
    des futurs WorkoutSet (partie 4/20) : target_reps, target_weight_kg,
    target_duration_seconds, target_distance_m, rest_seconds, target_rpe.
    Prend en compte les prescriptions canoniques précises de la séance (sets, reps, durée, note)
    ainsi que les 4 adaptations de tempo et repos par objectif (build-muscle, lose-fat...).
    """

    dominant_type = exercise.training_types[0] if exercise.training_types else None

    if is_load_based(exercise):
        low, high = REP_RANGE_BY_GOAL.get(goal, DEFAULT_REP_RANGE)
        num_sets = exact_sets if exact_sets is not None else (SETS_BY_LEVEL.get(level, DEFAULT_SETS) if level else DEFAULT_SETS)
        target_reps = exact_reps if exact_reps is not None else high

        # Repos selon l'objectif :
        # - lose-fat : temps de repos réduits à 45-60s (environ 50-60s)
        # - build-muscle : temps de repos allongés (1m30 à 2m30, soit 90-150s)
        if goal == GoalType.WEIGHT_LOSS:
            rest = 50
        elif goal == GoalType.MUSCLE_GAIN:
            base_rest = REST_SECONDS_BY_TRAINING_TYPE.get(dominant_type, 90)
            rest = max(100, round(base_rest * 1.25))
        else:
            base_rest = REST_SECONDS_BY_TRAINING_TYPE.get(dominant_type, DEFAULT_REST_SECONDS)
            rest = round(base_rest * GOAL_REST_MULTIPLIER.get(goal, DEFAULT_REST_MULTIPLIER))

        sets = [
            {
                "set_number": i + 1,
                "target_reps": target_reps,
                "target_weight_kg": None,
                "target_duration_seconds": None,
                "target_distance_m": None,
                "rest_seconds": rest,
                "target_rpe": session_rpe,
            }
            for i in range(num_sets)
        ]

        if exact_reps is not None:
            prescription_note = f"{num_sets} x {exact_reps} reps"
        else:
            prescription_note = f"{num_sets} x {low}-{high} reps"

        if item_note:
            prescription_note = f"{prescription_note} ({item_note})"

        # Adaptation build-muscle : Tempo d'exécution contrôlé (3s descente / 1s montée)
        if goal in (GoalType.MUSCLE_GAIN, GoalType.BODY_RECOMPOSITION):
            prescription_note = f"{prescription_note} · Tempo: {MUSCLE_TEMPO}"
    else:
        duration = (
            exact_duration_seconds
            if exact_duration_seconds is not None
            else (
                DURATION_SECONDS_BY_LEVEL.get(level, DEFAULT_DURATION_SECONDS)
                if level
                else DEFAULT_DURATION_SECONDS
            )
        )
        sets = [
            {
                "set_number": 1,
                "target_reps": None,
                "target_weight_kg": None,
                "target_duration_seconds": duration,
                "target_distance_m": None,
                "rest_seconds": None,
                "target_rpe": session_rpe,
            }
        ]
        if duration >= 60:
            prescription_note = f"{duration // 60} min"
        else:
            prescription_note = f"{duration}s"

        if item_note:
            prescription_note = f"{prescription_note} ({item_note})"

    return {"exercise": exercise, "sets": sets, "prescription_note": prescription_note}


def _pick_bookend_exercise(
    db: Session, wanted_types: set[TrainingType], exclude_ids: set[uuid.UUID]
) -> Optional[Exercise]:
    """
    Cherche un exercice generique (sans sport associe) correspondant a
    l'un des `wanted_types`, pour l'echauffement ou le retour au calme.
    Retourne None si le catalogue n'en a pas encore (etape 4/22) --
    l'appelant se rabat alors sur une consigne textuelle generique
    plutot que de faire echouer l'assemblage de la seance.
    """

    generic = list_exercises(db, sport_slug=None)
    candidates = [
        e
        for e in generic
        if e.sport_id is None
        and e.id not in exclude_ids
        and e.training_types
        and any(t in wanted_types for t in e.training_types)
    ]
    return candidates[0] if candidates else None


def recommend_workout(
    db: Session,
    user_id: uuid.UUID,
    goal: Optional[GoalType] = None,
    main_exercise_count: int = 5,
    recovery_score: Optional[float] = None,
    session_index: int = 0,
    exclude_exercise_ids: Optional[set[uuid.UUID]] = None,
    theme: Optional[dict] = None,
) -> dict:
    """
    Assemble une seance complete (echauffement + corps + retour au
    calme) a partir de recommend_exercises() (module Sport, partie 4 :
    Workout = Warmup + Exercise 1..N + Cooldown).

    Si `theme` est fourni (ex: par training_programs.build_training_day_sequence
    via weekly_scheduler.py), il est utilise directement -- structure
    exacte du jour voulue (ex: "Push", "Full-Body A", "VMA/Interval").
    Sinon, retombe sur la rotation cyclique existante (session_index)
    selon le sport et l'objectif, pour ne jamais casser les appels
    existants qui ne connaissent pas encore la notion de programme
    complet (frequence + niveau).
    """

    primary = get_primary_sport(db, user_id)
    sport_slug = primary.sport.slug if primary and primary.sport else None
    level = primary.level if primary else None

    session_rpe = _target_rpe(level, recovery_score)

    if theme is None:
        # Fallback deriver de la sequence de branches (training_programs,
        # meme source de verite que build_training_day_sequence), remplace
        # l'ancien training_splits.py insensible a la frequence/niveau.
        primary = get_primary_sport(db, user_id)
        theme = get_sport_session_theme(
            primary.sport.slug if primary and primary.sport else None,
            _activity_level_for_user(db, user_id),
            primary.level if primary else None,
            primary.frequency_per_week if primary and primary.frequency_per_week else 3,
            goal,
            session_index=session_index,
        )
    preferred_categories = theme.get("categories") if theme else None
    preferred_types = theme.get("types") if theme else None

    # Extraction des items canoniques de la séance si disponibles
    canonical_items = theme_exercise_items(theme, sport_slug) if theme else []
    used_ids: set[uuid.UUID] = set()

    # 1. Warmup (soit canonique du thème, soit générique)
    warmup_exercise = None
    warmup_duration = WARMUP_DURATION_MINUTES
    warmup_instruction = "Échauffement dynamique général, 5-10 min"
    if theme and theme.get("warmup"):
        w_slugs = [item["slug"] for item in theme["warmup"] if "slug" in item]
        w_objs = get_exercises_by_slugs(db, w_slugs)
        if w_objs:
            warmup_exercise = w_objs[0]
            used_ids.add(warmup_exercise.id)
            first_w = theme["warmup"][0]
            if first_w.get("duration_seconds"):
                warmup_duration = max(3, round(first_w["duration_seconds"] / 60))
    if not warmup_exercise:
        warmup_exercise = _pick_bookend_exercise(db, WARMUP_TYPES, used_ids)
        if warmup_exercise is not None:
            used_ids.add(warmup_exercise.id)

    # 2. Cooldown (soit canonique du thème, soit adaptation healthy-lifestyle 10-15 min, soit générique)
    cooldown_exercise = None
    cooldown_duration = COOLDOWN_DURATION_MINUTES
    cooldown_instruction = "Étirements / retour au calme, 5-10 min"

    if goal in (GoalType.GENERAL_HEALTH, GoalType.MAINTENANCE):
        # Adaptation healthy-lifestyle : 10-15 min fin de séance dédiées travail postural / respiration / mobilité
        h_objs = get_exercises_by_slugs(db, list(HEALTHY_COOLDOWN_SLUGS))
        if h_objs:
            cooldown_exercise = h_objs[0]
            cooldown_duration = HEALTHY_COOLDOWN_MINUTES
            cooldown_instruction = "Travail postural, respiration diaphragmatique & mobilité articulaire (10-15 min)"
            used_ids.add(cooldown_exercise.id)
    elif theme and theme.get("cooldown"):
        c_slugs = [item["slug"] for item in theme["cooldown"] if "slug" in item]
        c_objs = get_exercises_by_slugs(db, c_slugs)
        if c_objs:
            cooldown_exercise = c_objs[0]
            used_ids.add(cooldown_exercise.id)
            first_c = theme["cooldown"][0]
            if first_c.get("duration_seconds"):
                cooldown_duration = max(3, round(first_c["duration_seconds"] / 60))

    if not cooldown_exercise:
        cooldown_exercise = _pick_bookend_exercise(db, COOLDOWN_TYPES, used_ids)
        if cooldown_exercise is not None:
            used_ids.add(cooldown_exercise.id)

    # 3. Exercices principaux
    main_prescriptions = []

    if canonical_items:
        # Parcours fidèle de la séance définie dans le répertoire
        c_slugs = [it["slug"] for it in canonical_items if "slug" in it]
        c_exercises = get_exercises_by_slugs(db, c_slugs)
        c_ex_map = {e.slug: e for e in c_exercises}

        for item in canonical_items:
            slug = item.get("slug")
            ex_obj = c_ex_map.get(slug)
            if ex_obj:
                used_ids.add(ex_obj.id)
                prescription = _prescribe_exercise(
                    ex_obj,
                    goal=goal,
                    level=level,
                    session_rpe=session_rpe,
                    exact_sets=item.get("sets"),
                    exact_reps=item.get("reps"),
                    exact_duration_seconds=item.get("duration_seconds"),
                    item_note=item.get("note"),
                )
                main_prescriptions.append(prescription)

    # Si aucun item canonique ou séance incomplète, fallback sur le moteur de scoring
    if len(main_prescriptions) < main_exercise_count and not canonical_items:
        candidate_pool_size = main_exercise_count + 8
        scored = recommend_exercises(
            db,
            user_id,
            goal=goal,
            target_count=candidate_pool_size,
            recovery_score=recovery_score,
            preferred_categories=preferred_categories,
            preferred_types=preferred_types,
            exclude_exercise_ids=exclude_exercise_ids,
        )
        for item in scored:
            if item["exercise"].id not in used_ids:
                used_ids.add(item["exercise"].id)
                main_prescriptions.append(
                    _prescribe_exercise(item["exercise"], goal=goal, level=level, session_rpe=session_rpe)
                )
                if len(main_prescriptions) >= main_exercise_count:
                    break

    # Adaptation improve-performance : Intégration systématique d'exercices d'explosivité en début de séance
    if goal == GoalType.PERFORMANCE:
        power_slugs = list(PERFORMANCE_POWER_SLUGS)
        if theme and theme.get("power_exercises"):
            power_slugs = theme["power_exercises"] + power_slugs
        # Si aucun exercice d'explosivité n'est présent en tête, on en insère un
        has_power_in_session = any(
            p["exercise"].slug in power_slugs or
            (p["exercise"].training_types and TrainingType.POWER in p["exercise"].training_types)
            for p in main_prescriptions
        )
        if not has_power_in_session:
            power_candidates = get_exercises_by_slugs(db, power_slugs)
            p_obj = next((e for e in power_candidates if e.id not in used_ids), None)
            if p_obj:
                used_ids.add(p_obj.id)
                p_presc = _prescribe_exercise(
                    p_obj,
                    goal=goal,
                    level=level,
                    session_rpe=session_rpe,
                    exact_sets=3,
                    exact_reps=5,
                    item_note="Explosivité début de séance",
                )
                main_prescriptions.insert(0, p_presc)

    # Adaptation lose-fat : Finisseur métabolique de 5-8 min en fin de séance
    # (Burpees, Jumping Jacks, Corde à sauter)
    finisher = None
    if goal in FINISHER_GOALS:
        finisher_candidates = get_exercises_by_slugs(db, list(FINISHER_PREFERRED_SLUGS))
        finisher_obj = next((e for e in finisher_candidates if e.id not in used_ids), None)
        if not finisher_obj:
            generic_cardio = [
                e for e in list_exercises(db, sport_slug=None)
                if e.sport_id is None and e.id not in used_ids and e.training_types
                and any(t in {TrainingType.INTERVAL, TrainingType.CARDIO} for t in e.training_types)
            ]
            if generic_cardio:
                finisher_obj = generic_cardio[0]

        if finisher_obj:
            finisher = {
                "exercise": finisher_obj,
                "duration_minutes": FINISHER_DURATION_MINUTES,
                "note": "Finisseur métabolique 5-8 min HIIT (temps de repos réduits à 45-60s)",
            }

    main_duration_minutes = 0.0
    for prescription in main_prescriptions:
        for workout_set in prescription["sets"]:
            if workout_set["target_duration_seconds"] is not None:
                main_duration_minutes += workout_set["target_duration_seconds"] / 60
            else:
                main_duration_minutes += 0.75
            if workout_set["rest_seconds"]:
                main_duration_minutes += workout_set["rest_seconds"] / 60

    planned_duration_minutes = round(
        (warmup_duration if warmup_exercise else 0)
        + main_duration_minutes
        + (finisher["duration_minutes"] if finisher else 0)
        + (cooldown_duration if cooldown_exercise else 0)
    )

    # Type d'entrainement dominant de la seance : le plus frequent parmi
    # les training_types des exercices principaux retenus.
    type_counts: dict[TrainingType, int] = {}
    for item in main_prescriptions:
        for t in item["exercise"].training_types or []:
            type_counts[t] = type_counts.get(t, 0) + 1
    dominant_training_type = max(type_counts, key=type_counts.get) if type_counts else None
    if preferred_types and preferred_types[0] in type_counts:
        dominant_training_type = preferred_types[0]

    difficulty_by_level = {
        SportLevel.BEGINNER: DifficultyLevel.EASY,
        SportLevel.INTERMEDIATE: DifficultyLevel.MEDIUM,
        SportLevel.ADVANCED: DifficultyLevel.HARD,
        SportLevel.EXPERT: DifficultyLevel.HARD,
    }

    session_name = theme.get("name") if theme else None

    return {
        "sport_slug": sport_slug,
        "goal": goal,
        "level": level,
        "training_type": dominant_training_type,
        "difficulty": difficulty_by_level.get(level) if level else None,
        "planned_duration_minutes": planned_duration_minutes,
        "target_rpe": session_rpe,
        # Laisse a None deliberement : l'estimation des calories brulees
        # se branchera sur le moteur nutritionnel existant a l'etape 9
        # (module Sport, parties 15/17), pas de calcul invente ici.
        "estimated_calories_kcal": None,
        "session_name": session_name,
        "warmup": (
            {"exercise": warmup_exercise, "duration_minutes": warmup_duration, "instruction": warmup_instruction}
            if warmup_exercise
            else {
                "exercise": None,
                "instruction": warmup_instruction,
                "duration_minutes": warmup_duration,
            }
        ),
        "exercises": main_prescriptions,
        "finisher": finisher,
        "cooldown": (
            {"exercise": cooldown_exercise, "duration_minutes": cooldown_duration, "instruction": cooldown_instruction}
            if cooldown_exercise
            else {
                "exercise": None,
                "instruction": cooldown_instruction,
                "duration_minutes": cooldown_duration,
            }
        ),
    }
