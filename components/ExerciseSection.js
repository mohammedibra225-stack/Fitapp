import React from 'react';

import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
} from 'react-native';

import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

import { colors } from '../constants/colors';
import { comingSoon } from '../constants/comingSoon';

export default function ExerciseSection({
                                             icon,
                                             name,
                                             sets,
                                             done = false,
                                             iconColor,
                                             iconBackground,
                                             onPress,
                                         }) {
    return (
        <TouchableOpacity
            style={styles.card}
            onPress={onPress || (() => comingSoon(name))}
            activeOpacity={0.8}
        >

            <View
                style={[
                    styles.icon,
                    { backgroundColor: iconBackground },
                ]}
            >
                <MaterialCommunityIcons
                    name={icon}
                    size={26}
                    color={iconColor}
                />
            </View>

            <View style={styles.info}>
                <Text style={styles.name}>
                    {name}
                </Text>

                <Text style={styles.sets}>
                    {sets}
                </Text>
            </View>

            <View
                style={[
                    styles.check,
                    done && styles.checkDone,
                ]}
            >
                {done && (
                    <Ionicons
                        name="checkmark"
                        size={18}
                        color={colors.white}
                    />
                )}
            </View>

        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: colors.white,

        borderRadius: 22,

        padding: 14,

        flexDirection: 'row',

        alignItems: 'center',

        marginBottom: 14,
    },

    icon: {
        width: 56,
        height: 56,

        borderRadius: 18,

        alignItems: 'center',
        justifyContent: 'center',

        marginRight: 14,
    },

    info: {
        flex: 1,
    },

    name: {
        color: colors.text,

        fontSize: 17,

        fontWeight: '800',

        marginBottom: 3,
    },

    sets: {
        color: colors.secondaryText,

        fontSize: 14,
    },

    check: {
        width: 30,
        height: 30,

        borderRadius: 15,

        borderWidth: 1.5,

        borderColor: colors.border,

        alignItems: 'center',
        justifyContent: 'center',
    },

    checkDone: {
        backgroundColor: colors.primary,
        borderColor: colors.primary,
    },
});
