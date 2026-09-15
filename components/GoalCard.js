import React from 'react';

import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { MaterialCommunityIcons } from '@expo/vector-icons';

import { colors } from '../constants/colors';
import { comingSoon } from '../constants/comingSoon';
import { useI18n } from '../i18n/I18nContext';

/**
 * Carte "Objectif du jour".
 *
 * Props :
 *  - consumed  : kcal déjà consommées aujourd'hui
 *  - target    : kcal visées aujourd'hui (targets.daily_calories)
 *  - remaining : kcal restantes (target - consumed, jamais négatif)
 *  - progress  : 0 -> 1
 *  - deficit   : écart entre la dépense estimée (TDEE) et l'objectif calorique.
 *                > 0  => kcal à perdre chaque jour (déficit)
 *                < 0  => kcal de surplus (prise de masse)
 *                = 0  => maintien, la ligne est masquée
 */
export default function GoalCard({
    consumed = 0,
    target = 0,
    remaining = 0,
    progress = 0,
    deficit = 0,
    isConnected = false,
}) {
    const { t } = useI18n();

    const safeProgress = Math.max(0, Math.min(progress || 0, 1));
    const percent = Math.round(safeProgress * 100);

    const roundedDeficit = Math.round(deficit || 0);
    const isSurplus = roundedDeficit < 0;
    const showDeficit = roundedDeficit !== 0;

    const format = (value) => Math.round(value || 0).toLocaleString();

    return (
        <View style={styles.card}>

            {/* HEADER */}

            <View style={styles.header}>

                <View style={styles.titleContainer}>
                    <MaterialCommunityIcons
                        name="target"
                        size={22}
                        color={colors.primary}
                    />

                    <Text
                        style={styles.title}
                        numberOfLines={1}
                    >
                        {t('home.today_goal')}
                    </Text>
                </View>


            </View>

            {/* CALORIES */}

            <View style={styles.caloriesContainer}>

                {/* Anneau des calories consommées */}

                <View style={styles.circle}>

                    <View style={styles.circleInner}>

                        <MaterialCommunityIcons
                            name="fire"
                            size={22}
                            color="#FF5B35"
                        />

                        <Text
                            style={styles.consumed}
                            numberOfLines={1}
                            adjustsFontSizeToFit
                            minimumFontScale={0.6}
                        >
                            {format(consumed)}
                        </Text>

                        <Text
                            style={styles.circleLabel}
                            numberOfLines={2}
                        >
                            kcal {t('home.kcal_consumed')}
                        </Text>

                    </View>

                </View>

                {/* Colonne des chiffres */}

                <View style={styles.stats}>

                    <View style={styles.statRow}>
                        <Text
                            style={styles.statLabel}
                            numberOfLines={2}
                        >
                            {t('home.kcal_target')}
                        </Text>

                        <Text
                            style={styles.statValue}
                            numberOfLines={1}
                            adjustsFontSizeToFit
                            minimumFontScale={0.7}
                        >
                            {format(target)}
                        </Text>
                    </View>

                    <View style={styles.statSeparator} />

                    <View style={styles.statRow}>
                        <Text
                            style={styles.statLabel}
                            numberOfLines={2}
                        >
                            {t('home.kcal_remaining')}
                        </Text>

                        <Text
                            style={[styles.statValue, { color: colors.primary }]}
                            numberOfLines={1}
                            adjustsFontSizeToFit
                            minimumFontScale={0.7}
                        >
                            {format(remaining)}
                        </Text>
                    </View>

                    {showDeficit && (
                        <>
                            <View style={styles.statSeparator} />

                            <View style={styles.statRow}>
                                <Text
                                    style={styles.statLabel}
                                    numberOfLines={2}
                                >
                                    {isSurplus
                                        ? t('home.kcal_surplus')
                                        : t('home.kcal_to_lose')}
                                </Text>

                                <Text
                                    style={[
                                        styles.statValue,
                                        { color: isSurplus ? colors.blue : '#FF5B35' },
                                    ]}
                                    numberOfLines={1}
                                    adjustsFontSizeToFit
                                    minimumFontScale={0.7}
                                >
                                    {isSurplus ? '+' : '−'}
                                    {format(Math.abs(roundedDeficit))}
                                </Text>
                            </View>
                        </>
                    )}

                </View>

            </View>

            {/* PROGRESS */}

            <View style={styles.progressBackground}>
                <View style={[styles.progress, { width: `${percent}%` }]} />
            </View>

            <Text style={styles.percentage}>
                <Text style={styles.green}>
                    {percent}%
                </Text>{' '}
                {t('home.of_daily_goal')}
            </Text>

            {!isConnected && (
                <Text style={styles.connectionStatus}>
                    Données du serveur indisponibles
                </Text>
            )}

        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: colors.white,

        borderRadius: 28,

        padding: 20,

        marginBottom: 18,
    },

    header: {
        flexDirection: 'row',

        alignItems: 'center',

        justifyContent: 'space-between',

        gap: 10,
    },

    titleContainer: {
        flexDirection: 'row',

        alignItems: 'center',

        gap: 9,

        // Laisse le bouton "Modifier" garder sa taille naturelle
        // et évite que le titre le pousse hors de la carte.
        flexShrink: 1,
    },

    title: {
        fontSize: 20,

        fontWeight: '800',

        color: colors.text,

        flexShrink: 1,
    },

    editButton: {
        flexDirection: 'row',

        alignItems: 'center',

        gap: 5,

        borderWidth: 1,

        borderColor: '#C9F3E0',

        paddingHorizontal: 12,
        paddingVertical: 8,

        borderRadius: 25,

        flexShrink: 0,
    },

    editText: {
        color: colors.primary,

        fontSize: 13,

        fontWeight: '600',
    },

    caloriesContainer: {
        flexDirection: 'row',

        alignItems: 'center',

        marginTop: 20,

        marginBottom: 20,

        gap: 16,
    },

    circle: {
        // Taille fixe : l'anneau ne doit jamais être écrasé par la colonne
        // de chiffres, qui elle est élastique (flex: 1).
        width: 132,
        height: 132,

        borderRadius: 66,

        borderWidth: 12,

        borderColor: colors.primary,

        alignItems: 'center',
        justifyContent: 'center',

        flexShrink: 0,
    },

    circleInner: {
        alignItems: 'center',

        paddingHorizontal: 6,
    },

    consumed: {
        fontSize: 25,

        fontWeight: '800',

        color: colors.text,

        marginTop: 2,
    },

    circleLabel: {
        fontSize: 12,

        color: colors.secondaryText,

        lineHeight: 15,

        textAlign: 'center',
    },

    stats: {
        // Prend toute la largeur restante : 1 ligne par chiffre,
        // donc plus de colonnes serrées côte à côte.
        flex: 1,

        minWidth: 0,
    },

    statRow: {
        flexDirection: 'row',

        alignItems: 'center',

        justifyContent: 'space-between',

        gap: 10,

        paddingVertical: 9,
    },

    statLabel: {
        fontSize: 13,

        color: colors.secondaryText,

        lineHeight: 17,

        flexShrink: 1,
    },

    statValue: {
        fontSize: 21,

        fontWeight: '800',

        color: colors.text,

        flexShrink: 0,
    },

    statSeparator: {
        height: 1,

        backgroundColor: '#E6E8EE',
    },

    progressBackground: {
        height: 14,

        backgroundColor: '#DFF5EB',

        borderRadius: 10,

        overflow: 'hidden',
    },

    progress: {
        height: '100%',

        backgroundColor: colors.primary,

        borderRadius: 10,
    },

    percentage: {
        textAlign: 'center',

        marginTop: 12,

        fontSize: 15,

        color: colors.secondaryText,

        fontWeight: '600',
    },

    green: {
        color: colors.primary,

        fontWeight: '800',
    },

    connectionStatus: {
        color: colors.secondaryText,
        fontSize: 12,
        marginTop: 8,
        textAlign: 'center',
    },
});
