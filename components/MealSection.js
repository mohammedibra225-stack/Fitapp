import React from 'react';

import {
    Alert,
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';

export default function MealSection({
                                        icon,
                                        title,
                                        calories,
                                        mealName,
                                        mealCalories,
                                        recommendedRecipe,
                                        consumedMeal,
                                        iconColor,
                                        iconBackground,
                                        onAdd,
                                        onMealPress,
                                        onConsumedPress,
                                        empty = false,
                                                                         }) {
                                        const { t } = useI18n();
    const displayRecipe = recommendedRecipe;

    return (
        <View style={styles.container}>

            {/* HEADER */}

            <View style={styles.header}>

                <View style={styles.headerLeft}>

                    <View
                        style={[
                            styles.icon,
                            {
                                backgroundColor: iconBackground,
                            },
                        ]}
                    >
                        <MaterialCommunityIcons
                            name={icon}
                            size={22}
                            color={iconColor}
                        />
                    </View>

                    <View>
                        <Text style={styles.title}>
                            {title}
                        </Text>

                        <Text style={styles.calories}>
                            {calories}
                        </Text>
                    </View>

                </View>

                <TouchableOpacity
                    style={styles.addButton}
                    onPress={onAdd || (() => Alert.alert(title, 'Ajout de repas disponible depuis cette section.', [{ text: 'OK' }]))}
                    activeOpacity={0.7}
                >
                    <Ionicons
                        name="add"
                        size={25}
                        color={colors.primary}
                    />
                </TouchableOpacity>

            </View>

            {/* MEAL */}

            {displayRecipe ? (
                <>
                <TouchableOpacity
                    style={styles.mealCard}
                    onPress={onMealPress}
                    activeOpacity={0.8}
                >

                    <View style={styles.mealImage}>
                        <MaterialCommunityIcons
                            name="silverware-fork-knife"
                            size={30}
                            color={colors.white}
                        />
                    </View>

                    <View style={styles.mealInfo}>
                        <Text style={styles.recommendedLabel}>Recommandé par le plan</Text>
                        <Text style={styles.mealName} numberOfLines={2}>
                            {displayRecipe.name || displayRecipe.label || 'Recette recommandée'}
                        </Text>
                        <Text style={styles.ingredients} numberOfLines={2}>
                            {(displayRecipe.ingredient_lines || []).join(' • ') || 'Voir les ingrédients'}
                        </Text>
                    </View>

                    <View style={styles.mealCaloriesContainer}>
                        <Text style={styles.mealCaloriesNumber}>
                            {Math.round(displayRecipe.calories_kcal || displayRecipe.calories || 0)}
                        </Text>
                        <Text style={styles.kcal}>kcal</Text>
                    </View>
                </TouchableOpacity>
                {consumedMeal && (
                    <TouchableOpacity
                        style={styles.consumedCard}
                        onPress={onConsumedPress}
                        activeOpacity={0.8}
                    >
                        <View style={styles.consumedIcon}>
                            <MaterialCommunityIcons name="check-circle" size={20} color={colors.primary} />
                        </View>
                        <View style={styles.mealInfo}>
                            <Text style={styles.consumedLabel}>Consommé</Text>
                            <Text style={styles.consumedText} numberOfLines={2}>
                                {(consumedMeal.items || []).map((item) => `${item.quantity} ${item.unit} ${item.food_slug}`).join(' • ')}
                            </Text>
                        </View>
                        <Text style={styles.consumedCalories}>
                            {Math.round(consumedMeal.total_calories_kcal)} kcal
                        </Text>
                    </TouchableOpacity>
                )}
                </>
            ) : empty ? (
                <View style={styles.empty}>
                    <Text style={styles.emptyText}>
                        {t('nutrition.no_meal_logged')}
                    </Text>
                </View>
            ) : (
                <TouchableOpacity
                    style={styles.mealCard}
                    onPress={onConsumedPress || onMealPress || (() => Alert.alert(mealName, 'Repas consommé', [{ text: 'OK' }]))}
                    activeOpacity={0.8}
                >

                    <View style={styles.mealImage}>
                        <MaterialCommunityIcons
                            name="food"
                            size={30}
                            color={colors.white}
                        />
                    </View>

                    <View style={styles.mealInfo}>

                        <Text style={styles.mealName}>
                            {mealName}
                        </Text>

                        <Text style={styles.ingredients} numberOfLines={2}>
                            {(consumedMeal?.items || []).map((item) => `${item.quantity} ${item.unit} ${item.food_slug}`).join(' • ')}
                        </Text>

                    </View>

                    <View style={styles.mealCaloriesContainer}>

                        <Text style={styles.mealCaloriesNumber}>
                            {mealCalories}
                        </Text>

                        <Text style={styles.kcal}>
                            kcal
                        </Text>

                    </View>

                </TouchableOpacity>
            )}

        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        marginBottom: 22,
    },

    header: {
        flexDirection: 'row',

        justifyContent: 'space-between',

        alignItems: 'center',

        marginBottom: 10,
    },

    headerLeft: {
        flexDirection: 'row',

        alignItems: 'center',

        gap: 14,
    },

    icon: {
        width: 58,
        height: 58,

        borderRadius: 20,

        alignItems: 'center',
        justifyContent: 'center',
    },

    title: {
        fontSize: 20,

        fontWeight: '800',

        color: colors.text,
    },

    calories: {
        color: colors.secondaryText,

        fontSize: 15,

        marginTop: 2,
    },

    addButton: {
        width: 50,
        height: 50,

        borderRadius: 25,

        borderWidth: 1,

        borderColor: '#D4F4E6',

        alignItems: 'center',
        justifyContent: 'center',
    },

    mealCard: {
        backgroundColor: colors.white,

        minHeight: 110,

        borderRadius: 23,

        padding: 14,

        flexDirection: 'row',

        alignItems: 'center',
    },

    consumedCard: {
        backgroundColor: colors.primaryLight,
        minHeight: 64,
        borderRadius: 16,
        padding: 10,
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 8,
    },

    consumedIcon: {
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: colors.white,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 10,
    },

    consumedLabel: {
        color: colors.primary,
        fontSize: 11,
        fontWeight: '800',
        textTransform: 'uppercase',
    },

    consumedText: {
        color: colors.text,
        fontSize: 13,
        marginTop: 3,
    },

    consumedCalories: {
        color: colors.text,
        fontSize: 12,
        fontWeight: '700',
        marginLeft: 8,
    },

    mealImage: {
        width: 72,
        height: 72,

        borderRadius: 18,

        backgroundColor: '#F6BE75',

        alignItems: 'center',
        justifyContent: 'center',

        marginRight: 15,
    },

    mealInfo: {
        flex: 1,
    },

    mealName: {
        color: colors.text,

        fontSize: 17,

        fontWeight: '800',

        marginBottom: 4,
    },

    recommendedLabel: {
        color: colors.primary,
        fontSize: 11,
        fontWeight: '800',
        marginBottom: 3,
        textTransform: 'uppercase',
    },

    ingredients: {
        color: colors.secondaryText,

        fontSize: 14,
    },

    mealCaloriesContainer: {
        alignItems: 'flex-end',

        marginLeft: 8,
    },

    mealCaloriesNumber: {
        fontSize: 18,

        fontWeight: '800',

        color: colors.text,
    },

    kcal: {
        fontSize: 13,

        color: colors.secondaryText,
    },

    empty: {
        height: 80,

        borderRadius: 20,

        borderWidth: 1,

        borderStyle: 'dashed',

        borderColor: '#D9DDE6',

        backgroundColor: colors.white,

        alignItems: 'center',
        justifyContent: 'center',
    },

    emptyText: {
        color: colors.secondaryText,

        fontSize: 14,
    },
});