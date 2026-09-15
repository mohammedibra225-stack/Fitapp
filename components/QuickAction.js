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

export default function QuickAction({
                                        icon,
                                        title,
                                        color,
                                        background,
                                        material = false,
                                        onPress,
                                    }) {
    return (
        <TouchableOpacity
            style={[
                styles.container,
                { backgroundColor: background },
            ]}
            onPress={onPress}
            activeOpacity={0.8}
        >
            {material ? (
                <MaterialCommunityIcons
                    name={icon}
                    size={27}
                    color={color}
                />
            ) : (
                <Ionicons
                    name={icon}
                    size={27}
                    color={color}
                />
            )}

            <Text style={styles.title}>
                {title}
            </Text>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    container: {
        width: '23%',
        minHeight: 125,

        borderRadius: 22,

        padding: 14,

        justifyContent: 'space-between',
    },

    title: {
        fontSize: 14,
        lineHeight: 19,

        color: colors.text,

        fontWeight: '700',
    },
});