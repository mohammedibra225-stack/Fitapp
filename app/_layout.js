import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { I18nProvider } from '../i18n/I18nContext';
import { UserProvider, useUser } from '../user/UserContext';
import {
    NOTIFICATIONS_ENABLED_KEY,
    DEFAULT_MEAL_TIMES,
    MEAL_TYPES,
    setupNotificationChannels,
    requestNotificationPermissions,
    scheduleDailyMealReminder,
    scheduleHydrationReminders,
    logNotificationToBackend,
    addNotificationReceivedListenerSafe,
} from '../services/notificationService';

const MEAL_TIMES_STORAGE_KEY = '@fitapp/meal_reminder_times';
const MEAL_ENABLED_STORAGE_KEY = '@fitapp/meal_reminders_enabled';
const WATER_ENABLED_STORAGE_KEY = '@fitapp/water_reminder_enabled';

function NotificationInitializer() {
    const { user } = useUser();

    useEffect(() => {
        let isMounted = true;
        let unsubscribeListener = null;

        async function initNotifications() {
            try {
                // Initialise les canaux de notifications Android
                await setupNotificationChannels();

                const enabled = await AsyncStorage.getItem(NOTIFICATIONS_ENABLED_KEY);
                // Si la préférence n'a jamais été initialisée, on active par défaut
                const isEnabled = enabled === null || enabled === 'true';

                if (isEnabled) {
                    const granted = await requestNotificationPermissions();
                    if (granted) {
                        // Charger heures repas
                        const storedTimes = await AsyncStorage.getItem(MEAL_TIMES_STORAGE_KEY);
                        const times = storedTimes ? { ...DEFAULT_MEAL_TIMES, ...JSON.parse(storedTimes) } : DEFAULT_MEAL_TIMES;

                        // Vérifier si repas activés
                        const mealVal = await AsyncStorage.getItem(MEAL_ENABLED_STORAGE_KEY);
                        if (mealVal === null || mealVal === 'true') {
                            for (const mealType of MEAL_TYPES) {
                                const timeStr = times[mealType] || DEFAULT_MEAL_TIMES[mealType];
                                await scheduleDailyMealReminder(mealType, timeStr, {
                                    title: `Rappel repas (${mealType})`,
                                    body: `C'est l'heure de votre repas !`,
                                });
                            }
                        }

                        // Vérifier si hydratation activée
                        const waterVal = await AsyncStorage.getItem(WATER_ENABLED_STORAGE_KEY);
                        if (waterVal === null || waterVal === 'true') {
                            await scheduleHydrationReminders(2, {
                                title: 'Rappel hydratation 💧',
                                body: "Pensez à boire un verre d'eau !",
                            });
                        }
                    }
                }

                // Écouter les notifications reçues de manière sécurisée
                if (isMounted) {
                    unsubscribeListener = addNotificationReceivedListenerSafe((notification) => {
                        if (user?.userId) {
                            const title = notification?.request?.content?.title || 'Rappel Fitapp';
                            const body = notification?.request?.content?.body || '';
                            const data = notification?.request?.content?.data || {};
                            const notifType = data.type === 'water_reminder' ? 'water_reminder' : 'meal_reminder';

                            logNotificationToBackend(user.userId, {
                                notificationType: notifType,
                                title,
                                body,
                                languageCode: 'fr',
                            }).catch(() => {});
                        }
                    });
                }
            } catch (err) {
                if (__DEV__) console.warn('[layout] initNotifications erreur:', err);
            }
        }

        initNotifications();

        return () => {
            isMounted = false;
            if (typeof unsubscribeListener === 'function') {
                unsubscribeListener();
            }
        };
    }, [user?.userId]);

    return null;
}

export default function RootLayout() {
    return (
        <I18nProvider>
            <UserProvider>
                <NotificationInitializer />
                <Stack
                    screenOptions={{
                        headerShown: false,
                    }}
                />
            </UserProvider>
        </I18nProvider>
    );
}