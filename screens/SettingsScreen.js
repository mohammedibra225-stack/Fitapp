import React, { useEffect, useState } from 'react';

import {
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    Switch,
    StyleSheet,
    Alert,
    ActivityIndicator,
} from 'react-native';

import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { SUPPORTED_LANGUAGES } from '../i18n/languages';
import { useUser } from '../user/UserContext';
import TimePickerModal from '../components/TimePickerModal';
import AboutModal from '../components/AboutModal';
import {
    NOTIFICATIONS_ENABLED_KEY,
    DEFAULT_MEAL_TIMES,
    MEAL_TYPES,
    requestNotificationPermissions,
    setupNotificationChannels,
    scheduleDailyMealReminder,
    cancelMealReminder,
    scheduleHydrationReminders,
    cancelHydrationReminders,
    sendTestLocalNotification,
    syncNotificationSettingWithBackend,
    logNotificationToBackend,
} from '../services/notificationService';

const MEAL_TIMES_STORAGE_KEY = '@fitapp/meal_reminder_times';
const MEAL_ENABLED_STORAGE_KEY = '@fitapp/meal_reminders_enabled';
const WATER_ENABLED_STORAGE_KEY = '@fitapp/water_reminder_enabled';

export default function SettingsScreen() {
    const router = useRouter();
    const { t, language, setLanguage, isRTL } = useI18n();
    const { user } = useUser();

    // États principaux de notification
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);
    const [mealRemindersEnabled, setMealRemindersEnabled] = useState(true);
    const [waterReminderEnabled, setWaterReminderEnabled] = useState(true);

    // Heures personnalisées des repas
    const [mealTimes, setMealTimes] = useState(DEFAULT_MEAL_TIMES);

    // Modal de sélection d'heure
    const [activeMealPicker, setActiveMealPicker] = useState(null);
    const [isTestingNotif, setIsTestingNotif] = useState(false);
    const [aboutVisible, setAboutVisible] = useState(false);

    // Chargement initial des préférences
    useEffect(() => {
        let isMounted = true;

        Promise.all([
            AsyncStorage.getItem(NOTIFICATIONS_ENABLED_KEY),
            AsyncStorage.getItem(MEAL_ENABLED_STORAGE_KEY),
            AsyncStorage.getItem(WATER_ENABLED_STORAGE_KEY),
            AsyncStorage.getItem(MEAL_TIMES_STORAGE_KEY),
        ]).then(([globalVal, mealVal, waterVal, timesVal]) => {
            if (!isMounted) return;
            if (globalVal !== null) setNotificationsEnabled(globalVal === 'true');
            if (mealVal !== null) setMealRemindersEnabled(mealVal === 'true');
            if (waterVal !== null) setWaterReminderEnabled(waterVal === 'true');
            if (timesVal !== null) {
                try {
                    setMealTimes({ ...DEFAULT_MEAL_TIMES, ...JSON.parse(timesVal) });
                } catch (e) {}
            }
        }).catch(() => {});

        return () => {
            isMounted = false;
        };
    }, []);

    // Active ou désactive le système global de notifications
    const toggleNotifications = async (value) => {
        setNotificationsEnabled(value);
        await AsyncStorage.setItem(NOTIFICATIONS_ENABLED_KEY, value ? 'true' : 'false');

        if (value) {
            const granted = await requestNotificationPermissions();
            if (!granted) {
                Alert.alert(
                    t('settings.permission_required') || 'Permission requise',
                    t('settings.permission_required_desc') || 'Veuillez autoriser les notifications dans les réglages.'
                );
            } else {
                await setupNotificationChannels();
                if (mealRemindersEnabled) await rescheduleAllMeals(mealTimes);
                if (waterReminderEnabled) await rescheduleWater();
            }
        } else {
            // Désactiver toutes les notifications planifiées
            for (const mealType of MEAL_TYPES) {
                await cancelMealReminder(mealType);
            }
            await cancelHydrationReminders();
        }
    };

    // Reprogramme tous les repas
    const rescheduleAllMeals = async (times) => {
        for (const mealType of MEAL_TYPES) {
            const timeStr = times[mealType] || DEFAULT_MEAL_TIMES[mealType];
            const mealLabel = t(`nutrition.${mealType}`) || mealType;
            await scheduleDailyMealReminder(mealType, timeStr, {
                title: (t('settings.notif_meal_title') || 'Rappel repas : {meal}').replace('{meal}', mealLabel),
                body: (t('settings.notif_meal_body') || "C'est l'heure de votre {meal} !").replace('{meal}', mealLabel),
            });
            if (user?.userId) {
                syncNotificationSettingWithBackend(user.userId, {
                    notificationType: 'meal_reminder',
                    scheduledTime: timeStr,
                    isEnabled: true,
                    title: `Rappel : ${mealLabel}`,
                    body: `C'est l'heure de votre ${mealLabel} !`,
                    languageCode: language,
                }).catch(() => {});
            }
        }
    };

    // Reprogramme l'eau
    const rescheduleWater = async () => {
        await scheduleHydrationReminders(2, {
            title: t('settings.notif_water_title') || 'Rappel hydratation 💧',
            body: t('settings.notif_water_body') || "Pensez à boire un verre d'eau pour rester bien hydraté !",
        });
        if (user?.userId) {
            syncNotificationSettingWithBackend(user.userId, {
                notificationType: 'water_reminder',
                scheduledTime: '10:00:00',
                isEnabled: true,
                title: 'Rappel hydratation 💧',
                body: "Pensez à boire de l'eau régulièrement.",
                languageCode: language,
            }).catch(() => {});
        }
    };

    // Active ou désactive le rappel de chaque repas
    const toggleMealReminders = async (value) => {
        setMealRemindersEnabled(value);
        await AsyncStorage.setItem(MEAL_ENABLED_STORAGE_KEY, value ? 'true' : 'false');

        if (value && notificationsEnabled) {
            const granted = await requestNotificationPermissions();
            if (granted) {
                await setupNotificationChannels();
                await rescheduleAllMeals(mealTimes);
            }
        } else {
            for (const mealType of MEAL_TYPES) {
                await cancelMealReminder(mealType);
            }
        }
    };

    // Active ou désactive le rappel d'hydratation
    const toggleWaterReminder = async (value) => {
        setWaterReminderEnabled(value);
        await AsyncStorage.setItem(WATER_ENABLED_STORAGE_KEY, value ? 'true' : 'false');

        if (value && notificationsEnabled) {
            const granted = await requestNotificationPermissions();
            if (granted) {
                await setupNotificationChannels();
                await rescheduleWater();
            }
        } else {
            await cancelHydrationReminders();
        }
    };

    // Changement d'heure pour un repas spécifique (ex: dîner à 20:00)
    const handleTimeSave = async (newTime) => {
        if (!activeMealPicker) return;
        const updatedTimes = { ...mealTimes, [activeMealPicker]: newTime };
        setMealTimes(updatedTimes);
        await AsyncStorage.setItem(MEAL_TIMES_STORAGE_KEY, JSON.stringify(updatedTimes));

        if (notificationsEnabled && mealRemindersEnabled) {
            const mealLabel = t(`nutrition.${activeMealPicker}`) || activeMealPicker;
            await scheduleDailyMealReminder(activeMealPicker, newTime, {
                title: (t('settings.notif_meal_title') || 'Rappel repas : {meal}').replace('{meal}', mealLabel),
                body: (t('settings.notif_meal_body') || "C'est l'heure de votre {meal} !").replace('{meal}', mealLabel),
            });
            if (user?.userId) {
                syncNotificationSettingWithBackend(user.userId, {
                    notificationType: 'meal_reminder',
                    scheduledTime: newTime,
                    isEnabled: true,
                    title: `Rappel : ${mealLabel}`,
                    body: `C'est l'heure de votre ${mealLabel} !`,
                    languageCode: language,
                }).catch(() => {});
            }
        }
        setActiveMealPicker(null);
    };

    // Déclencher une notification test immédiate
    const handleTestNotification = async () => {
        setIsTestingNotif(true);
        try {
            const granted = await requestNotificationPermissions();
            if (!granted) {
                Alert.alert(
                    t('settings.permission_required') || 'Permission requise',
                    t('settings.permission_required_desc') || 'Veuillez autoriser les notifications dans les réglages.'
                );
                return;
            }

            const id = await sendTestLocalNotification({
                title: t('settings.notif_water_title') || 'Rappel hydratation 💧',
                body: t('settings.notif_water_body') || "Pensez à boire un verre d'eau pour rester bien hydraté !",
                data: { origin: 'settings_test' },
            });

            if (user?.userId) {
                logNotificationToBackend(user.userId, {
                    notificationType: 'water_reminder',
                    title: 'Rappel hydratation 💧',
                    body: "Pensez à boire un grand verre d'eau !",
                    languageCode: language,
                }).catch(() => {});
            }

            if (id) {
                Alert.alert('Fitapp', t('settings.test_notification_sent') || 'Notification envoyée ! Regardez vos notifications.');
            } else {
                Alert.alert('Fitapp', t('settings.test_notification_error') || 'Impossible d\'envoyer la notification.');
            }
        } catch (e) {
            Alert.alert('Fitapp', e?.message || 'Erreur inconnue');
        } finally {
            setIsTestingNotif(false);
        }
    };

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            {/* HEADER */}
            <View style={[styles.header, isRTL && styles.headerRTL]}>
                <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => router.back()}
                    activeOpacity={0.7}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                    <Ionicons
                        name={isRTL ? 'arrow-forward' : 'arrow-back'}
                        size={24}
                        color={colors.text}
                    />
                </TouchableOpacity>

                <Text style={styles.headerTitle}>{t('settings.title')}</Text>

                <View style={styles.backButton} />
            </View>

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.content}
            >
                {/* SECTION LANGUE */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('settings.language')}
                </Text>

                <View style={styles.card}>
                    {SUPPORTED_LANGUAGES.map((item, index) => {
                        const selected = item.code === language;

                        return (
                            <TouchableOpacity
                                key={item.code}
                                style={[
                                    styles.row,
                                    isRTL && styles.rowRTL,
                                    index < SUPPORTED_LANGUAGES.length - 1 &&
                                        styles.rowBorder,
                                ]}
                                onPress={() => setLanguage(item.code)}
                                activeOpacity={0.7}
                            >
                                <Text
                                    style={[
                                        styles.rowLabel,
                                        isRTL && styles.textRTL,
                                    ]}
                                >
                                    {item.name}
                                </Text>

                                {selected && (
                                    <Ionicons
                                        name="checkmark-circle"
                                        size={22}
                                        color={colors.primary}
                                    />
                                )}
                            </TouchableOpacity>
                        );
                    })}
                </View>

                {/* SECTION NOTIFICATIONS */}
                <Text
                    style={[
                        styles.sectionTitle,
                        styles.sectionSpacing,
                        isRTL && styles.textRTL,
                    ]}
                >
                    {t('settings.notifications')}
                </Text>

                <View style={styles.card}>
                    {/* Interrupteur Général */}
                    <View style={[styles.row, isRTL && styles.rowRTL]}>
                        <View style={styles.notifTextWrapper}>
                            <Text
                                style={[
                                    styles.rowLabel,
                                    isRTL && styles.textRTL,
                                ]}
                            >
                                {t('settings.notifications')}
                            </Text>

                            <Text
                                style={[
                                    styles.rowDescription,
                                    isRTL && styles.textRTL,
                                ]}
                            >
                                {t('settings.notifications_description')}
                            </Text>
                        </View>

                        <Switch
                            value={notificationsEnabled}
                            onValueChange={toggleNotifications}
                            trackColor={{
                                false: colors.border,
                                true: colors.primaryLight,
                            }}
                            thumbColor={
                                notificationsEnabled
                                    ? colors.primary
                                    : colors.white
                            }
                        />
                    </View>

                    {/* Rappel Hydratation */}
                    {notificationsEnabled && (
                        <View style={[styles.subSection, styles.rowBorderTop]}>
                            <View style={[styles.row, isRTL && styles.rowRTL]}>
                                <View style={[styles.iconBadge, { backgroundColor: colors.blueLight }]}>
                                    <MaterialCommunityIcons name="water" size={22} color={colors.blue} />
                                </View>
                                <View style={styles.notifTextWrapper}>
                                    <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                                        {t('settings.water_reminder')}
                                    </Text>
                                    <Text style={[styles.rowDescription, isRTL && styles.textRTL]}>
                                        {t('settings.water_reminder_description')}
                                    </Text>
                                </View>
                                <Switch
                                    value={waterReminderEnabled}
                                    onValueChange={toggleWaterReminder}
                                    trackColor={{
                                        false: colors.border,
                                        true: colors.blueLight,
                                    }}
                                    thumbColor={
                                        waterReminderEnabled
                                            ? colors.blue
                                            : colors.white
                                    }
                                />
                            </View>
                        </View>
                    )}

                    {/* Rappels de Repas */}
                    {notificationsEnabled && (
                        <View style={[styles.subSection, styles.rowBorderTop]}>
                            <View style={[styles.row, isRTL && styles.rowRTL]}>
                                <View style={[styles.iconBadge, { backgroundColor: colors.primaryLight }]}>
                                    <MaterialCommunityIcons name="silverware-fork-knife" size={20} color={colors.primary} />
                                </View>
                                <View style={styles.notifTextWrapper}>
                                    <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                                        {t('settings.meal_reminders')}
                                    </Text>
                                    <Text style={[styles.rowDescription, isRTL && styles.textRTL]}>
                                        {t('settings.meal_reminders_description')}
                                    </Text>
                                </View>
                                <Switch
                                    value={mealRemindersEnabled}
                                    onValueChange={toggleMealReminders}
                                    trackColor={{
                                        false: colors.border,
                                        true: colors.primaryLight,
                                    }}
                                    thumbColor={
                                        mealRemindersEnabled
                                            ? colors.primary
                                            : colors.white
                                    }
                                />
                            </View>

                            {/* Liste détaillée des repas avec heure modifiable */}
                            {mealRemindersEnabled && (
                                <View style={styles.mealsContainer}>
                                    {MEAL_TYPES.map((mealKey) => {
                                        const mealLabel = t(`nutrition.${mealKey}`) || mealKey;
                                        const time = mealTimes[mealKey] || DEFAULT_MEAL_TIMES[mealKey];
                                        return (
                                            <TouchableOpacity
                                                key={mealKey}
                                                style={[styles.mealRow, isRTL && styles.rowRTL]}
                                                onPress={() => setActiveMealPicker(mealKey)}
                                                activeOpacity={0.7}
                                            >
                                                <View style={styles.mealLeft}>
                                                    <Ionicons
                                                        name="time-outline"
                                                        size={18}
                                                        color={colors.secondaryText}
                                                        style={{ marginRight: 8 }}
                                                    />
                                                    <Text style={[styles.mealName, isRTL && styles.textRTL]}>
                                                        {mealLabel}
                                                    </Text>
                                                </View>
                                                <View style={styles.timeBadge}>
                                                    <Text style={styles.timeBadgeText}>{time}</Text>
                                                    <Ionicons
                                                        name={isRTL ? 'chevron-back' : 'chevron-forward'}
                                                        size={14}
                                                        color={colors.primary}
                                                        style={{ marginLeft: 4 }}
                                                    />
                                                </View>
                                            </TouchableOpacity>
                                        );
                                    })}
                                </View>
                            )}
                        </View>
                    )}

                    {/* Bouton pour tester une notification immédiate sur le téléphone */}
                    {notificationsEnabled && (
                        <TouchableOpacity
                            style={[styles.testRow, styles.rowBorderTop, isRTL && styles.rowRTL]}
                            onPress={handleTestNotification}
                            disabled={isTestingNotif}
                            activeOpacity={0.7}
                        >
                            <View style={[styles.iconBadge, { backgroundColor: '#F0F3F6' }]}>
                                <Ionicons name="notifications-outline" size={18} color={colors.text} />
                            </View>
                            <Text style={[styles.testRowText, isRTL && styles.textRTL]}>
                                {t('settings.test_notification')}
                            </Text>
                            {isTestingNotif ? (
                                <ActivityIndicator size="small" color={colors.primary} />
                            ) : (
                                <Ionicons
                                    name={isRTL ? 'chevron-back' : 'chevron-forward'}
                                    size={18}
                                    color={colors.secondaryText}
                                />
                            )}
                        </TouchableOpacity>
                    )}
                </View>

                {/* SECTION À PROPOS */}
                <Text
                    style={[
                        styles.sectionTitle,
                        styles.sectionSpacing,
                        isRTL && styles.textRTL,
                    ]}
                >
                    {t('settings.about') || 'À propos'}
                </Text>

                <View style={styles.card}>
                    <TouchableOpacity
                        style={[styles.row, isRTL && styles.rowRTL]}
                        onPress={() => setAboutVisible(true)}
                        activeOpacity={0.7}
                    >
                        <View style={[styles.iconBadge, { backgroundColor: colors.primaryLight }]}>
                            <Ionicons name="information-circle-outline" size={20} color={colors.primary} />
                        </View>

                        <Text style={[styles.testRowText, isRTL && styles.textRTL]}>
                            {t('settings.about_app') || "À propos de l'application"}
                        </Text>

                        <Ionicons
                            name={isRTL ? 'chevron-back' : 'chevron-forward'}
                            size={18}
                            color={colors.secondaryText}
                        />
                    </TouchableOpacity>
                </View>
            </ScrollView>

            {/* Modal À propos */}
            <AboutModal
                visible={aboutVisible}
                onClose={() => setAboutVisible(false)}
            />

            {/* Modal de modification de l'heure d'un repas */}
            <TimePickerModal
                visible={!!activeMealPicker}
                initialTime={activeMealPicker ? (mealTimes[activeMealPicker] || DEFAULT_MEAL_TIMES[activeMealPicker]) : '20:00'}
                title={activeMealPicker ? `${t('settings.change_time')} : ${t(`nutrition.${activeMealPicker}`) || activeMealPicker}` : ''}
                onClose={() => setActiveMealPicker(null)}
                onSave={handleTimeSave}
            />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: colors.background,
    },

    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 8,
        paddingBottom: 12,
    },

    headerRTL: {
        flexDirection: 'row-reverse',
    },

    backButton: {
        width: 40,
        height: 40,
        alignItems: 'center',
        justifyContent: 'center',
    },

    headerTitle: {
        fontSize: 18,
        fontWeight: '800',
        color: colors.text,
    },

    content: {
        padding: 20,
        paddingBottom: 40,
    },

    sectionTitle: {
        fontSize: 15,
        fontWeight: '700',
        color: colors.secondaryText,
        marginBottom: 10,
        textTransform: 'uppercase',
    },

    sectionSpacing: {
        marginTop: 28,
    },

    textRTL: {
        textAlign: 'right',
    },

    card: {
        backgroundColor: colors.white,
        borderRadius: 18,
        borderWidth: 1,
        borderColor: colors.border,
        overflow: 'hidden',
    },

    row: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 16,
        paddingHorizontal: 18,
        minHeight: 60,
    },

    rowRTL: {
        flexDirection: 'row-reverse',
    },

    rowBorder: {
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },

    rowBorderTop: {
        borderTopWidth: 1,
        borderTopColor: colors.border,
    },

    subSection: {
        backgroundColor: colors.white,
    },

    iconBadge: {
        width: 36,
        height: 36,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 12,
    },

    mealsContainer: {
        backgroundColor: '#FAFAFC',
        paddingHorizontal: 18,
        paddingVertical: 8,
        borderTopWidth: 1,
        borderTopColor: colors.border,
    },

    mealRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 10,
    },

    mealLeft: {
        flexDirection: 'row',
        alignItems: 'center',
    },

    mealName: {
        fontSize: 15,
        fontWeight: '600',
        color: colors.text,
    },

    timeBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.primaryLight,
        paddingVertical: 6,
        paddingHorizontal: 10,
        borderRadius: 10,
    },

    timeBadgeText: {
        fontSize: 14,
        fontWeight: '700',
        color: colors.primary,
    },

    testRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 14,
        paddingHorizontal: 18,
    },

    testRowText: {
        flex: 1,
        fontSize: 15,
        fontWeight: '600',
        color: colors.text,
    },

    rowLabel: {
        fontSize: 16,
        color: colors.text,
        fontWeight: '600',
    },

    rowDescription: {
        fontSize: 13,
        color: colors.secondaryText,
        marginTop: 3,
        maxWidth: 240,
    },

    notifTextWrapper: {
        flex: 1,
        paddingRight: 12,
    },
});
