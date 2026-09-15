import React from 'react';

import {
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { colors } from '../constants/colors';

export default function DayBox({
                                   day,
                                   number,
                                   active = false,
                                   onPress,
                               }) {
    return (
        <TouchableOpacity
            style={[
                styles.container,
                active && styles.active,
            ]}
            onPress={onPress}
            activeOpacity={0.7}
        >
            <Text
                style={[
                    styles.day,
                    active && styles.activeText,
                ]}
            >
                {day}
            </Text>

            <Text
                style={[
                    styles.number,
                    active && styles.activeText,
                ]}
            >
                {number}
            </Text>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    container: {
        // Flex-based width instead of a fixed pixel width so that 7 boxes
        // always add up to exactly the available row width, on any screen
        // size, instead of overflowing off the right edge on narrower phones.
        flex: 1,
        height: 90,

        borderRadius: 19,

        backgroundColor: colors.white,

        alignItems: 'center',
        justifyContent: 'center',
    },

    active: {
        backgroundColor: colors.primary,
    },

    day: {
        fontSize: 15,

        fontWeight: '600',

        color: colors.secondaryText,

        marginBottom: 7,
    },

    number: {
        fontSize: 19,

        fontWeight: '800',

        color: colors.text,
    },

    activeText: {
        color: colors.white,
    },
});
