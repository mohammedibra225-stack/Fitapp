import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
    ActivityIndicator,
    Alert,
    RefreshControl,
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

import DayBox from '../components/DayBox';
import MacroCard from '../components/MacroCard';
import ExerciseSection from '../components/ExerciseSection';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

const WEEKDAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

const EXERCISE_ICONS = ['weight-lifter', 'arm-flex-outline', 'human-handsup', 'dumbbell'];
const EXERCISE_COLORS = [colors.primary, colors.teal, colors.orange, colors.blue];
const EXERCISE_BACKGROUNDS = [colors.primaryLight, colors.tealLight, colors.orangeLight, colors.blueLight];

// Traduction des activites Lifestyle suggerees par le backend (slugs
// fixes definis dans lifestyle_service.SUGGESTED_ACTIVITIES) : le
// backend ne renvoie qu'un libelle FR statique, donc on retraduit ici
// a partir du slug, avec repli sur le libelle brut si jamais un
// nouveau slug apparait cote serveur.
const ACTIVITY_LABEL_KEYS = {
    marche_10: 'training.activity_marche_10',
    marche_15: 'training.activity_marche_15',
    marche_30: 'training.activity_marche_30',
    mobilite_10: 'training.activity_mobilite_10',
    etirements_10: 'training.activity_etirements_10',
    petite_promenade: 'training.activity_petite_promenade',
    repos: 'training.rest',
};

// Construit le payload de series a envoyer au backend a partir d'un
// item recommande (module Sport, partie 4/20). Les echauffements/
// retours au calme n'ont pas toujours de "sets" detailles -> un seul
// bloc base sur leur duree.
function buildSetsPayload(item) {
    if (item.sets && item.sets.length) {
        return item.sets.map((s) => ({
            reps: s.target_reps ?? undefined,
            weight_kg: s.target_weight_kg ?? undefined,
            duration_seconds: s.target_duration_seconds ?? undefined,
            distance_m: s.target_distance_m ?? undefined,
            rest_seconds: s.rest_seconds ?? undefined,
            rpe: s.target_rpe ?? undefined,
        }));
    }
    if (item.duration_minutes) {
        return [{ duration_seconds: Math.round(item.duration_minutes * 60) }];
    }
    return [{}];
}

export default function TrainingScreen() {
    const [activeDay, setActiveDay] = useState(0);
    const [recommendation, setRecommendation] = useState(null);
    const [recovery, setRecovery] = useState(null);
    const [weeklyProgram, setWeeklyProgram] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const [doneSlugs, setDoneSlugs] = useState(new Set());
    const [savingSlugs, setSavingSlugs] = useState(new Set());
    const [localDone, setLocalDone] = useState(new Set());
    const [lifestyleToday, setLifestyleToday] = useState(null);
    const [nutritionToday, setNutritionToday] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isCompletingAll, setIsCompletingAll] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isLoggingActivity, setIsLoggingActivity] = useState(false);
    const { t, language } = useI18n();
    const { user } = useUser();

    const loadWorkout = useCallback(async () => {
        if (!user?.userId) {
            setIsLoading(false);
            return;
        }
        try {
            const lang = language || 'fr';
            const results = await Promise.allSettled([
                apiRequest(`/workouts/recommended/${user.userId}?language=${lang}`),
                apiRequest(`/workouts/sessions/${user.userId}?days=1`),
                apiRequest(`/lifestyle/today/${user.userId}`),
                apiRequest(`/nutrition-tracking/daily/${user.userId}`),
                apiRequest(`/programs/weekly/${user.userId}?language=${lang}`),
            ]);
            const [recoResult, sessionsResult, lifestyleResult, nutritionResult, weeklyResult] = results;

            if (recoResult.status === 'fulfilled') {
                setRecommendation(recoResult.value.recommendation);
                setRecovery(recoResult.value.recovery);
            } else {
                Alert.alert(t('navigation.training'), recoResult.reason?.message || t('training.error_load'));
            }

            const todayISO = new Date().toISOString().slice(0, 10);
            const todaysLog = sessionsResult.status === 'fulfilled'
                ? sessionsResult.value.find((log) => log.performed_at?.slice(0, 10) === todayISO)
                : null;
            setSessionId(todaysLog ? todaysLog.id : null);
            setDoneSlugs(new Set(todaysLog ? todaysLog.exercises.map((e) => e.exercise_slug) : []));

            if (lifestyleResult.status === 'fulfilled') setLifestyleToday(lifestyleResult.value);
            if (nutritionResult.status === 'fulfilled') setNutritionToday(nutritionResult.value);
            if (weeklyResult.status === 'fulfilled') setWeeklyProgram(weeklyResult.value);
        } finally {
            setIsLoading(false);
        }
    }, [user?.userId, language, t]);

    useEffect(() => {
        loadWorkout();
    }, [loadWorkout]);

    const refreshPage = async () => {
        setIsRefreshing(true);
        await loadWorkout();
        setIsRefreshing(false);
    };

    // ------------------------------------------------------------
    // Traduction des types d'entrainement / niveaux de recuperation
    // (enums renvoyes tels quels par le backend, non traduits cote
    // serveur) et des activites Lifestyle suggerees / jours de repos.
    // ------------------------------------------------------------
    const translateTrainingType = useCallback((type) => (type ? t(`training.type_${type}`) : null), [t]);
    const translateRecoveryLevel = useCallback((level) => (level ? t(`training.recovery_level_${level}`) : level), [t]);
    const translateActivityLabel = useCallback((activity) => {
        if (!activity) return '';
        const key = ACTIVITY_LABEL_KEYS[activity.slug];
        return key ? t(key) : activity.label;
    }, [t]);
    const translateActivitySlug = useCallback((slug) => {
        const key = ACTIVITY_LABEL_KEYS[slug];
        return key ? t(key) : slug;
    }, [t]);

    // ------------------------------------------------------------
    // Logging d'un exercice, echauffement ou retour au calme
    // ------------------------------------------------------------
    const logExercise = useCallback(async (slug, sets) => {
        if (!user?.userId || !slug) return;
        setSavingSlugs((prev) => new Set(prev).add(slug));
        try {
            let updatedLog;
            if (sessionId) {
                updatedLog = await apiRequest(`/workouts/logs/${user.userId}`, {
                    method: 'POST',
                    body: JSON.stringify({ workout_log_id: sessionId, exercise_slug: slug, sets }),
                });
            } else {
                updatedLog = await apiRequest(`/workouts/sessions/${user.userId}`, {
                    method: 'POST',
                    body: JSON.stringify({ exercises: [{ exercise_slug: slug, sets }] }),
                });
                setSessionId(updatedLog.id);
            }
            setDoneSlugs(new Set(updatedLog.exercises.map((e) => e.exercise_slug)));
        } catch (error) {
            Alert.alert(t('navigation.training'), error.message);
        } finally {
            setSavingSlugs((prev) => {
                const next = new Set(prev);
                next.delete(slug);
                return next;
            });
        }
    }, [user?.userId, sessionId, t]);

    const handleItemPress = useCallback((item) => {
        const slug = item.exercise?.slug;
        if (!slug) {
            // Instruction generique sans exercice catalogue (ex: "Etirements
            // generaux 5-10 min") : pas de exercise_slug a logger cote
            // backend, on garde juste une coche visuelle locale.
            setLocalDone((prev) => {
                const next = new Set(prev);
                if (next.has(item.key)) next.delete(item.key); else next.add(item.key);
                return next;
            });
            return;
        }
        if (doneSlugs.has(slug) || savingSlugs.has(slug)) return;
        logExercise(slug, buildSetsPayload(item));
    }, [doneSlugs, savingSlugs, logExercise]);

    // Un jour autre qu'aujourd'hui est un apercu en lecture seule :
    // aucun WorkoutLog n'a de sens pour un jour passe/futur. On le
    // signale a l'utilisateur au lieu de laisser le bouton muet.
    const handlePreviewItemPress = useCallback(() => {
        Alert.alert(t('navigation.training'), t('training.preview_locked'));
    }, [t]);

    // ------------------------------------------------------------
    // Suggestion Lifestyle : "Commencer" logue reellement l'activite
    // (POST /lifestyle/activity) quand elle a une duree, sinon on se
    // contente de la marquer comme faite (ex: repos, petite promenade).
    // ------------------------------------------------------------
    const startSuggestedActivity = useCallback(async (activity) => {
        if (!user?.userId || !activity || isLoggingActivity) return;
        const label = translateActivityLabel(activity);

        if (!activity.duration_minutes) {
            Alert.alert(t('navigation.training'), t('training.activity_marked', { label }));
            return;
        }

        setIsLoggingActivity(true);
        try {
            const currentActivity = lifestyleToday?.activity || {};
            const updated = await apiRequest(`/lifestyle/activity/${user.userId}`, {
                method: 'POST',
                body: JSON.stringify({
                    steps: currentActivity.steps ?? undefined,
                    walking_duration_minutes: currentActivity.walking_duration_minutes ?? undefined,
                    distance_m: currentActivity.distance_m ?? undefined,
                    active_minutes: (currentActivity.active_minutes || 0) + activity.duration_minutes,
                }),
            });
            setLifestyleToday((prev) => (prev ? { ...prev, activity: { ...prev.activity, ...updated } } : prev));
            Alert.alert(t('navigation.training'), t('training.activity_logged', { label, minutes: activity.duration_minutes }));
        } catch (error) {
            Alert.alert(t('navigation.training'), error.message);
        } finally {
            setIsLoggingActivity(false);
        }
    }, [user?.userId, lifestyleToday, isLoggingActivity, translateActivityLabel, t]);

    // ------------------------------------------------------------
    // Construction de l'affichage a partir de la recommandation
    // ------------------------------------------------------------
    const mainItems = useMemo(
        () => (recommendation?.exercises || []).map((item, index) => ({ ...item, key: item.exercise?.slug || `main-${index}` })),
        [recommendation]
    );
    const warmupItem = recommendation?.warmup ? { ...recommendation.warmup, key: 'warmup' } : null;
    const cooldownItem = recommendation?.cooldown ? { ...recommendation.cooldown, key: 'cooldown' } : null;
    const finisherItem = recommendation?.finisher ? { ...recommendation.finisher, key: 'finisher' } : null;

    const isItemDone = (item) => (item.exercise?.slug ? doneSlugs.has(item.exercise.slug) : localDone.has(item.key));
    const isItemSaving = (item) => Boolean(item.exercise?.slug && savingSlugs.has(item.exercise.slug));

    const displayList = useMemo(() => {
        const rows = [];
        if (warmupItem) {
            rows.push({
                ...warmupItem,
                name: `${t('training.warmup')} · ${warmupItem.exercise?.name || warmupItem.instruction || ''}`,
                icon: 'weather-windy',
                iconColor: colors.blue,
                iconBackground: colors.blueLight,
                subtitle: `${warmupItem.duration_minutes || 0} min`,
            });
        }
        mainItems.forEach((item, index) => {
            rows.push({
                ...item,
                name: item.exercise?.name || t('training.exercise_default'),
                icon: EXERCISE_ICONS[index % EXERCISE_ICONS.length],
                iconColor: EXERCISE_COLORS[index % EXERCISE_COLORS.length],
                iconBackground: EXERCISE_BACKGROUNDS[index % EXERCISE_BACKGROUNDS.length],
                subtitle: item.prescription_note || t('training.sets_count', { count: item.sets?.length || 1 }),
            });
        });
        if (finisherItem) {
            rows.push({
                ...finisherItem,
                name: `${t('training.finisher_label')} · ${finisherItem.exercise?.name || finisherItem.instruction || ''}`,
                icon: 'fire',
                iconColor: colors.orange || colors.primary,
                iconBackground: colors.orangeLight || colors.blueLight,
                subtitle: `${finisherItem.duration_minutes || 0} min · ${t('training.hiit_label')}`,
            });
        }
        if (cooldownItem) {
            rows.push({
                ...cooldownItem,
                name: `${t('training.rest')} · ${cooldownItem.exercise?.name || cooldownItem.instruction || ''}`,
                icon: 'weather-night',
                iconColor: colors.teal,
                iconBackground: colors.tealLight,
                subtitle: `${cooldownItem.duration_minutes || 0} min`,
            });
        }
        return rows;
    }, [warmupItem, mainItems, finisherItem, cooldownItem, t]);

    const doneCount = mainItems.filter(isItemDone).length;
    const progressPercent = mainItems.length ? Math.round((doneCount / mainItems.length) * 100) : 0;
    const fullyDone = mainItems.length > 0 && doneCount === mainItems.length;
    const translatedTrainingType = translateTrainingType(recommendation?.training_type);
    const workoutTitle = recommendation?.session_name || translatedTrainingType || t('training.session_default');
    const lifestyleSuggestion = lifestyleToday?.suggested_activities?.[0];

    // ------------------------------------------------------------
    // Carte Calories : desormais entierement basee sur la seance du
    // jour (calories a BRULER), plus sur la nutrition. current/target
    // pilotent le fil de progression de la carte (calories brulees vs
    // objectif de la seance), et le sous-titre affiche le reliquat en
    // clair ("X kcal a perdre").
    // ------------------------------------------------------------
    const sessionCalorieTarget = Math.round(recommendation?.estimated_calories_kcal || 0);
    const sessionCaloriesBurned = fullyDone
        ? sessionCalorieTarget
        : Math.round(sessionCalorieTarget * (progressPercent / 100));
    const caloriesToBurn = Math.max(0, sessionCalorieTarget - sessionCaloriesBurned);
    const calorieCardProgress = sessionCalorieTarget
        ? Math.min(100, Math.round((sessionCaloriesBurned / sessionCalorieTarget) * 100))
        : 0;

    // ------------------------------------------------------------
    // Semaine (Weekly Scheduler, /programs/weekly) : la ligne de jours
    // pointe sur les 7 prochains jours reels a partir d'aujourd'hui
    // (index 0 = aujourd'hui, interactif via `recommendation` ci-dessus ;
    // index 1-6 = apercu en lecture seule tire de weeklyProgram, aucun
    // log possible -- WorkoutLog n'a de sens que pour "maintenant").
    // ------------------------------------------------------------
    const weekDates = useMemo(() => {
        const today = new Date();
        return Array.from({ length: 7 }, (_, i) => {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            return d;
        });
    }, []);

    const isToday = activeDay === 0;
    const previewDay = !isToday ? weeklyProgram?.days?.[activeDay] : null;
    const previewTrainingType = translateTrainingType(previewDay?.workout?.training_type);

    const previewItems = useMemo(() => {
        if (!previewDay) return [];

        if (previewDay.day_type === 'rest') {
            return (previewDay.activities || []).map((a, index) => ({
                key: `rest-${index}`,
                name: translateActivitySlug(a.exercise_slug),
                icon: 'walk',
                iconColor: colors.teal,
                iconBackground: colors.tealLight,
                subtitle: `${a.duration_minutes} min`,
            }));
        }

        const workout = previewDay.workout;
        if (!workout) return [];

        const rows = [];
        if (workout.warmup) {
            rows.push({
                key: 'preview-warmup',
                name: `${t('training.warmup')} · ${workout.warmup.exercise?.name || workout.warmup.instruction || ''}`,
                icon: 'weather-windy',
                iconColor: colors.blue,
                iconBackground: colors.blueLight,
                subtitle: `${workout.warmup.duration_minutes || 0} min`,
            });
        }
        (workout.exercises || []).forEach((item, index) => {
            rows.push({
                key: item.exercise?.slug || `preview-main-${index}`,
                name: item.exercise?.name || t('training.exercise_default'),
                icon: EXERCISE_ICONS[index % EXERCISE_ICONS.length],
                iconColor: EXERCISE_COLORS[index % EXERCISE_COLORS.length],
                iconBackground: EXERCISE_BACKGROUNDS[index % EXERCISE_BACKGROUNDS.length],
                subtitle: item.prescription_note || t('training.sets_count', { count: item.sets?.length || 1 }),
            });
        });
        if (workout.cooldown) {
            rows.push({
                key: 'preview-cooldown',
                name: `${t('training.rest')} · ${workout.cooldown.exercise?.name || workout.cooldown.instruction || ''}`,
                icon: 'weather-night',
                iconColor: colors.teal,
                iconBackground: colors.tealLight,
                subtitle: `${workout.cooldown.duration_minutes || 0} min`,
            });
        }
        return rows;
    }, [previewDay, t, translateActivitySlug]);

    // ------------------------------------------------------------
    // Terminer toute la seance en un clic (uniquement avant le
    // premier exercice logue, pour ne jamais dupliquer la seance)
    // ------------------------------------------------------------
    const completeAll = async () => {
        if (!user?.userId || sessionId || !mainItems.length || isCompletingAll) return;
        setIsCompletingAll(true);
        try {
            const updatedLog = await apiRequest(`/workouts/sessions/${user.userId}`, {
                method: 'POST',
                body: JSON.stringify({
                    duration_minutes: recommendation?.planned_duration_minutes || undefined,
                    exercises: mainItems
                        .filter((item) => item.exercise?.slug)
                        .map((item) => ({
                            exercise_slug: item.exercise.slug,
                            sets: buildSetsPayload(item),
                        })),
                }),
            });
            setSessionId(updatedLog.id);
            setDoneSlugs(new Set(updatedLog.exercises.map((e) => e.exercise_slug)));
        } catch (error) {
            Alert.alert(t('navigation.training'), error.message);
        } finally {
            setIsCompletingAll(false);
        }
    };

    return (
        <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.content}
            refreshControl={
                <RefreshControl
                    refreshing={isRefreshing}
                    onRefresh={refreshPage}
                    tintColor={colors.primary}
                />
            }
        >

            {/* HEADER */}

            <View style={styles.header}>

                <View>
                    <Text style={styles.title}>
                        {t('navigation.training')}
                    </Text>

                    <Text style={styles.date}>
                        {isToday
                            ? (fullyDone
                                ? t('training.session_completed_today')
                                : recommendation
                                    ? t('training.minutes_recommended', { count: recommendation.planned_duration_minutes || 0 })
                                    : t('training.loading_session'))
                            : previewDay
                                ? (previewDay.day_type === 'rest'
                                    ? t('training.rest_day')
                                    : t('training.minutes_planned', { count: previewDay.workout?.planned_duration_minutes || 0 }))
                                : t('training.loading_program')}
                    </Text>
                </View>

                <TouchableOpacity
                    style={[styles.addButton, Boolean(sessionId) && styles.addButtonDisabled]}
                    onPress={completeAll}
                    disabled={isCompletingAll || !recommendation || Boolean(sessionId) || !isToday}
                    activeOpacity={0.7}
                >
                    <Ionicons
                        name={!isToday ? 'calendar-outline' : fullyDone ? 'checkmark' : isCompletingAll ? 'hourglass-outline' : 'checkmark-done'}
                        size={26}
                        color={!isToday ? colors.secondaryText : fullyDone ? colors.primary : Boolean(sessionId) ? colors.secondaryText : colors.text}
                    />
                </TouchableOpacity>

            </View>

            {/* DAYS */}

            <View style={styles.days}>

                {weekDates.map((date, index) => (
                    <DayBox
                        key={index}
                        day={t(`days.${WEEKDAY_KEYS[date.getDay()]}`)}
                        number={String(date.getDate())}
                        active={activeDay === index}
                        onPress={() => setActiveDay(index)}
                    />
                ))}

            </View>

            {/* WORKOUT SUMMARY */}

            {isToday ? (
            <View style={styles.summary}>

                <View style={styles.summaryHeader}>

                    <View>
                        <Text style={styles.summaryTitle}>
                            {workoutTitle}
                        </Text>

                        <Text style={styles.summarySubtitle}>
                            {t('training.exercises_done', {
                                done: doneCount,
                                total: mainItems.length,
                            })}
                        </Text>
                    </View>

                    <View style={styles.summaryIcon}>
                        <MaterialCommunityIcons
                            name="dumbbell"
                            size={26}
                            color={colors.primary}
                        />
                    </View>

                </View>

                <View style={styles.progressBackground}>
                    <View
                        style={[
                            styles.progress,
                            { width: `${progressPercent}%` },
                        ]}
                    />
                </View>

                <Text style={styles.progressLabel}>
                    {t('training.percent_completed', {
                        percent: progressPercent,
                    })}
                </Text>

            </View>
            ) : (
            <View style={styles.summary}>

                <View style={styles.summaryHeader}>

                    <View>
                        <Text style={styles.summaryTitle}>
                            {previewDay
                                ? (previewDay.day_type === 'rest' ? t('training.rest') : (previewTrainingType || t('training.session_label')))
                                : '—'}
                        </Text>

                        <Text style={styles.summarySubtitle}>
                            {previewDay?.day_type === 'training'
                                ? t('training.rpe_kcal', {
                                    rpe: previewDay.workout?.target_rpe ?? '—',
                                    kcal: Math.round(previewDay.workout?.estimated_calories_kcal || 0),
                                })
                                : t('training.active_recovery_label')}
                        </Text>
                    </View>

                    <View style={styles.summaryIcon}>
                        <MaterialCommunityIcons
                            name={previewDay?.day_type === 'rest' ? 'weather-night' : 'dumbbell'}
                            size={26}
                            color={colors.primary}
                        />
                    </View>

                </View>

            </View>
            )}

            {/* STATS */}

            {isToday && (
            <View style={styles.statsRow}>

                <MacroCard
                    icon="fire"
                    title={t('nutrition.calories')}
                    current={String(sessionCaloriesBurned)}
                    target={String(sessionCalorieTarget)}
                    progress={calorieCardProgress}
                    unit="kcal"
                    color={colors.orange}
                    background={colors.orangeLight}
                    subtitle={t('training.calories_to_burn', { value: caloriesToBurn })}
                />

                <MacroCard
                    icon="clock-outline"
                    title={t('training.duration')}
                    current={String(fullyDone ? (recommendation?.planned_duration_minutes || 0) : 0)}
                    target={String(recommendation?.planned_duration_minutes || 0)}
                    progress={progressPercent}
                    unit="min"
                    color={colors.teal}
                    background={colors.tealLight}
                />

                <MacroCard
                    icon="chart-line"
                    title={t('training.streak')}
                    current={recovery ? String(Math.round(recovery.score || 0)) : '—'}
                    target="100"
                    progress={recovery ? Math.round(recovery.score || 0) : 0}
                    unit="pts"
                    color={colors.primary}
                    background={colors.primaryLight}
                />

            </View>
            )}

            {isToday && (lifestyleToday?.activity?.steps != null || lifestyleSuggestion || recovery?.level) && (
                <View style={styles.lifestyleCard}>
                    <Text style={styles.lifestyleTitle}>{t('training.lifestyle_today')}</Text>
                    {lifestyleToday?.activity?.steps != null && (
                        <Text style={styles.lifestyleText}>
                            {t('training.steps_count', { count: lifestyleToday.activity.steps })}
                            {lifestyleToday.activity.active_minutes != null
                                ? ` · ${t('training.active_minutes_count', { count: lifestyleToday.activity.active_minutes })}`
                                : ''}
                        </Text>
                    )}
                    {recovery?.level && (
                        <Text style={styles.lifestyleText}>
                            {t('training.recovery_prefix', { level: translateRecoveryLevel(recovery.level) })}
                        </Text>
                    )}
                    {lifestyleSuggestion && (
                        <TouchableOpacity
                            style={styles.suggestionButton}
                            onPress={() => startSuggestedActivity(lifestyleSuggestion)}
                            disabled={isLoggingActivity}
                            activeOpacity={0.8}
                        >
                            <Text style={styles.suggestionButtonText}>
                                {isLoggingActivity
                                    ? t('training.saving')
                                    : t('training.suggestion_button', { label: translateActivityLabel(lifestyleSuggestion) })}
                            </Text>
                        </TouchableOpacity>
                    )}
                </View>
            )}

            {/* EXERCISES (echauffement + seance principale, ou apercu
                en lecture seule pour un jour autre qu'aujourd'hui) */}

            <Text style={styles.sectionTitle}>
                {isToday
                    ? t('training.today_exercises')
                    : previewDay?.day_type === 'rest'
                        ? t('training.suggestions_section')
                        : t('training.planned_session_section')}
            </Text>

            {isLoading ? (
                <ActivityIndicator color={colors.primary} size="large" />
            ) : isToday ? (
                displayList.length ? (
                    displayList.map((item) => (
                        <ExerciseSection
                            key={item.key}
                            icon={item.icon}
                            name={item.name}
                            sets={isItemSaving(item) ? t('training.saving') : item.subtitle}
                            done={isItemDone(item)}
                            iconColor={item.iconColor}
                            iconBackground={item.iconBackground}
                            onPress={() => handleItemPress(item)}
                        />
                    ))
                ) : (
                    <Text style={styles.emptyText}>
                        {t('training.no_exercises')}
                    </Text>
                )
            ) : previewItems.length ? (
                previewItems.map((item) => (
                    <ExerciseSection
                        key={item.key}
                        icon={item.icon}
                        name={item.name}
                        sets={item.subtitle}
                        done={false}
                        iconColor={item.iconColor}
                        iconBackground={item.iconBackground}
                        onPress={handlePreviewItemPress}
                    />
                ))
            ) : (
                <Text style={styles.emptyText}>
                    {t('training.no_activities')}
                </Text>
            )}

            {/* REPOS (retour au calme, module Sport partie 4) --
                uniquement pour aujourd'hui : deja inclus dans previewItems
                pour les autres jours */}

            {isToday && cooldownItem && (
                <>
                    <Text style={styles.sectionTitle}>
                        {t('training.rest')}
                    </Text>
                    <ExerciseSection
                        icon="weather-night"
                        name={cooldownItem.exercise?.name || cooldownItem.instruction || t('training.rest')}
                        sets={isItemSaving(cooldownItem) ? t('training.saving') : `${cooldownItem.duration_minutes || 0} min`}
                        done={isItemDone(cooldownItem)}
                        iconColor={colors.teal}
                        iconBackground={colors.tealLight}
                        onPress={() => handleItemPress(cooldownItem)}
                    />
                </>
            )}

        </ScrollView>
    );
}

const styles = StyleSheet.create({
    content: {
        padding: 20,

        paddingBottom: 35,
    },

    header: {
        flexDirection: 'row',

        justifyContent: 'space-between',

        alignItems: 'center',

        marginBottom: 20,
    },

    title: {
        fontSize: 29,

        fontWeight: '800',

        color: colors.text,
    },

    date: {
        fontSize: 17,

        color: colors.secondaryText,

        marginTop: 3,
    },

    addButton: {
        width: 55,
        height: 55,

        borderRadius: 28,

        backgroundColor: colors.white,

        alignItems: 'center',
        justifyContent: 'center',
    },

    addButtonDisabled: {
        opacity: 0.5,
    },

    days: {
        flexDirection: 'row',

        gap: 8,

        marginBottom: 20,
    },

    summary: {
        backgroundColor: colors.white,

        borderRadius: 26,

        padding: 22,

        marginBottom: 20,
    },

    summaryHeader: {
        flexDirection: 'row',

        alignItems: 'center',

        justifyContent: 'space-between',

        marginBottom: 18,
    },

    summaryTitle: {
        fontSize: 21,

        fontWeight: '800',

        color: colors.text,
    },

    summarySubtitle: {
        color: colors.secondaryText,

        fontSize: 14,

        marginTop: 3,
    },

    summaryIcon: {
        width: 52,
        height: 52,

        borderRadius: 26,

        backgroundColor: colors.primaryLight,

        alignItems: 'center',
        justifyContent: 'center',
    },

    progressBackground: {
        height: 10,

        borderRadius: 10,

        backgroundColor: '#E9EBF0',

        overflow: 'hidden',
    },

    progress: {
        height: '100%',

        borderRadius: 10,

        backgroundColor: colors.primary,
    },

    progressLabel: {
        marginTop: 10,

        color: colors.secondaryText,

        fontSize: 14,

        fontWeight: '600',
    },

    statsRow: {
        flexDirection: 'row',

        marginHorizontal: -4,

        marginBottom: 26,
    },

    lifestyleCard: {
        backgroundColor: colors.white,
        borderRadius: 22,
        padding: 18,
        marginBottom: 26,
    },

    lifestyleTitle: {
        color: colors.text,
        fontSize: 17,
        fontWeight: '800',
        marginBottom: 6,
    },

    lifestyleText: {
        color: colors.secondaryText,
        fontSize: 14,
    },

    suggestionButton: {
        backgroundColor: colors.primaryLight,
        borderRadius: 14,
        paddingVertical: 10,
        paddingHorizontal: 12,
        marginTop: 10,
    },

    suggestionButtonText: {
        color: colors.primary,
        fontSize: 14,
        fontWeight: '800',
    },

    sectionTitle: {
        fontSize: 23,

        fontWeight: '800',

        color: colors.text,

        marginBottom: 16,
    },

    emptyText: {
        color: colors.secondaryText,
        fontSize: 14,
        marginBottom: 16,
    },
});
