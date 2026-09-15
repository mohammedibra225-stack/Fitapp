import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    Dimensions,
    ActivityIndicator,
    RefreshControl,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 72;

const DAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

// Filtres de periode : pilotent TOUTES les requetes de la page
// (sport + nutrition + lifestyle), pas seulement les graphiques.
const PERIODS = [
    { key: 'week', days: 7, labelKey: 'week', rangeKey: 'range_week' },
    { key: 'days30', days: 30, labelKey: 'days30', rangeKey: 'range_days30' },
    { key: 'year', days: 365, labelKey: 'year', rangeKey: 'range_year' },
];

// Libelles courts pour les records personnels (module Sport, partie 6).
const RECORD_TYPE_KEYS = {
    max_weight: 'record_max_weight',
    max_reps: 'record_max_reps',
    one_rep_max: 'record_one_rep_max',
    best_time: 'record_best_time',
    best_distance: 'record_best_distance',
    max_duration: 'record_max_duration',
};

const MEAL_TYPE_KEYS = {
    breakfast: 'nutrition.breakfast',
    lunch: 'nutrition.lunch',
    dinner: 'nutrition.dinner',
    snack: 'nutrition.snacks',
    snacks: 'nutrition.snacks',
};

// Objectif de pas par defaut (recommandation OMS) : sert de reference
// tant que l'utilisateur n'a pas d'objectif de pas personnalise.
const DEFAULT_STEPS_GOAL = 8000;
const DEFAULT_SESSIONS_PER_WEEK = 3;

const toISODate = (d) => {
    const copy = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return copy.toISOString().slice(0, 10);
};

function pickNumber(source, keys) {
    if (!source) return null;
    for (const key of keys) {
        const value = source[key];
        if (typeof value === 'number' && Number.isFinite(value)) return value;
    }
    return null;
}

function safeRatio(current, target) {
    if (!target || target <= 0) return 0;
    return Math.max(0, Math.min(1, current / target));
}

export default function ProgressScreen() {
    const [selectedPeriod, setSelectedPeriod] = useState('week');
    const [sportProgress, setSportProgress] = useState(null);
    const [lifestyleScore, setLifestyleScore] = useState(null);
    const [activityLogs, setActivityLogs] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [meals, setMeals] = useState([]);
    const [nutritionTargets, setNutritionTargets] = useState(null);
    const [sessionsPerWeekGoal, setSessionsPerWeekGoal] = useState(DEFAULT_SESSIONS_PER_WEEK);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const { t } = useI18n();
    const { user } = useUser();

    const period = PERIODS.find((p) => p.key === selectedPeriod) || PERIODS[0];
    const periodDays = period.days;

    const loadData = useCallback(async () => {
        if (!user?.userId) {
            setIsLoading(false);
            return;
        }

        const today = new Date();
        const start = new Date(today);
        start.setDate(start.getDate() - (periodDays - 1));
        const startISO = toISODate(start);
        const endISO = toISODate(today);
        const userId = user.userId;

        try {
            const [
                progressResult,
                scoreResult,
                activityResult,
                sessionsResult,
                mealsResult,
                dailyResult,
                sportProfileResult,
            ] = await Promise.allSettled([
                apiRequest(`/progress/${userId}`),
                apiRequest(`/lifestyle/score/${userId}`),
                apiRequest(
                    `/lifestyle/activity/${userId}?start_date=${startISO}&end_date=${endISO}`
                ),
                apiRequest(`/workouts/sessions/${userId}?days=${periodDays}`),
                apiRequest(
                    `/nutrition-tracking/meals/${userId}?start_date=${startISO}&end_date=${endISO}`
                ),
                apiRequest(`/nutrition-tracking/daily/${userId}`),
                apiRequest(`/sports/profile/${userId}`),
            ]);

            if (progressResult.status === 'fulfilled') setSportProgress(progressResult.value);
            if (scoreResult.status === 'fulfilled') setLifestyleScore(scoreResult.value);
            setActivityLogs(
                activityResult.status === 'fulfilled' && Array.isArray(activityResult.value)
                    ? activityResult.value
                    : []
            );
            setSessions(
                sessionsResult.status === 'fulfilled' && Array.isArray(sessionsResult.value)
                    ? sessionsResult.value
                    : []
            );
            setMeals(
                mealsResult.status === 'fulfilled' && Array.isArray(mealsResult.value)
                    ? mealsResult.value
                    : []
            );
            if (dailyResult.status === 'fulfilled') {
                setNutritionTargets(dailyResult.value?.targets ?? null);
            }

            // Objectif de seances = frequence declaree dans le profil sportif.
            if (sportProfileResult.status === 'fulfilled') {
                const payload = sportProfileResult.value;
                const list = Array.isArray(payload)
                    ? payload
                    : payload?.sports || payload?.user_sports || [];
                const primary = list.find((s) => s?.is_primary) || list[0];
                const frequency = primary?.frequency_per_week;
                if (typeof frequency === 'number' && frequency > 0) {
                    setSessionsPerWeekGoal(frequency);
                }
            }
        } finally {
            setIsLoading(false);
        }
    }, [user?.userId, periodDays]);

    useEffect(() => {
        setIsLoading(true);
        loadData();
    }, [loadData]);

    const refreshPage = async () => {
        setIsRefreshing(true);
        await loadData();
        setIsRefreshing(false);
    };

    // ------------------------------------------------------------
    // AGREGATION : une seule timeline jour par jour, alimentee par le
    // sport (WorkoutLog), le lifestyle (DailyActivityLog) et la
    // nutrition (Meal). Toutes les stats de la page en decoulent.
    // ------------------------------------------------------------
    const timeline = useMemo(() => {
        const today = new Date();
        const days = [];
        const byDate = new Map();

        for (let i = periodDays - 1; i >= 0; i -= 1) {
            const d = new Date(today);
            d.setDate(d.getDate() - i);
            const iso = toISODate(d);
            const entry = {
                date: iso,
                dayKey: DAY_KEYS[d.getDay()],
                label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
                monthLabel: String(d.getMonth() + 1).padStart(2, '0'),
                sessions: 0,
                minutes: 0,
                volume: 0,
                rpeValues: [],
                steps: 0,
                activeMinutes: 0,
                meals: 0,
                calories: 0,
                protein: 0,
                carbs: 0,
                fat: 0,
            };
            days.push(entry);
            byDate.set(iso, entry);
        }

        activityLogs.forEach((log) => {
            const entry = byDate.get(String(log?.log_date || '').slice(0, 10));
            if (!entry) return;
            entry.steps += log?.steps ?? 0;
            entry.activeMinutes += log?.active_minutes ?? 0;
        });

        sessions.forEach((session) => {
            const entry = byDate.get(String(session?.performed_at || '').slice(0, 10));
            if (!entry) return;
            entry.sessions += 1;
            entry.minutes += session?.duration_minutes ?? 0;
            (session?.exercises || []).forEach((exercise) => {
                (exercise?.sets || []).forEach((set) => {
                    if (set?.reps != null && set?.weight_kg != null) {
                        entry.volume += set.reps * set.weight_kg;
                    }
                    if (set?.rpe != null) entry.rpeValues.push(set.rpe);
                });
            });
        });

        meals.forEach((meal) => {
            const entry = byDate.get(String(meal?.consumed_on || '').slice(0, 10));
            if (!entry) return;
            entry.meals += 1;
            entry.calories += meal?.total_calories_kcal ?? 0;
            entry.protein += meal?.total_protein_g ?? 0;
            entry.carbs += meal?.total_carbs_g ?? 0;
            entry.fat += meal?.total_fat_g ?? 0;
        });

        return days;
    }, [activityLogs, sessions, meals, periodDays]);

    const stats = useMemo(() => {
        const totalSessions = timeline.reduce((sum, d) => sum + d.sessions, 0);
        const totalMinutes = timeline.reduce((sum, d) => sum + d.minutes, 0);
        const totalVolume = timeline.reduce((sum, d) => sum + d.volume, 0);
        const rpeValues = timeline.flatMap((d) => d.rpeValues);
        const avgRpe = rpeValues.length
            ? Math.round((rpeValues.reduce((a, b) => a + b, 0) / rpeValues.length) * 10) / 10
            : null;

        const stepDays = timeline.filter((d) => d.steps > 0);
        const avgSteps = stepDays.length
            ? Math.round(stepDays.reduce((sum, d) => sum + d.steps, 0) / stepDays.length)
            : 0;

        const nutritionDays = timeline.filter((d) => d.meals > 0);
        const avg = (selector) =>
            nutritionDays.length
                ? Math.round(nutritionDays.reduce((sum, d) => sum + selector(d), 0) / nutritionDays.length)
                : 0;

        // Streak : jours consecutifs (en partant du plus recent) avec au
        // moins une seance OU un repas enregistre.
        let streak = 0;
        for (let i = timeline.length - 1; i >= 0; i -= 1) {
            const day = timeline[i];
            const active = day.sessions > 0 || day.meals > 0;
            if (active) {
                streak += 1;
            } else if (i === timeline.length - 1) {
                continue; // la journee en cours n'est pas encore finie
            } else {
                break;
            }
        }

        return {
            totalSessions,
            totalMinutes,
            totalVolume,
            avgRpe,
            avgSteps,
            trackedDays: nutritionDays.length,
            totalMeals: timeline.reduce((sum, d) => sum + d.meals, 0),
            avgCalories: avg((d) => d.calories),
            avgProtein: avg((d) => d.protein),
            avgCarbs: avg((d) => d.carbs),
            avgFat: avg((d) => d.fat),
            streak,
        };
    }, [timeline]);

    // Regroupement des jours en points de graphique lisibles :
    // 7 jours -> 1 point/jour, 30 jours -> 6 points de 5 jours,
    // 1 an -> 12 points mensuels.
    const buckets = useMemo(() => {
        const makeBucket = (label) => ({
            label,
            days: 0,
            sessions: 0,
            calories: 0,
            steps: 0,
            nutritionDays: 0,
        });

        const push = (bucket, day) => {
            bucket.days += 1;
            bucket.sessions += day.sessions;
            bucket.steps += day.steps;
            if (day.meals > 0) {
                bucket.calories += day.calories;
                bucket.nutritionDays += 1;
            }
        };

        if (periodDays <= 7) {
            return timeline.map((day) => {
                const bucket = makeBucket(t(`days.${day.dayKey}`).slice(0, 3));
                push(bucket, day);
                return bucket;
            });
        }

        if (periodDays <= 30) {
            const size = Math.ceil(timeline.length / 6);
            const result = [];
            for (let i = 0; i < timeline.length; i += size) {
                const slice = timeline.slice(i, i + size);
                const bucket = makeBucket(slice[slice.length - 1].label);
                slice.forEach((day) => push(bucket, day));
                result.push(bucket);
            }
            return result;
        }

        const byMonth = new Map();
        timeline.forEach((day) => {
            const key = day.date.slice(0, 7);
            if (!byMonth.has(key)) byMonth.set(key, makeBucket(day.monthLabel));
            push(byMonth.get(key), day);
        });
        return Array.from(byMonth.values());
    }, [timeline, periodDays, t]);

    const sessionsChartData = useMemo(
        () => ({
            labels: buckets.map((b) => b.label),
            datasets: [{ data: buckets.length ? buckets.map((b) => b.sessions) : [0] }],
        }),
        [buckets]
    );

    const stepsChartData = useMemo(
        () => ({
            labels: buckets.map((b) => b.label),
            datasets: [
                {
                    data: buckets.length
                        ? buckets.map((b) => (b.days ? Math.round(b.steps / b.days) : 0))
                        : [0],
                },
            ],
        }),
        [buckets]
    );

    const caloriesChartData = useMemo(
        () => ({
            labels: buckets.map((b) => b.label),
            datasets: [
                {
                    data: buckets.length
                        ? buckets.map((b) =>
                            b.nutritionDays ? Math.round(b.calories / b.nutritionDays) : 0
                        )
                        : [0],
                    color: () => colors.orange,
                    strokeWidth: 3,
                },
            ],
        }),
        [buckets]
    );

    const targets = useMemo(() => {
        const source = nutritionTargets || {};
        return {
            calories: pickNumber(source, ['calories_kcal', 'calories', 'target_calories_kcal']),
            protein: pickNumber(source, ['protein_g', 'protein', 'target_protein_g']),
            carbs: pickNumber(source, ['carbs_g', 'carbohydrates_g', 'carbs']),
            fat: pickNumber(source, ['fat_g', 'fat', 'lipids_g']),
        };
    }, [nutritionTargets]);

    // Objectifs unifies sport + nutrition : c'est ce qui alimente le
    // resume global (progression, objectifs atteints).
    const goals = useMemo(() => {
        const weeks = Math.max(1, periodDays / 7);
        const sessionsTarget = Math.round(sessionsPerWeekGoal * weeks);
        const list = [
            {
                key: 'sessions',
                icon: 'dumbbell',
                color: colors.primary,
                label: t('progress.goal_sessions'),
                current: stats.totalSessions,
                target: sessionsTarget,
                unit: '',
            },
            {
                key: 'steps',
                icon: 'walk',
                color: colors.blue,
                label: t('progress.goal_steps'),
                current: stats.avgSteps,
                target: DEFAULT_STEPS_GOAL,
                unit: '',
            },
        ];

        if (targets.calories) {
            list.push({
                key: 'calories',
                icon: 'fire',
                color: colors.orange,
                label: t('progress.goal_calories'),
                current: stats.avgCalories,
                target: Math.round(targets.calories),
                unit: 'kcal',
            });
        }
        if (targets.protein) {
            list.push({
                key: 'protein',
                icon: 'food-drumstick',
                color: colors.teal,
                label: t('progress.goal_protein'),
                current: stats.avgProtein,
                target: Math.round(targets.protein),
                unit: 'g',
            });
        }

        return list.map((goal) => ({ ...goal, ratio: safeRatio(goal.current, goal.target) }));
    }, [stats, targets, sessionsPerWeekGoal, periodDays, t]);

    const globalProgress = goals.length
        ? Math.round((goals.reduce((sum, g) => sum + g.ratio, 0) / goals.length) * 100)
        : 0;
    const goalsReached = goals.filter((g) => g.ratio >= 1).length;

    const records = sportProgress?.personal_records || [];
    const suggestions = (sportProgress?.progression_suggestions || []).filter(
        (s) => s.status === 'ok' && s.action !== 'maintain'
    );
    const scoreValue = lifestyleScore?.score != null ? Math.round(lifestyleScore.score) : null;

    const sessionHistory = useMemo(
        () =>
            [...sessions]
                .sort((a, b) => String(b.performed_at).localeCompare(String(a.performed_at)))
                .slice(0, 8),
        [sessions]
    );

    const mealHistory = useMemo(
        () =>
            [...meals]
                .sort((a, b) => String(b.consumed_on).localeCompare(String(a.consumed_on)))
                .slice(0, 8),
        [meals]
    );

    const achievements = [
        { icon: 'medal', labelKey: 'month1', unlocked: stats.totalSessions >= 1 },
        { icon: 'fire', labelKey: 'full_week', unlocked: stats.streak >= 7 },
        { icon: 'target', labelKey: 'goal_reached', unlocked: goalsReached >= goals.length && goals.length > 0 },
        { icon: 'star', labelKey: 'sessions20', unlocked: stats.totalSessions >= 20 },
    ];

    const chartConfig = {
        backgroundColor: colors.white,
        backgroundGradientFrom: colors.white,
        backgroundGradientTo: colors.white,
        decimalPlaces: 0,
        color: () => colors.primary,
        labelColor: () => colors.secondaryText,
        barPercentage: 0.6,
        style: { borderRadius: 12 },
    };

    return (
        <ScrollView
            style={styles.container}
            showsVerticalScrollIndicator={false}
            refreshControl={
                <RefreshControl refreshing={isRefreshing} onRefresh={refreshPage} tintColor={colors.primary} />
            }
        >
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>{t('progress.title')}</Text>
                <Text style={styles.headerDate}>{t(`progress.${period.rangeKey}`)}</Text>
            </View>

            {/* Filtres de periode : pilotent sport ET nutrition */}
            <View style={styles.periodContainer}>
                {PERIODS.map((p) => (
                    <TouchableOpacity
                        key={p.key}
                        style={[styles.periodButton, selectedPeriod === p.key && styles.periodButtonActive]}
                        onPress={() => setSelectedPeriod(p.key)}
                    >
                        <Text
                            style={[styles.periodText, selectedPeriod === p.key && styles.periodTextActive]}
                        >
                            {t(`progress.${p.labelKey}`)}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {isLoading ? (
                <ActivityIndicator color={colors.primary} size="large" style={{ marginTop: 40 }} />
            ) : (
                <>
                    {/* ============ RESUME GLOBAL (sport + nutrition) ============ */}
                    <View style={styles.summaryCard}>
                        <View style={styles.cardHeader}>
                            <Text style={styles.cardTitle}>{t('progress.overview')}</Text>
                            <Text style={styles.badge}>
                                {t('progress.goals_reached_count', { done: goalsReached, total: goals.length })}
                            </Text>
                        </View>

                        <View style={styles.summaryRow}>
                            <View style={styles.summaryRing}>
                                <Text style={styles.summaryRingValue}>{globalProgress}%</Text>
                                <Text style={styles.summaryRingLabel}>{t('progress.global_progress')}</Text>
                            </View>

                            <View style={styles.summarySide}>
                                <SummaryLine
                                    icon="fire"
                                    color={colors.orange}
                                    label={t('progress.streak_label')}
                                    value={t('progress.streak_days', { count: stats.streak })}
                                />
                                <SummaryLine
                                    icon="dumbbell"
                                    color={colors.primary}
                                    label={t('progress.sessions_total')}
                                    value={String(stats.totalSessions)}
                                />
                                <SummaryLine
                                    icon="silverware-fork-knife"
                                    color={colors.teal}
                                    label={t('progress.days_tracked')}
                                    value={String(stats.trackedDays)}
                                />
                                <SummaryLine
                                    icon="heart-pulse"
                                    color={colors.blue}
                                    label={t('progress.lifestyle_score')}
                                    value={scoreValue != null ? String(scoreValue) : '—'}
                                />
                            </View>
                        </View>

                        <View style={styles.goalsBlock}>
                            <Text style={styles.blockTitle}>{t('progress.goals_section')}</Text>
                            {goals.map((goal) => (
                                <GoalBar key={goal.key} goal={goal} />
                            ))}
                            {!targets.calories && (
                                <Text style={styles.emptyText}>{t('progress.targets_unavailable')}</Text>
                            )}
                        </View>
                    </View>

                    {/* ======================= SPORT ======================= */}
                    <SectionHeader icon="dumbbell" title={t('progress.sport_section')} color={colors.primary} />

                    <View style={styles.statsContainer}>
                        <StatCard
                            icon="dumbbell"
                            label={t('progress.sessions_total')}
                            value={String(stats.totalSessions)}
                            color={colors.primary}
                        />
                        <StatCard
                            icon="timer-outline"
                            label={t('progress.total_duration')}
                            value={t('progress.minutes_short', { count: stats.totalMinutes })}
                            color={colors.blue}
                        />
                        <StatCard
                            icon="lightning-bolt"
                            label={t('progress.total_intensity')}
                            value={stats.avgRpe != null ? String(stats.avgRpe) : '—'}
                            color="#FF6B4A"
                        />
                    </View>

                    <View style={styles.card}>
                        <View style={styles.cardHeader}>
                            <Text style={styles.cardTitle}>{t('progress.sessions_chart')}</Text>
                            <Text style={styles.badge}>
                                {t('progress.volume_total', { value: Math.round(stats.totalVolume) })}
                            </Text>
                        </View>
                        <BarChart
                            data={sessionsChartData}
                            width={CHART_WIDTH}
                            height={190}
                            fromZero
                            chartConfig={chartConfig}
                            style={styles.chart}
                        />
                    </View>

                    <View style={styles.card}>
                        <View style={styles.cardHeader}>
                            <Text style={styles.cardTitle}>{t('progress.activity_section')}</Text>
                            <Text style={styles.badge}>
                                {t('progress.avg_steps_day')} : {stats.avgSteps}
                            </Text>
                        </View>
                        {stats.avgSteps === 0 ? (
                            <Text style={styles.emptyText}>{t('progress.no_activity_data')}</Text>
                        ) : (
                            <BarChart
                                data={stepsChartData}
                                width={CHART_WIDTH}
                                height={190}
                                fromZero
                                chartConfig={{ ...chartConfig, color: () => colors.blue }}
                                style={styles.chart}
                            />
                        )}
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{t('progress.history_sport')}</Text>
                        {sessionHistory.length === 0 ? (
                            <Text style={styles.emptyText}>{t('progress.no_sessions')}</Text>
                        ) : (
                            sessionHistory.map((session) => {
                                const exercises = session?.exercises || [];
                                const sets = exercises.reduce(
                                    (sum, exercise) => sum + (exercise?.sets?.length || 0),
                                    0
                                );
                                return (
                                    <View key={session.id} style={styles.historyRow}>
                                        <View style={styles.historyLeft}>
                                            <Text style={styles.historyTitle}>
                                                {String(session.performed_at).slice(0, 10)}
                                            </Text>
                                            <Text style={styles.historySubtitle}>
                                                {t('progress.session_summary', {
                                                    exercises: exercises.length,
                                                    sets,
                                                })}
                                            </Text>
                                        </View>
                                        <Text style={styles.historyValue}>
                                            {t('progress.minutes_short', {
                                                count: session.duration_minutes ?? 0,
                                            })}
                                        </Text>
                                    </View>
                                );
                            })
                        )}
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{t('progress.personal_records')}</Text>
                        {records.length === 0 ? (
                            <Text style={styles.emptyText}>{t('progress.no_records')}</Text>
                        ) : (
                            records.slice(0, 5).map((record) => (
                                <View key={record.id} style={styles.recordRow}>
                                    <Text style={styles.recordLabel}>
                                        {t(`progress.${RECORD_TYPE_KEYS[record.record_type] || 'record_max_weight'}`)}
                                    </Text>
                                    <Text style={styles.recordValue}>
                                        {record.value} {record.unit}
                                    </Text>
                                </View>
                            ))
                        )}
                    </View>

                    {suggestions.length > 0 && (
                        <View style={styles.card}>
                            <Text style={styles.cardTitle}>{t('progress.suggestions')}</Text>
                            {suggestions.slice(0, 3).map((s) => (
                                <View key={s.exercise_id} style={styles.suggestionRow}>
                                    <MaterialCommunityIcons
                                        name={s.action === 'increase' ? 'trending-up' : 'trending-down'}
                                        size={18}
                                        color={s.action === 'increase' ? colors.primary : colors.orange}
                                    />
                                    <Text style={styles.suggestionText}>{s.reason}</Text>
                                </View>
                            ))}
                        </View>
                    )}

                    {/* ===================== NUTRITION ===================== */}
                    <SectionHeader
                        icon="silverware-fork-knife"
                        title={t('progress.nutrition_section')}
                        color={colors.orange}
                    />

                    <View style={styles.statsContainer}>
                        <StatCard
                            icon="fire"
                            label={t('progress.avg_calories_day')}
                            value={String(stats.avgCalories)}
                            color={colors.orange}
                        />
                        <StatCard
                            icon="food-drumstick"
                            label={t('progress.avg_protein_day')}
                            value={`${stats.avgProtein} g`}
                            color={colors.teal}
                        />
                        <StatCard
                            icon="calendar-check"
                            label={t('progress.days_tracked')}
                            value={String(stats.trackedDays)}
                            color={colors.primary}
                        />
                    </View>

                    <View style={styles.card}>
                        <View style={styles.cardHeader}>
                            <Text style={styles.cardTitle}>{t('progress.calories_trend')}</Text>
                            <Text style={styles.badge}>
                                {targets.calories
                                    ? t('progress.calories_vs_target', {
                                        avg: stats.avgCalories,
                                        target: Math.round(targets.calories),
                                    })
                                    : t('progress.calories_avg_only', { avg: stats.avgCalories })}
                            </Text>
                        </View>
                        {stats.trackedDays === 0 ? (
                            <Text style={styles.emptyText}>{t('progress.no_meals')}</Text>
                        ) : (
                            <LineChart
                                data={caloriesChartData}
                                width={CHART_WIDTH}
                                height={190}
                                fromZero
                                chartConfig={{ ...chartConfig, color: () => colors.orange }}
                                style={styles.chart}
                            />
                        )}
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{t('progress.macros_average')}</Text>
                        <MacroBar
                            label={t('progress.avg_protein_day')}
                            current={stats.avgProtein}
                            target={targets.protein}
                            color={colors.teal}
                            unit="g"
                        />
                        <MacroBar
                            label={t('progress.avg_carbs_day')}
                            current={stats.avgCarbs}
                            target={targets.carbs}
                            color={colors.blue}
                            unit="g"
                        />
                        <MacroBar
                            label={t('progress.avg_fat_day')}
                            current={stats.avgFat}
                            target={targets.fat}
                            color={colors.orange}
                            unit="g"
                        />
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{t('progress.history_nutrition')}</Text>
                        {mealHistory.length === 0 ? (
                            <Text style={styles.emptyText}>{t('progress.no_meals')}</Text>
                        ) : (
                            mealHistory.map((meal) => (
                                <View key={meal.id} style={styles.historyRow}>
                                    <View style={styles.historyLeft}>
                                        <Text style={styles.historyTitle}>
                                            {meal.name ||
                                                t(MEAL_TYPE_KEYS[meal.meal_type] || 'nutrition.daily_summary')}
                                        </Text>
                                        <Text style={styles.historySubtitle}>
                                            {String(meal.consumed_on).slice(0, 10)} ·{' '}
                                            {Math.round(meal.total_protein_g ?? 0)} g{' '}
                                            {t('nutrition.protein').toLowerCase()}
                                        </Text>
                                    </View>
                                    <Text style={styles.historyValue}>
                                        {Math.round(meal.total_calories_kcal ?? 0)} kcal
                                    </Text>
                                </View>
                            ))
                        )}
                    </View>

                    {/* Achievements (bases sur les donnees reelles agregees) */}
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{t('progress.achievements')}</Text>
                        <View style={styles.achievementsGrid}>
                            {achievements.map((a) => (
                                <Achievement
                                    key={a.labelKey}
                                    icon={a.icon}
                                    label={t(`progress.${a.labelKey}`)}
                                    unlocked={a.unlocked}
                                />
                            ))}
                        </View>
                    </View>

                    <View style={styles.spacer} />
                </>
            )}
        </ScrollView>
    );
}

function SectionHeader({ icon, title, color }) {
    return (
        <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, { backgroundColor: color + '20' }]}>
                <MaterialCommunityIcons name={icon} size={18} color={color} />
            </View>
            <Text style={styles.sectionTitle}>{title}</Text>
        </View>
    );
}

function SummaryLine({ icon, color, label, value }) {
    return (
        <View style={styles.summaryLine}>
            <MaterialCommunityIcons name={icon} size={16} color={color} />
            <Text style={styles.summaryLineLabel}>{label}</Text>
            <Text style={styles.summaryLineValue}>{value}</Text>
        </View>
    );
}

function GoalBar({ goal }) {
    return (
        <View style={styles.goalRow}>
            <View style={styles.goalHeader}>
                <MaterialCommunityIcons name={goal.icon} size={16} color={goal.color} />
                <Text style={styles.goalLabel}>{goal.label}</Text>
                <Text style={[styles.goalValue, { color: goal.color }]}>
                    {goal.current} / {goal.target} {goal.unit}
                </Text>
            </View>
            <View style={styles.progressTrack}>
                <View
                    style={[
                        styles.progressFill,
                        { width: `${Math.round(goal.ratio * 100)}%`, backgroundColor: goal.color },
                    ]}
                />
            </View>
        </View>
    );
}

function MacroBar({ label, current, target, color, unit }) {
    const ratio = target ? safeRatio(current, target) : 0;
    return (
        <View style={styles.goalRow}>
            <View style={styles.goalHeader}>
                <Text style={styles.goalLabel}>{label}</Text>
                <Text style={[styles.goalValue, { color }]}>
                    {current}
                    {target ? ` / ${Math.round(target)}` : ''} {unit}
                </Text>
            </View>
            <View style={styles.progressTrack}>
                <View
                    style={[styles.progressFill, { width: `${Math.round(ratio * 100)}%`, backgroundColor: color }]}
                />
            </View>
        </View>
    );
}

function StatCard({ icon, label, value, color }) {
    return (
        <View style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: color + '20' }]}>
                <MaterialCommunityIcons name={icon} size={20} color={color} />
            </View>
            <Text style={styles.statLabel}>{label}</Text>
            <Text style={styles.statValue}>{value}</Text>
        </View>
    );
}

function Achievement({ icon, label, unlocked }) {
    return (
        <View style={[styles.achievement, !unlocked && styles.achievementLocked]}>
            <View
                style={[
                    styles.achievementIcon,
                    unlocked ? { backgroundColor: '#FFD93D' } : { backgroundColor: colors.border },
                ]}
            >
                <MaterialCommunityIcons name={icon} size={24} color={unlocked ? '#FF6B4A' : colors.secondaryText} />
            </View>
            <Text style={[styles.achievementLabel, !unlocked && styles.achievementLabelGray]}>{label}</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 16,
        backgroundColor: colors.white,
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: '700',
        color: colors.text,
    },
    headerDate: {
        fontSize: 12,
        color: colors.secondaryText,
    },
    periodContainer: {
        flexDirection: 'row',
        gap: 8,
        paddingHorizontal: 20,
        paddingVertical: 12,
        backgroundColor: colors.white,
    },
    periodButton: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        backgroundColor: colors.border,
        borderRadius: 6,
    },
    periodButtonActive: {
        backgroundColor: colors.text,
    },
    periodText: {
        fontSize: 12,
        color: colors.secondaryText,
        fontWeight: '500',
    },
    periodTextActive: {
        color: colors.white,
    },
    card: {
        backgroundColor: colors.white,
        marginHorizontal: 20,
        marginVertical: 8,
        padding: 16,
        borderRadius: 12,
    },
    summaryCard: {
        backgroundColor: colors.white,
        marginHorizontal: 20,
        marginTop: 12,
        marginBottom: 4,
        padding: 18,
        borderRadius: 18,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    cardTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: colors.text,
    },
    badge: {
        fontSize: 11,
        backgroundColor: colors.primary + '20',
        color: colors.primary,
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
        overflow: 'hidden',
        fontWeight: '600',
    },
    summaryRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 16,
    },
    summaryRing: {
        width: 104,
        height: 104,
        borderRadius: 52,
        borderWidth: 8,
        borderColor: colors.primaryLight,
        justifyContent: 'center',
        alignItems: 'center',
    },
    summaryRingValue: {
        fontSize: 24,
        fontWeight: '700',
        color: colors.primary,
    },
    summaryRingLabel: {
        fontSize: 9,
        color: colors.secondaryText,
        textAlign: 'center',
        paddingHorizontal: 6,
    },
    summarySide: {
        flex: 1,
        gap: 8,
    },
    summaryLine: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    summaryLineLabel: {
        flex: 1,
        fontSize: 12,
        color: colors.secondaryText,
    },
    summaryLineValue: {
        fontSize: 13,
        fontWeight: '700',
        color: colors.text,
    },
    goalsBlock: {
        marginTop: 18,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        paddingTop: 14,
    },
    blockTitle: {
        fontSize: 13,
        fontWeight: '700',
        color: colors.text,
        marginBottom: 10,
    },
    goalRow: {
        marginBottom: 12,
    },
    goalHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 6,
    },
    goalLabel: {
        flex: 1,
        fontSize: 12,
        color: colors.text,
        fontWeight: '500',
    },
    goalValue: {
        fontSize: 12,
        fontWeight: '700',
    },
    progressTrack: {
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.border,
        overflow: 'hidden',
    },
    progressFill: {
        height: 8,
        borderRadius: 4,
    },
    sectionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        marginTop: 18,
        marginBottom: 2,
        paddingHorizontal: 20,
    },
    sectionIcon: {
        width: 32,
        height: 32,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.text,
    },
    chart: {
        marginVertical: 8,
        borderRadius: 12,
    },
    statsContainer: {
        flexDirection: 'row',
        gap: 12,
        paddingHorizontal: 20,
        marginVertical: 8,
    },
    statCard: {
        flex: 1,
        backgroundColor: colors.white,
        padding: 12,
        borderRadius: 12,
        alignItems: 'center',
    },
    statIcon: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 8,
    },
    statLabel: {
        fontSize: 11,
        color: colors.secondaryText,
        marginBottom: 4,
        textAlign: 'center',
    },
    statValue: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.text,
    },
    emptyText: {
        fontSize: 13,
        color: colors.secondaryText,
    },
    historyRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 10,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    historyLeft: {
        flex: 1,
        paddingRight: 12,
    },
    historyTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: colors.text,
    },
    historySubtitle: {
        fontSize: 11,
        color: colors.secondaryText,
        marginTop: 2,
    },
    historyValue: {
        fontSize: 13,
        fontWeight: '700',
        color: colors.primary,
    },
    recordRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 8,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    recordLabel: {
        fontSize: 14,
        color: colors.text,
        fontWeight: '500',
    },
    recordValue: {
        fontSize: 14,
        color: colors.primary,
        fontWeight: '700',
    },
    suggestionRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: 8,
        paddingVertical: 6,
    },
    suggestionText: {
        flex: 1,
        fontSize: 13,
        color: colors.secondaryText,
    },
    achievementsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
        marginTop: 12,
    },
    achievement: {
        width: '23%',
        alignItems: 'center',
    },
    achievementLocked: {
        opacity: 0.5,
    },
    achievementIcon: {
        width: 50,
        height: 50,
        borderRadius: 25,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 8,
    },
    achievementLabel: {
        fontSize: 10,
        color: colors.text,
        textAlign: 'center',
        fontWeight: '500',
    },
    achievementLabelGray: {
        color: colors.secondaryText,
    },
    spacer: {
        height: 30,
    },
});