import React, { useEffect, useState } from 'react';

import {
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import {
    Ionicons,
    MaterialCommunityIcons,
} from '@expo/vector-icons';

import { useFocusEffect, useRouter } from 'expo-router';

import GoalCard from '../components/GoalCard';
import MacroCard from '../components/MacroCard';
import QuickAction from '../components/QuickAction';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

// Étapes du guide d'utilisation (l'ordre définit la numérotation affichée)
const GUIDE_STEPS = [
    { key: 'guide_profile', icon: 'account-cog-outline', route: '/profile', color: colors.primary, background: colors.primaryLight },
    { key: 'guide_log_meal', icon: 'camera-outline', route: '/meal-analysis', color: colors.teal, background: colors.tealLight },
    { key: 'guide_recipes', icon: 'silverware-fork-knife', route: '/recipes', color: colors.orange, background: colors.orangeLight },
    { key: 'guide_track_day', icon: 'chart-donut', route: '/nutrition', color: colors.blue, background: colors.blueLight },
    { key: 'guide_training', icon: 'dumbbell', route: '/training', color: colors.primary, background: colors.primaryLight },
];

// Conseils pour un mode de vie sain (valables pour les sportifs comme les non-sportifs)
const LIFESTYLE_TIPS = [
    { key: 'tip_hydration', icon: 'cup-water', color: colors.blue, background: colors.blueLight },
    { key: 'tip_sleep', icon: 'moon-waning-crescent', color: colors.primary, background: colors.primaryLight },
    { key: 'tip_move', icon: 'walk', color: colors.teal, background: colors.tealLight },
    { key: 'tip_whole_food', icon: 'food-apple-outline', color: colors.orange, background: colors.orangeLight },
    { key: 'tip_protein', icon: 'arm-flex', color: colors.primary, background: colors.primaryLight },
    { key: 'tip_recovery', icon: 'meditation', color: colors.teal, background: colors.tealLight },
];

export default function HomeScreen() {
    const router = useRouter();
    const { t } = useI18n();
    const { user } = useUser();
    const [dailySummary, setDailySummary] = useState(null);
    const [unreadNotifications, setUnreadNotifications] = useState(0);

    useEffect(() => {
        if (!user?.userId) return;

        let isMounted = true;
        apiRequest(`/nutrition-tracking/daily/${user.userId}`)
            .then((summary) => {
                if (isMounted) setDailySummary(summary);
            })
            .catch((error) => {
                if (__DEV__) console.warn('[home] résumé indisponible:', error.message);
            });

        return () => {
            isMounted = false;
        };
    }, [user?.userId]);

    // Rafraîchit les macros au retour sur la page d'accueil
    useFocusEffect(
        React.useCallback(() => {
            if (!user?.userId) return undefined;
            let isMounted = true;
            apiRequest(`/nutrition-tracking/daily/${user.userId}`)
                .then((summary) => {
                    if (isMounted) setDailySummary(summary);
                })
                .catch(() => {});
            return () => {
                isMounted = false;
            };
        }, [user?.userId]),
    );

    useFocusEffect(
        React.useCallback(() => {
            if (!user?.userId) return undefined;

            let isMounted = true;
            apiRequest(`/notifications/logs/${user.userId}?unread_only=true&limit=100`)
                .then((items) => {
                    if (isMounted) setUnreadNotifications(items.length);
                })
                .catch((error) => {
                    if (__DEV__) console.warn('[home] notifications indisponibles:', error.message);
                });

            return () => {
                isMounted = false;
            };
        }, [user?.userId])
    );

    const consumed = dailySummary?.consumed || {};
    const targets = dailySummary?.targets || {};
    const calories = dailySummary ? (consumed.calories_kcal || 0) : 1840;
    const calorieTarget = dailySummary ? (targets.daily_calories || 0) : 2450;
    const remaining = Math.max(0, calorieTarget - calories);
    const calorieProgress = calorieTarget ? Math.min(calories / calorieTarget, 1) : 0;

    // Dépense estimée (TDEE) renvoyée par /nutrition-tracking/daily -> targets.tdee
    // Le déficit du jour = ce qu'il faut "perdre" par rapport à la dépense.
    // > 0 : déficit (perte de poids) · < 0 : surplus (prise de masse) · 0 : maintien
    const maintenanceCalories = dailySummary ? (targets.tdee || 0) : 2880;
    const calorieDeficit =
        maintenanceCalories && calorieTarget
            ? Math.round(maintenanceCalories - calorieTarget)
            : 0;

    return (
        <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.content}
        >

            {/* HEADER */}

            <View style={styles.header}>

                <View>
                    <Text style={styles.appName}>
                        Fitapp
                    </Text>

                    <Text style={styles.goodMorning}>
                        {t('home.greeting')}
                    </Text>

                    <Text style={styles.username}>
                        {user?.username || 'Fitapp'}
                    </Text>
                </View>

                <View style={styles.headerRight}>

                    <TouchableOpacity
                        style={styles.settingsButton}
                        onPress={() => router.push('/settings')}
                        activeOpacity={0.7}
                    >
                        <Ionicons
                            name="settings-outline"
                            size={26}
                            color={colors.text}
                        />
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.notification}
                        onPress={() => router.push('/notifications')}
                        activeOpacity={0.7}
                    >
                        <Ionicons
                            name="notifications-outline"
                            size={28}
                            color={colors.text}
                        />

                        {unreadNotifications > 0 && (
                            <View style={styles.badge}>
                                <Text style={styles.badgeText}>
                                    {unreadNotifications > 99 ? '99+' : unreadNotifications}
                                </Text>
                            </View>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.avatarButton}
                        onPress={() => router.push('/profile')}
                        activeOpacity={0.7}
                    >
                        <Ionicons
                            name="person-circle-outline"
                            size={44}
                            color={colors.primary}
                        />
                    </TouchableOpacity>

                </View>

            </View>

            {/* GOAL */}

            <GoalCard
                consumed={calories}
                target={calorieTarget}
                remaining={remaining}
                progress={calorieProgress}
                deficit={calorieDeficit}
                isConnected={Boolean(dailySummary)}
            />

            {/* MACROS */}

            <View style={styles.macroRow}>

                <MacroCard
                    icon="arm-flex"
                    title={t('nutrition.protein')}
                    current={Math.round(dailySummary ? (consumed.protein_g || 0) : 132)}
                    target={Math.round(dailySummary ? (targets.protein_g || 0) : 160)}
                    progress={dailySummary && targets.protein_g ? Math.min((consumed.protein_g || 0) / targets.protein_g * 100, 100) : 82}
                    color={colors.primary}
                    background={colors.primaryLight}
                />

                <MacroCard
                    icon="leaf"
                    title={t('nutrition.carbohydrates')}
                    current={Math.round(dailySummary ? (consumed.carbs_g || 0) : 245)}
                    target={Math.round(dailySummary ? (targets.carbs_g || 0) : 300)}
                    progress={dailySummary && targets.carbs_g ? Math.min((consumed.carbs_g || 0) / targets.carbs_g * 100, 100) : 82}
                    color={colors.teal}
                    background={colors.tealLight}
                />

                <MacroCard
                    icon="water"
                    title={t('nutrition.fat')}
                    current={Math.round(dailySummary ? (consumed.fat_g || 0) : 54)}
                    target={Math.round(dailySummary ? (targets.fat_g || 0) : 70)}
                    progress={dailySummary && targets.fat_g ? Math.min((consumed.fat_g || 0) / targets.fat_g * 100, 100) : 77}
                    color={colors.orange}
                    background={colors.orangeLight}
                />

            </View>

            {/* QUICK ACTIONS */}

            <Text style={styles.sectionTitle}>
                {t('home.what_to_do')}
            </Text>

            <View style={styles.actions}>

                <QuickAction
                    icon="camera-outline"
                    title={t('home.analyze_meal')}
                    color={colors.primary}
                    background={colors.primaryLight}
                    onPress={() => router.push('/meal-analysis')}
                />

                <QuickAction
                    icon="magnify"
                    title={t('home.find_recipe')}
                    color={colors.teal}
                    background={colors.tealLight}
                    material
                    onPress={() => router.push('/recipes')}
                />

                <QuickAction
                    icon="silverware-fork-knife"
                    title={t('home.what_can_cook')}
                    color={colors.text}
                    background={colors.white}
                    material
                    onPress={() => router.push('/recipes')}
                />

                <QuickAction
                    icon="robot-outline"
                    title={t('home.ask_assistant')}
                    color={colors.text}
                    background={colors.white}
                    material
                    onPress={() => router.push('/ai')}
                />

            </View>

            {/* GUIDE D'UTILISATION */}

            <Text style={styles.blockTitle}>
                {t('home.guide_title')}
            </Text>

            <Text style={styles.blockSubtitle}>
                {t('home.guide_subtitle')}
            </Text>

            <View style={styles.guideCard}>

                {GUIDE_STEPS.map((step, index) => (
                    <TouchableOpacity
                        key={step.key}
                        style={[
                            styles.guideStep,
                            index === GUIDE_STEPS.length - 1 && styles.guideStepLast,
                        ]}
                        onPress={() => router.push(step.route)}
                        activeOpacity={0.7}
                    >

                        <View style={[styles.guideBadge, { backgroundColor: step.background }]}>
                            <MaterialCommunityIcons
                                name={step.icon}
                                size={22}
                                color={step.color}
                            />
                        </View>

                        <View style={styles.guideText}>

                            <Text style={styles.guideStepTitle}>
                                {`${index + 1}. ${t(`home.${step.key}_title`)}`}
                            </Text>

                            <Text style={styles.guideStepDescription}>
                                {t(`home.${step.key}_desc`)}
                            </Text>

                        </View>

                        <Ionicons
                            name="chevron-forward"
                            size={20}
                            color={colors.secondaryText}
                        />

                    </TouchableOpacity>
                ))}

            </View>

            {/* CONSEILS MODE DE VIE SAIN */}

            <Text style={styles.blockTitle}>
                {t('home.tips_title')}
            </Text>

            <Text style={styles.blockSubtitle}>
                {t('home.tips_subtitle')}
            </Text>

            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.tipsRow}
            >

                {LIFESTYLE_TIPS.map((tip) => (
                    <View key={tip.key} style={styles.tipCard}>

                        <View style={[styles.tipIcon, { backgroundColor: tip.background }]}>
                            <MaterialCommunityIcons
                                name={tip.icon}
                                size={24}
                                color={tip.color}
                            />
                        </View>

                        <Text style={styles.tipTitle}>
                            {t(`home.${tip.key}_title`)}
                        </Text>

                        <Text style={styles.tipDescription}>
                            {t(`home.${tip.key}_desc`)}
                        </Text>

                    </View>
                ))}

            </ScrollView>

        </ScrollView>
    );
}

const styles = StyleSheet.create({
    content: {
        padding: 20,

        paddingBottom: 30,
    },

    header: {
        flexDirection: 'row',

        justifyContent: 'space-between',

        alignItems: 'flex-start',

        marginBottom: 24,
    },

    appName: {
        color: colors.primary,

        fontSize: 27,

        fontWeight: '800',

        marginBottom: 25,
    },

    goodMorning: {
        color: colors.text,

        fontSize: 30,

        fontWeight: '800',
    },

    username: {
        color: colors.secondaryText,

        fontSize: 18,

        marginTop: 4,
    },

    headerRight: {
        flexDirection: 'row',

        alignItems: 'center',

        gap: 18,

        paddingTop: 5,
    },

    notification: {
        position: 'relative',
    },

    settingsButton: {
        padding: 2,
    },

    badge: {
        position: 'absolute',

        right: -5,
        top: -8,

        width: 22,
        height: 22,

        borderRadius: 11,

        backgroundColor: '#FF633C',

        alignItems: 'center',
        justifyContent: 'center',
    },

    badgeText: {
        color: colors.white,

        fontSize: 12,

        fontWeight: '800',
    },

    avatarButton: {
        padding: 2,
    },

    macroRow: {
        flexDirection: 'row',

        marginHorizontal: -4,

        marginBottom: 26,
    },

    sectionTitle: {
        fontSize: 23,

        fontWeight: '800',

        color: colors.text,

        marginBottom: 16,
    },

    actions: {
        flexDirection: 'row',

        justifyContent: 'space-between',

        marginBottom: 30,
    },

    blockTitle: {
        fontSize: 23,

        fontWeight: '800',

        color: colors.text,

        marginBottom: 4,
    },

    blockSubtitle: {
        color: colors.secondaryText,

        fontSize: 14,

        lineHeight: 19,

        marginBottom: 14,
    },

    guideCard: {
        backgroundColor: colors.white,

        borderRadius: 25,

        paddingHorizontal: 16,

        marginBottom: 30,
    },

    guideStep: {
        flexDirection: 'row',

        alignItems: 'center',

        paddingVertical: 14,

        borderBottomWidth: 1,

        borderBottomColor: colors.border,
    },

    guideStepLast: {
        borderBottomWidth: 0,
    },

    guideBadge: {
        width: 42,
        height: 42,

        borderRadius: 14,

        alignItems: 'center',
        justifyContent: 'center',

        marginRight: 14,
    },

    guideText: {
        flex: 1,

        marginRight: 10,
    },

    guideStepTitle: {
        color: colors.text,

        fontSize: 16,

        fontWeight: '700',

        marginBottom: 3,
    },

    guideStepDescription: {
        color: colors.secondaryText,

        fontSize: 13,

        lineHeight: 18,
    },

    tipsRow: {
        paddingRight: 6,
    },

    tipCard: {
        width: 215,

        backgroundColor: colors.white,

        borderRadius: 22,

        padding: 16,

        marginRight: 14,
    },

    tipIcon: {
        width: 44,
        height: 44,

        borderRadius: 15,

        alignItems: 'center',
        justifyContent: 'center',

        marginBottom: 12,
    },

    tipTitle: {
        color: colors.text,

        fontSize: 16,

        fontWeight: '800',

        marginBottom: 5,
    },

    tipDescription: {
        color: colors.secondaryText,

        fontSize: 13,

        lineHeight: 18,
    },
});