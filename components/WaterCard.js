import React, { useEffect, useState } from 'react';

import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { MaterialCommunityIcons } from '@expo/vector-icons';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { apiRequest } from '../constants/api';

const TOTAL_GLASSES = 8;

export default function WaterCard({ userId }) {
    const [totalMl, setTotalMl] = useState(0);
    const [goalMl, setGoalMl] = useState(2000);
    const { t } = useI18n();

    useEffect(() => {
        if (!userId) return;
        apiRequest(`/hydration/${userId}/today`)
            .then((data) => {
                setTotalMl(data.total_ml || 0);
                setGoalMl(data.goal_ml || 2000);
            })
            .catch((error) => {
                if (__DEV__) console.warn('[hydration] chargement impossible:', error.message);
            });
    }, [userId]);

    const glasses = Math.min(Math.floor(totalMl / 250), TOTAL_GLASSES);

    const addGlass = async () => {
        if (!userId) return;
        try {
            const data = await apiRequest(`/hydration/log/${userId}`, {
                method: 'POST',
                body: JSON.stringify({ quantity_ml: 250 }),
            });
            setTotalMl((current) => current + (data.quantity_ml || 250));
        } catch (error) {
            if (__DEV__) console.warn('[hydration] ajout impossible:', error.message);
        }
    };

    return (
        <TouchableOpacity
            style={styles.card}
            onPress={addGlass}
            activeOpacity={0.8}
        >

            <View style={styles.icon}>
                <MaterialCommunityIcons
                    name="water"
                    size={23}
                    color={colors.blue}
                />
            </View>

            <View style={styles.info}>

                <Text style={styles.title}>
                    {t('nutrition.water_intake')}
                </Text>

                <Text style={styles.subtitle}>
                    {t('nutrition.glasses_subtitle', {
                        current: glasses,
                        total: TOTAL_GLASSES,
                    })}
                </Text>

            </View>

            <View style={styles.dots}>

                {Array.from({ length: TOTAL_GLASSES }, (_, index) => index + 1).map(
                    (item) => (
                        <View
                            key={item}
                            style={[
                                styles.dot,
                                item <= glasses && styles.activeDot,
                            ]}
                        />
                    )
                )}

            </View>

        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: colors.white,

        borderRadius: 24,

        padding: 18,

        flexDirection: 'row',

        alignItems: 'center',

        marginTop: 5,
    },

    icon: {
        width: 55,
        height: 55,

        borderRadius: 18,

        backgroundColor: colors.blueLight,

        alignItems: 'center',
        justifyContent: 'center',
    },

    info: {
        flex: 1,

        marginLeft: 15,
    },

    title: {
        fontSize: 18,

        fontWeight: '800',

        color: colors.text,
    },

    subtitle: {
        color: colors.secondaryText,

        fontSize: 15,

        marginTop: 3,
    },

    dots: {
        flexDirection: 'row',

        gap: 6,
    },

    dot: {
        width: 17,
        height: 17,

        borderRadius: 9,

        backgroundColor: '#E5EFFA',
    },

    activeDot: {
        backgroundColor: '#419AF5',
    },
});
