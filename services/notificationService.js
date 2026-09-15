import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiRequest } from '../constants/api';

// Accès paresseux et sécurisé à expo-notifications
function getNotificationsModule() {
    try {
        const notif = require('expo-notifications');
        return notif;
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] expo-notifications non accessible:', e?.message || e);
        return null;
    }
}

// Initialise le handler d'alerte en avant-plan si disponible
try {
    const mod = getNotificationsModule();
    if (mod && typeof mod.setNotificationHandler === 'function') {
        mod.setNotificationHandler({
            handleNotification: async () => ({
                shouldShowBanner: true,
                shouldShowList: true,
                shouldPlaySound: true,
                shouldSetBadge: false,
            }),
        });
    }
} catch (e) {
    if (__DEV__) console.warn('[notificationService] setNotificationHandler non disponible:', e);
}

export const NOTIFICATIONS_ENABLED_KEY = '@fitapp/notifications_enabled';
export const MEAL_NOTIF_PREFIX = '@fitapp/notif_identifier_meal_';
export const WATER_NOTIF_KEY = '@fitapp/notif_identifier_water';

export const MEAL_TYPES = ['breakfast', 'lunch', 'snack', 'dinner'];

export const DEFAULT_MEAL_TIMES = {
    breakfast: '08:00',
    lunch: '12:30',
    snack: '16:30',
    dinner: '20:00',
};

export const DEFAULT_WATER_CONFIG = {
    enabled: true,
    intervalHours: 2, // Toutes les 2 heures
    startHour: 8,
    endHour: 22,
};

/**
 * Configure les canaux de notifications pour Android (requis Android 8+)
 */
export async function setupNotificationChannels() {
    if (Platform.OS !== 'android') return;
    const notif = getNotificationsModule();
    if (!notif || typeof notif.setNotificationChannelAsync !== 'function') return;
    try {
        await notif.setNotificationChannelAsync('meals', {
            name: 'Rappels de repas',
            importance: notif.AndroidImportance?.HIGH ?? 4,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#16C784',
            sound: 'default',
        });

        await notif.setNotificationChannelAsync('hydration', {
            name: 'Rappels hydratation',
            importance: notif.AndroidImportance?.DEFAULT ?? 3,
            vibrationPattern: [0, 250],
            lightColor: '#419AF5',
            sound: 'default',
        });
    } catch (e) {
        // En Expo Go sur Android, le provider natif de channels est parfois absent ou null.
        // On intercepte silencieusement pour ne pas polluer la console ni bloquer l'appli.
        if (__DEV__) {
            const msg = e?.message || String(e);
            if (!msg.includes('NotificationsChannelsProvider')) {
                console.warn('[notificationService] setupNotificationChannels erreur:', e);
            }
        }
    }
}

/**
 * Demande les permissions au système (Android / iOS)
 */
export async function requestNotificationPermissions() {
    const notif = getNotificationsModule();
    if (!notif || !notif.getPermissionsAsync) return false;
    try {
        const { status: existingStatus } = await notif.getPermissionsAsync();
        let finalStatus = existingStatus;
        if (existingStatus !== 'granted' && notif.requestPermissionsAsync) {
            const { status } = await notif.requestPermissionsAsync();
            finalStatus = status;
        }
        return finalStatus === 'granted';
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] requestPermissionsAsync erreur:', e);
        return false;
    }
}

/**
 * Programme un rappel quotidien pour un repas précis (ex: dîner à 20:00)
 * @param {string} mealType - 'breakfast' | 'lunch' | 'snack' | 'dinner'
 * @param {string} timeString - Format "HH:mm" (ex: "20:00")
 * @param {object} content - { title, body }
 */
export async function scheduleDailyMealReminder(mealType, timeString, content) {
    const notif = getNotificationsModule();
    if (!notif || !notif.scheduleNotificationAsync) return null;
    const parts = (timeString || '20:00').split(':');
    const hour = parseInt(parts[0], 10) || 0;
    const minute = parseInt(parts[1], 10) || 0;

    // Annule l'ancien rappel si existant
    await cancelMealReminder(mealType);

    try {
        const triggerType = notif.SchedulableTriggerInputTypes?.DAILY ?? 'daily';
        const identifier = await notif.scheduleNotificationAsync({
            content: {
                title: content?.title || 'Rappel repas',
                body: content?.body || "C'est l'heure de votre repas !",
                data: { type: 'meal_reminder', mealType, time: timeString },
                sound: 'default',
            },
            trigger: {
                type: triggerType,
                hour,
                minute,
                channelId: 'meals',
            },
        });

        await AsyncStorage.setItem(`${MEAL_NOTIF_PREFIX}${mealType}`, identifier);
        return identifier;
    } catch (e) {
        if (__DEV__) console.warn(`[notificationService] Erreur scheduleMealReminder (${mealType}):`, e);
        return null;
    }
}

/**
 * Annule le rappel d'un repas spécifique
 */
export async function cancelMealReminder(mealType) {
    const notif = getNotificationsModule();
    if (!notif || !notif.cancelScheduledNotificationAsync) return;
    try {
        const key = `${MEAL_NOTIF_PREFIX}${mealType}`;
        const existingId = await AsyncStorage.getItem(key);
        if (existingId) {
            await notif.cancelScheduledNotificationAsync(existingId);
            await AsyncStorage.removeItem(key);
        }
    } catch (e) {
        if (__DEV__) console.warn(`[notificationService] Erreur cancelMealReminder (${mealType}):`, e);
    }
}

/**
 * Programme les rappels d'hydratation (ex: toutes les 2h entre 8h et 22h)
 * @param {number} intervalHours - Intervalle en heures (défaut: 2)
 * @param {object} content - { title, body }
 */
export async function scheduleHydrationReminders(intervalHours = 2, content) {
    const notif = getNotificationsModule();
    if (!notif || !notif.scheduleNotificationAsync) return [];
    await cancelHydrationReminders();

    const storedIds = [];
    const validInterval = Math.max(1, Math.min(6, intervalHours));

    try {
        const triggerType = notif.SchedulableTriggerInputTypes?.DAILY ?? 'daily';
        for (let hour = DEFAULT_WATER_CONFIG.startHour; hour <= DEFAULT_WATER_CONFIG.endHour; hour += validInterval) {
            const identifier = await notif.scheduleNotificationAsync({
                content: {
                    title: content?.title || 'Rappel hydratation 💧',
                    body: content?.body || "Pensez à boire un verre d'eau pour rester bien hydraté !",
                    data: { type: 'water_reminder', hour },
                    sound: 'default',
                },
                trigger: {
                    type: triggerType,
                    hour,
                    minute: 0,
                    channelId: 'hydration',
                },
            });
            storedIds.push(identifier);
        }

        await AsyncStorage.setItem(WATER_NOTIF_KEY, JSON.stringify(storedIds));
        return storedIds;
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] Erreur scheduleHydrationReminders:', e);
        return [];
    }
}

/**
 * Annule tous les rappels d'hydratation
 */
export async function cancelHydrationReminders() {
    const notif = getNotificationsModule();
    if (!notif || !notif.cancelScheduledNotificationAsync) return;
    try {
        const raw = await AsyncStorage.getItem(WATER_NOTIF_KEY);
        if (raw) {
            const ids = JSON.parse(raw);
            if (Array.isArray(ids)) {
                await Promise.all(
                    ids.map((id) => notif.cancelScheduledNotificationAsync(id).catch(() => { }))
                );
            }
            await AsyncStorage.removeItem(WATER_NOTIF_KEY);
        }
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] Erreur cancelHydrationReminders:', e);
    }
}

/**
 * Annule toutes les notifications programmées par l'application
 */
export async function cancelAllLocalNotifications() {
    const notif = getNotificationsModule();
    if (!notif || !notif.cancelAllScheduledNotificationsAsync) return;
    try {
        await notif.cancelAllScheduledNotificationsAsync();
        for (const mealType of MEAL_TYPES) {
            await AsyncStorage.removeItem(`${MEAL_NOTIF_PREFIX}${mealType}`);
        }
        await AsyncStorage.removeItem(WATER_NOTIF_KEY);
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] Erreur cancelAllLocalNotifications:', e);
    }
}

/**
 * Envoie une notification locale test immédiate pour vérifier le système du téléphone
 */
export async function sendTestLocalNotification({ title, body, data }) {
    const notif = getNotificationsModule();
    if (!notif || !notif.scheduleNotificationAsync) return null;
    try {
        const hasPermission = await requestNotificationPermissions();
        if (!hasPermission) return null;

        await setupNotificationChannels();

        return await notif.scheduleNotificationAsync({
            content: {
                title: title || 'Fitapp Notification',
                body: body || 'Ceci est un test de notification.',
                data: data || {},
                sound: 'default',
            },
            trigger: null, // Déclenchement immédiat
        });
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] sendTestLocalNotification erreur:', e);
        return null;
    }
}

/**
 * Synchronise les réglages avec le backend pour un utilisateur donné
 */
export async function syncNotificationSettingWithBackend(userId, { notificationType, scheduledTime, isEnabled, title, body, languageCode = 'fr' }) {
    if (!userId) return null;
    try {
        // Récupère d'abord les réglages existants de l'utilisateur
        const settings = await apiRequest(`/notifications/settings/${userId}`);
        const existing = (settings || []).find((s) => {
            if (s.notification_type !== notificationType) return false;
            // Pour meal_reminder avec heure spécifique, matcher sur scheduled_time
            if (scheduledTime) {
                const sTime = (s.scheduled_time || '').substring(0, 5);
                const targetTime = scheduledTime.substring(0, 5);
                return sTime === targetTime;
            }
            return true;
        });

        const formattedTime = scheduledTime ? (scheduledTime.length === 5 ? `${scheduledTime}:00` : scheduledTime) : null;
        const payload = {
            notification_type: notificationType,
            scheduled_time: formattedTime,
            days_of_week: [0, 1, 2, 3, 4, 5, 6],
            title: title || null,
            body: body || null,
            is_enabled: isEnabled,
            language_code: languageCode,
        };

        if (existing) {
            return await apiRequest(`/notifications/settings/${existing.id}`, {
                method: 'PATCH',
                body: JSON.stringify(payload),
            });
        } else {
            return await apiRequest(`/notifications/settings/${userId}`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        }
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] syncNotificationSettingWithBackend erreur:', e);
        return null;
    }
}

/**
 * Enregistre un log de notification dans le backend (historique visible sur la cloche)
 */
export async function logNotificationToBackend(userId, { notificationType, title, body, languageCode = 'fr' }) {
    if (!userId) return null;
    try {
        return await apiRequest(`/notifications/logs/${userId}`, {
            method: 'POST',
            body: JSON.stringify({
                notification_type: notificationType,
                title,
                body,
                language_code: languageCode,
            }),
        });
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] logNotificationToBackend erreur:', e);
        return null;
    }
}

/**
 * Permet d'écouter les notifications reçues de manière universelle et sûre
 */
export function addNotificationReceivedListenerSafe(callback) {
    const notif = getNotificationsModule();
    if (!notif || typeof notif.addNotificationReceivedListener !== 'function') {
        return () => {};
    }
    try {
        const sub = notif.addNotificationReceivedListener(callback);
        return () => {
            if (sub && typeof sub.remove === 'function') {
                sub.remove();
            }
        };
    } catch (e) {
        if (__DEV__) console.warn('[notificationService] addNotificationReceivedListenerSafe erreur:', e);
        return () => {};
    }
}
