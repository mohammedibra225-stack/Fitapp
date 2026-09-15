import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
    Alert,
    ActivityIndicator,
    Linking,
    RefreshControl,
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';

import DayBox from '../components/DayBox';
import MealSection from '../components/MealSection';
import WaterCard from '../components/WaterCard';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { apiRequest, cacheMealPlan, getCachedMealPlan, clearCachedMealPlan } from '../constants/api';
import { useUser } from '../user/UserContext';
import { useRouter, useFocusEffect } from 'expo-router';
import { consumeNutritionRefresh } from '../constants/refreshBus';

// Comme la page Sport : les 7 jours affiches partent d'aujourd'hui
// (index 0 = aujourd'hui) avec le vrai numero du jour dans le mois.
const WEEKDAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

export default function NutritionScreen() {
    const [activeDay, setActiveDay] = useState(0);
    const { t, language } = useI18n();
    const { user } = useUser();
    const [summary, setSummary] = useState(null);
    const [meals, setMeals] = useState([]);
    const [mealPlan, setMealPlan] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const router = useRouter();

    // Date réelle correspondant au jour sélectionné (7 jours à partir
    // d'aujourd'hui, même logique que la page Sport/Training).
    const weekDates = useMemo(() => {
        const today = new Date();
        return Array.from({ length: 7 }, (_, i) => {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            return d;
        });
    }, []);

    const selectedDate = useMemo(() => {
        const d = weekDates[activeDay];
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }, [weekDates, activeDay]);

    const loadNutrition = useCallback(async () => {
        if (!user?.userId) {
            setIsLoading(false);
            return;
        }

        try {
            const [daily, trackedMeals, cachedPlan] = await Promise.all([
                apiRequest(`/nutrition-tracking/daily/${user.userId}?tracked_date=${selectedDate}`),
                apiRequest(`/nutrition-tracking/meals/${user.userId}?start_date=${selectedDate}&end_date=${selectedDate}`),
                getCachedMealPlan(user.userId),
            ]);
            setSummary(daily);
            setMeals(trackedMeals.filter((meal) => meal.consumed_on === selectedDate));

            // Le cache sert de fallback hors-ligne, mais on consulte toujours
            // l'API pour afficher les recettes nouvellement seedées et celles
            // choisies selon le profil courant.
            let plan;
            try {
                plan = await apiRequest(`/nutrition/meal-plan/${user.userId}?language=${language || 'fr'}`);
            } catch (planError) {
                if (!cachedPlan && planError.message.includes('Aucun plan alimentaire')) {
                    plan = await apiRequest(`/nutrition/meal-plan/${user.userId}?language=${language || 'fr'}`, {
                        method: 'POST',
                    });
                } else if (cachedPlan) {
                    plan = cachedPlan;
                } else {
                    throw planError;
                }
            }
            await cacheMealPlan(user.userId, plan);
            setMealPlan(plan);
        } catch (error) {
            if (__DEV__) console.warn('[nutrition] chargement impossible:', error.message);
        } finally {
            setIsLoading(false);
        }
    }, [user?.userId, selectedDate, language]);

    useEffect(() => {
        loadNutrition();
    }, [loadNutrition]);

    const refreshPage = async () => {
        setIsRefreshing(true);
        await loadNutrition();
        setIsRefreshing(false);
    };

    // Ne recharge QUE si un repas vient d'être enregistré
    // (pas à chaque bascule vers la page Nutrition).
    useFocusEffect(
        React.useCallback(() => {
            if (consumeNutritionRefresh()) {
                loadNutrition();
            }
        }, [loadNutrition]),
    );

    const consumed = summary?.consumed || {};
    const targets = summary?.targets || {};
    const findMeal = (mealType) => meals.find((meal) => meal.meal_type === mealType);
    const mealProps = (meal) => meal ? {
        calories: `${Math.round(meal.total_calories_kcal)} kcal`,
        mealName: meal.name || t('nutrition.logged_meal'),
        mealCalories: Math.round(meal.total_calories_kcal).toString(),
    } : {};

    const planDay = mealPlan?.days?.[activeDay];
    const recommendedMeal = (mealType) => planDay?.meals?.find((meal) => meal.meal_type === mealType);
    const mealTypeLabels = {
        breakfast: t('nutrition.breakfast'),
        lunch: t('nutrition.lunch'),
        dinner: t('nutrition.dinner'),
        snack: t('nutrition.snacks'),
    };

    const editPlanMeal = (meal) => {
        router.push({
            pathname: '/edit-plan-meal',
            params: {
                userId: user.userId,
                mealId: meal.id,
                recipeId: meal.recipe?.id && typeof meal.recipe.id === 'string'
                    ? meal.recipe.id
                    : '',
                spoonacularRecipeId: meal.recipe?.id && typeof meal.recipe.id === 'number'
                    ? meal.recipe.id
                    : '',
                calories: meal.target_calories_kcal,
                protein: meal.target_protein_g,
                carbs: meal.target_carbs_g,
                fat: meal.target_fat_g,
            },
        });
    };

    const removePlanRecipe = async (meal) => {
        try {
            await apiRequest(`/nutrition/meal-plan/${user.userId}/meal/${meal.id}/recipe`, {
                method: 'DELETE',
            });
            setMealPlan((current) => {
                const next = {
                ...current,
                days: current.days.map((day) => ({
                    ...day,
                    meals: day.meals.map((item) => item.id === meal.id
                        ? { ...item, recipe: null }
                        : item),
                })),
                };
                cacheMealPlan(user.userId, next).catch(() => {});
                return next;
            });
        } catch (error) {
            Alert.alert(t('common.error'), error.message);
        }
    };

    const showRecipeDetails = async (recipe) => {
        try {
            if (typeof recipe.id === 'number') {
                const youtubeUrl = recipe.youtube_search_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(recipe.name || recipe.label)}`;
                Alert.alert(
                    recipe.name || recipe.label,
                    `${recipe.description || ''}\n\n${t('nutrition.ingredients')}:\n${(recipe.ingredient_lines || []).join('\n')}\n\n${t('nutrition.preparation')}:\n${(recipe.steps || []).map((step) => `${step.number}. ${step.step}`).join('\n')}`,
                    [
                        { text: t('common.close'), style: 'cancel' },
                        { text: t('nutrition.watch_youtube'), onPress: () => Linking.openURL(youtubeUrl) },
                    ]
                );
                return;
            }
            const details = await apiRequest(`/recipes/${recipe.id}?language=${language || 'fr'}`);
            const ingredients = (details.ingredients || [])
                .map((item) => `- ${item.quantity} ${item.unit} ${item.food_name}`)
                .join('\n');
            const steps = (details.steps || [])
                .map((item) => `${item.step_number}. ${item.instruction || t('nutrition.step_unavailable')}`)
                .join('\n');
            const youtubeUrl = details.youtube_search_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(details.name)}`;
            Alert.alert(
                details.name,
                `${details.description || ''}\n\n${t('nutrition.ingredients')}:\n${ingredients || t('nutrition.unavailable')}\n\n${t('nutrition.preparation')}:\n${steps || t('nutrition.unavailable')}`,
                [
                    { text: t('common.close'), style: 'cancel' },
                    { text: t('nutrition.watch_youtube'), onPress: () => Linking.openURL(youtubeUrl) },
                ]
            );
        } catch (error) {
            Alert.alert(t('common.error'), error.message);
        }
    };

    const showAddMeal = (mealType = 'breakfast') => {
        const planMeal = recommendedMeal(mealType);
        const recipe = planMeal?.recipe;
        router.push({
            pathname: '/add-meal',
            params: {
                mealType,
                consumedOn: selectedDate,
                // Repas recommandé du plan (macros déjà calculées)
                recommendedName: recipe?.name || recipe?.label || '',
                recommendedCalories: String(
                    Math.round(recipe?.calories_kcal || recipe?.calories || planMeal?.target_calories_kcal || 0),
                ),
                recommendedProtein: String(Math.round(recipe?.protein_g || planMeal?.target_protein_g || 0)),
                recommendedCarbs: String(Math.round(recipe?.carbs_g || planMeal?.target_carbs_g || 0)),
                recommendedFat: String(Math.round(recipe?.fat_g || planMeal?.target_fat_g || 0)),
            },
        });
    };

    const showMealDetails = (mealName) => {
        Alert.alert(mealName, t('nutrition.meal_logged_info'), [{ text: 'OK' }]);
    };

    // Supprime le plan existant puis en crée un nouveau avec
    // de nouvelles recettes tirées au hasard parmi les 5000+.
    const regeneratePlan = () => {
        Alert.alert(
            t('nutrition.regenerate_title'),
            t('nutrition.regenerate_message'),
            [
                { text: t('common.cancel'), style: 'cancel' },
                {
                    text: t('nutrition.regenerate_confirm'),
                    style: 'destructive',
                    onPress: async () => {
                        setIsLoading(true);
                        try {
                            await apiRequest(`/nutrition/meal-plan/${user.userId}`, { method: 'DELETE' });
                            await clearCachedMealPlan(user.userId);
                            const plan = await apiRequest(`/nutrition/meal-plan/${user.userId}?language=${language || 'fr'}`, {
                                method: 'POST',
                            });
                            await cacheMealPlan(user.userId, plan);
                            setMealPlan(plan);
                        } catch (error) {
                            Alert.alert(t('common.error'), error.message);
                        } finally {
                            setIsLoading(false);
                        }
                    },
                },
            ],
        );
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
                        {t('navigation.nutrition')}
                    </Text>

                    <Text style={styles.date}>
                        {summary?.date || t('nutrition.today')}
                    </Text>

                </View>

                <TouchableOpacity
                    style={styles.addButton}
                    onPress={showAddMeal}
                    activeOpacity={0.7}
                >
                    <Ionicons
                        name="add"
                        size={30}
                        color={colors.text}
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

            {/* DAILY SUMMARY */}

            {isLoading && (
                <ActivityIndicator
                    style={styles.loader}
                    color={colors.primary}
                />
            )}

            <View style={styles.summary}>

                <View style={styles.summaryHeader}>

                    <Text style={styles.summaryTitle}>
                        {t('nutrition.daily_summary')}
                    </Text>

                    <Text style={styles.dailyCalories}>
                        {Math.round(consumed.calories_kcal || 0)}
                        <Text style={styles.dailyTarget}>
                            {' '}/ {Math.round(targets.daily_calories || 0)} kcal
                        </Text>
                    </Text>

                </View>

                <View style={styles.summaryMacros}>

                    <SummaryMacro
                        title={t('nutrition.protein')}
                        value={`${Math.round(consumed.protein_g || 0)}/${Math.round(targets.protein_g || 0)}g`}
                        width={`${targets.protein_g ? Math.min((consumed.protein_g || 0) / targets.protein_g * 100, 100) : 0}%`}
                        color={colors.primary}
                    />

                    <SummaryMacro
                        title={t('nutrition.carbohydrates')}
                        value={`${Math.round(consumed.carbs_g || 0)}/${Math.round(targets.carbs_g || 0)}g`}
                        width={`${targets.carbs_g ? Math.min((consumed.carbs_g || 0) / targets.carbs_g * 100, 100) : 0}%`}
                        color={colors.teal}
                    />

                    <SummaryMacro
                        title={t('nutrition.fat')}
                        value={`${Math.round(consumed.fat_g || 0)}/${Math.round(targets.fat_g || 0)}g`}
                        width={`${targets.fat_g ? Math.min((consumed.fat_g || 0) / targets.fat_g * 100, 100) : 0}%`}
                        color={colors.orange}
                    />

                </View>

            </View>

            {mealPlan && (
                <View style={styles.planCard}>
                    <View style={styles.planHeader}>
                        <View>
                            <Text style={styles.planTitle}>{mealPlan.meal_plan.name}</Text>
                            <Text style={styles.planDates}>
                                {mealPlan.meal_plan.start_date} - {mealPlan.meal_plan.end_date}
                            </Text>
                        </View>
                        <TouchableOpacity onPress={regeneratePlan} activeOpacity={0.7}>
                            <Ionicons name="refresh-outline" size={22} color={colors.primary} />
                        </TouchableOpacity>
                    </View>
                    {mealPlan.budget?.weekly_budget_da != null && (
                        <View style={styles.budgetRow}>
                            <Ionicons
                                name="wallet-outline"
                                size={16}
                                color={mealPlan.budget.status === 'over_budget' ? colors.red : colors.primary}
                            />
                            <Text style={[
                                styles.budgetText,
                                mealPlan.budget.status === 'over_budget' && styles.budgetTextOver,
                            ]}>
                                {t('nutrition.budget_week', {
                                    estimated: Math.round(mealPlan.budget.estimated_cost_da),
                                    budget: Math.round(mealPlan.budget.weekly_budget_da),
                                })}
                                {mealPlan.budget.is_estimate_partial ? ` (${t('nutrition.budget_partial')})` : ''}
                            </Text>
                        </View>
                    )}
                    {planDay?.meals?.map((meal) => (
                        <TouchableOpacity
                            key={meal.id}
                            style={styles.planMeal}
                            onPress={() => meal.recipe
                                ? showRecipeDetails(meal.recipe)
                                : editPlanMeal(meal)}
                            activeOpacity={0.8}
                        >
                            <View>
                                <Text style={styles.planMealTitle}>{mealTypeLabels[meal.meal_type]}</Text>
                                {meal.recipe && (
                                    <Text style={styles.recipeName}>{meal.recipe.name}</Text>
                                )}
                                <Text style={styles.planMealValues}>
                                    {Math.round(meal.target_calories_kcal)} kcal | {Math.round(meal.target_protein_g)}g P | {Math.round(meal.target_carbs_g)}g G | {Math.round(meal.target_fat_g)}g L
                                </Text>
                            </View>
                            <View style={styles.planActions}>
                                <TouchableOpacity onPress={() => editPlanMeal(meal)}>
                                    <Ionicons name="pencil-outline" size={18} color={colors.secondaryText} />
                                </TouchableOpacity>
                                {meal.recipe && (
                                    <TouchableOpacity onPress={() => removePlanRecipe(meal)}>
                                        <Ionicons name="trash-outline" size={18} color={colors.red} />
                                    </TouchableOpacity>
                                )}
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>
            )}

            {/* BREAKFAST */}

            <MealSection
                icon="magnify"
                title={t('nutrition.breakfast')}
                {...mealProps(findMeal('breakfast'))}
                consumedMeal={findMeal('breakfast')}
                iconColor={colors.teal}
                iconBackground={colors.tealLight}
                empty={!findMeal('breakfast')}
                onAdd={() => showAddMeal('breakfast')}
                onConsumedPress={() => showMealDetails(findMeal('breakfast')?.name || t('nutrition.breakfast'))}
            />

            {/* LUNCH */}

            <MealSection
                icon="food-steak"
                title={t('nutrition.lunch')}
                {...mealProps(findMeal('lunch'))}
                consumedMeal={findMeal('lunch')}
                iconColor={colors.primary}
                iconBackground={colors.primaryLight}
                empty={!findMeal('lunch')}
                onAdd={() => showAddMeal('lunch')}
                onConsumedPress={() => showMealDetails(findMeal('lunch')?.name || t('nutrition.lunch'))}
            />

            {/* DINNER */}

            <MealSection
                icon="silverware-fork-knife"
                title={t('nutrition.dinner')}
                {...mealProps(findMeal('dinner'))}
                consumedMeal={findMeal('dinner')}
                empty={!findMeal('dinner')}
                iconColor={colors.secondaryText}
                iconBackground="#EAF0F0"
                onAdd={() => showAddMeal('dinner')}
                onConsumedPress={() => showMealDetails(findMeal('dinner')?.name || t('nutrition.dinner'))}
            />

            {/* SNACKS */}

            <MealSection
                icon="food-apple"
                title={t('nutrition.snacks')}
                {...mealProps(findMeal('snack'))}
                consumedMeal={findMeal('snack')}
                iconColor={colors.red}
                iconBackground="#E9F7E9"
                empty={!findMeal('snack')}
                onAdd={() => showAddMeal('snack')}
                onConsumedPress={() => showMealDetails(findMeal('snack')?.name || t('nutrition.snacks'))}
            />

            {/* WATER */}

            <WaterCard userId={user?.userId} />

        </ScrollView>
    );
}

/* =========================================================
   SUMMARY MACRO
========================================================= */

function SummaryMacro({
                          title,
                          value,
                          width,
                          color,
                      }) {
    return (
        <View style={styles.summaryMacro}>

            <Text style={styles.macroText}>
                {title}{' '}
                <Text style={styles.macroValue}>
                    {value}
                </Text>
            </Text>

            <View style={styles.progressBackground}>
                <View
                    style={[
                        styles.progress,
                        {
                            width,
                            backgroundColor: color,
                        },
                    ]}
                />
            </View>

        </View>
    );
}

const styles = StyleSheet.create({
    content: {
        padding: 20,

        paddingBottom: 35,
    },

    loader: {
        marginBottom: 12,
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

    days: {
        flexDirection: 'row',

        gap: 8,

        marginBottom: 20,
    },

    summary: {
        backgroundColor: colors.white,

        borderRadius: 26,

        padding: 22,

        marginBottom: 28,
    },

    planCard: {
        backgroundColor: colors.white,
        borderRadius: 26,
        padding: 20,
        marginBottom: 28,
    },

    planHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
    },

    planTitle: {
        color: colors.text,
        fontSize: 19,
        fontWeight: '800',
    },

    planDates: {
        color: colors.secondaryText,
        fontSize: 12,
        marginTop: 3,
    },

    budgetRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 10,
    },

    budgetText: {
        color: colors.primary,
        fontSize: 13,
        fontWeight: '700',
    },

    budgetTextOver: {
        color: colors.red,
    },

    planMeal: {
        borderTopWidth: 1,
        borderTopColor: colors.border,
        paddingVertical: 13,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },

    planMealTitle: {
        color: colors.text,
        fontSize: 15,
        fontWeight: '700',
    },

    planMealValues: {
        color: colors.secondaryText,
        fontSize: 12,
        marginTop: 4,
    },

    recipeName: {
        color: colors.primary,
        fontSize: 14,
        fontWeight: '800',
        marginTop: 4,
    },

    planActions: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 14,
        marginLeft: 10,
    },

    suggestions: {
        borderTopWidth: 1,
        borderTopColor: colors.border,
        marginTop: 8,
        paddingTop: 14,
    },

    suggestionsTitle: {
        color: colors.text,
        fontSize: 15,
        fontWeight: '800',
        marginBottom: 8,
    },

    suggestionRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 8,
    },

    suggestionName: {
        color: colors.primary,
        flex: 1,
        marginRight: 8,
    },

    suggestionCalories: {
        color: colors.secondaryText,
        fontSize: 12,
    },

    summaryHeader: {
        flexDirection: 'row',

        alignItems: 'center',

        justifyContent: 'space-between',

        marginBottom: 22,
    },

    summaryTitle: {
        fontSize: 21,

        fontWeight: '800',

        color: colors.text,
    },

    dailyCalories: {
        fontSize: 19,

        fontWeight: '800',

        color: colors.text,
    },

    dailyTarget: {
        color: colors.secondaryText,

        fontSize: 15,

        fontWeight: '500',
    },

    summaryMacros: {
        flexDirection: 'row',

        gap: 16,
    },

    summaryMacro: {
        flex: 1,
    },

    macroText: {
        color: colors.secondaryText,

        fontSize: 14,

        fontWeight: '600',

        marginBottom: 8,
    },

    macroValue: {
        color: colors.text,

        fontWeight: '800',
    },

    progressBackground: {
        height: 8,

        borderRadius: 10,

        backgroundColor: '#E9EBF0',

        overflow: 'hidden',
    },

    progress: {
        height: '100%',

        borderRadius: 10,
    },
});