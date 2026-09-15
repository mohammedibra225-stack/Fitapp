import React from 'react';

import {
    View,
    Text,
    StyleSheet,
} from 'react-native';

import { MaterialCommunityIcons } from '@expo/vector-icons';

import { colors } from '../constants/colors';

export default function MacroCard({
                                      icon,
                                      title,
                                      current,
                                      target,
                                      progress,
                                      color,
                                      background,
                                      unit = 'g',
                                      subtitle,
                                  }) {
    return (
        <View style={styles.card}>

            <View
                style={[
                    styles.iconContainer,
                    { backgroundColor: background },
                ]}
            >
                <MaterialCommunityIcons
                    name={icon}
                    size={22}
                    color={color}
                />
            </View>

            <Text style={styles.title}>
                {title}
            </Text>

            <Text style={styles.values}>
                {current}
                <Text style={styles.target}>
                    {' '}/ {target} {unit}
                </Text>
            </Text>

            <View style={styles.progressBackground}>
                <View
                    style={[
                        styles.progress,
                        {
                            width: `${progress}%`,
                            backgroundColor: color,
                        },
                    ]}
                />
            </View>

            {subtitle ? (
                <Text style={styles.subtitle} numberOfLines={1}>
                    {subtitle}
                </Text>
            ) : null}

        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        flex: 1,

        backgroundColor: colors.white,

        borderRadius: 22,

        padding: 16,

        marginHorizontal: 4,

        minHeight: 165,
    },

    iconContainer: {
        width: 48,
        height: 48,

        borderRadius: 24,

        alignItems: 'center',
        justifyContent: 'center',

        marginBottom: 12,
    },

    title: {
        fontSize: 17,
        fontWeight: '700',
        color: colors.text,

        marginBottom: 10,
    },

    values: {
        fontSize: 20,
        fontWeight: '800',
        color: colors.text,
    },

    target: {
        fontSize: 15,
        fontWeight: '500',
        color: colors.secondaryText,
    },

    progressBackground: {
        height: 8,

        borderRadius: 10,

        backgroundColor: '#E8E9EE',

        marginTop: 14,

        overflow: 'hidden',
    },

    progress: {
        height: '100%',
        borderRadius: 10,
    },

    subtitle: {
        fontSize: 12,
        fontWeight: '600',
        color: colors.secondaryText,
        marginTop: 8,
    },
});