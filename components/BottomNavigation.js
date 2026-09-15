import React from 'react';

import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import {
    Ionicons,
    MaterialCommunityIcons,
} from '@expo/vector-icons';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';

export default function BottomNavigation({
                                             activeTab,
                                             setActiveTab,
                                         }) {
    const { t, isRTL } = useI18n();

    const items = [
        {
            id: 'home',
            label: t('navigation.home'),
            icon: 'home-outline',
        },
        {
            id: 'nutrition',
            label: t('navigation.nutrition'),
            icon: 'silverware-fork-knife',
            material: true,
        },
        {
            id: 'training',
            label: t('navigation.training'),
            icon: 'dumbbell',
            material: true,
        },
        {
            id: 'progress',
            label: t('navigation.progress'),
            icon: 'chart-bar',
            material: true,
        },
        {
            id: 'ai',
            label: t('navigation.assistant'),
            icon: 'robot-outline',
            material: true,
        },
    ];

    return (
        <View style={[styles.container, isRTL && styles.containerRTL]}>
            {items.map((item) => {
                const active = activeTab === item.id;

                return (
                    <TouchableOpacity
                        key={item.id}
                        style={styles.item}
                        onPress={() => setActiveTab(item.id)}
                        activeOpacity={0.7}
                    >
                        {item.material ? (
                            <MaterialCommunityIcons
                                name={item.icon}
                                size={23}
                                color={
                                    active
                                        ? colors.primary
                                        : colors.secondaryText
                                }
                            />
                        ) : (
                            <Ionicons
                                name={item.icon}
                                size={24}
                                color={
                                    active
                                        ? colors.primary
                                        : colors.secondaryText
                                }
                            />
                        )}

                        <Text
                            style={[
                                styles.label,
                                active && styles.activeLabel,
                            ]}
                        >
                            {item.label}
                        </Text>
                    </TouchableOpacity>
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        height: 88,
        backgroundColor: colors.white,

        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-around',

        borderTopWidth: 1,
        borderTopColor: colors.border,
    },

    containerRTL: {
        flexDirection: 'row-reverse',
    },

    item: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        gap: 5,
    },

    label: {
        fontSize: 12,
        color: colors.secondaryText,
        fontWeight: '500',
    },

    activeLabel: {
        color: colors.primary,
        fontWeight: '700',
    },
});
