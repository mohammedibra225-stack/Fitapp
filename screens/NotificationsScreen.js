import React, { useCallback, useEffect, useState } from 'react';
import {
    ActivityIndicator,
    FlatList,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { apiRequest } from '../constants/api';
import { colors } from '../constants/colors';
import { useUser } from '../user/UserContext';

export default function NotificationsScreen() {
    const router = useRouter();
    const { user } = useUser();
    const [notifications, setNotifications] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadNotifications = useCallback(async () => {
        if (!user?.userId) {
            setIsLoading(false);
            return;
        }

        setError(null);
        try {
            const data = await apiRequest(`/notifications/logs/${user.userId}?limit=50`);
            setNotifications(data);
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsLoading(false);
        }
    }, [user?.userId]);

    useEffect(() => {
        loadNotifications();
    }, [loadNotifications]);

    const markAsRead = async (notification) => {
        if (notification.is_read) return;

        try {
            const updated = await apiRequest(`/notifications/logs/${notification.id}/read`, {
                method: 'PATCH',
            });
            setNotifications((current) => current.map((item) => (
                item.id === updated.id ? updated : item
            )));
        } catch (requestError) {
            setError(requestError.message);
        }
    };

    const renderNotification = ({ item }) => (
        <TouchableOpacity
            style={[styles.notification, !item.is_read && styles.unread]}
            onPress={() => markAsRead(item)}
            activeOpacity={0.8}
        >
            <View style={styles.icon}>
                <Ionicons name="notifications" size={20} color={colors.primary} />
            </View>
            <View style={styles.notificationContent}>
                <Text style={styles.notificationTitle}>{item.title}</Text>
                {item.body ? <Text style={styles.notificationBody}>{item.body}</Text> : null}
                <Text style={styles.notificationDate}>
                    {new Date(item.sent_at).toLocaleString()}
                </Text>
            </View>
            {!item.is_read && <View style={styles.unreadDot} />}
        </TouchableOpacity>
    );

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            <View style={styles.header}>
                <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={styles.title}>Notifications</Text>
                <TouchableOpacity style={styles.backButton} onPress={loadNotifications}>
                    <Ionicons name="refresh-outline" size={23} color={colors.text} />
                </TouchableOpacity>
            </View>

            {isLoading ? (
                <ActivityIndicator style={styles.loader} size="large" color={colors.primary} />
            ) : error ? (
                <View style={styles.center}>
                    <Text style={styles.error}>{error}</Text>
                    <TouchableOpacity style={styles.retryButton} onPress={loadNotifications}>
                        <Text style={styles.retryText}>Réessayer</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <FlatList
                    data={notifications}
                    renderItem={renderNotification}
                    keyExtractor={(item) => item.id}
                    contentContainerStyle={notifications.length ? styles.list : styles.emptyList}
                    ListEmptyComponent={<Text style={styles.empty}>Aucune notification</Text>}
                />
            )}
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: { flex: 1, backgroundColor: colors.background },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 10,
    },
    backButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
    title: { fontSize: 20, fontWeight: '800', color: colors.text },
    list: { padding: 20, paddingTop: 10 },
    notification: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.white,
        borderRadius: 18,
        padding: 16,
        marginBottom: 12,
    },
    unread: { borderLeftWidth: 4, borderLeftColor: colors.primary },
    icon: {
        width: 42,
        height: 42,
        borderRadius: 21,
        backgroundColor: colors.primaryLight,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 12,
    },
    notificationContent: { flex: 1 },
    notificationTitle: { fontSize: 16, fontWeight: '800', color: colors.text },
    notificationBody: { marginTop: 4, color: colors.secondaryText, fontSize: 14 },
    notificationDate: { marginTop: 7, color: colors.secondaryText, fontSize: 12 },
    unreadDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: colors.primary, marginLeft: 8 },
    loader: { marginTop: 40 },
    center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 },
    error: { color: colors.red, textAlign: 'center', marginBottom: 16 },
    retryButton: { backgroundColor: colors.primary, borderRadius: 10, paddingHorizontal: 18, paddingVertical: 11 },
    retryText: { color: colors.white, fontWeight: '700' },
    emptyList: { flexGrow: 1, alignItems: 'center', justifyContent: 'center' },
    empty: { color: colors.secondaryText, fontSize: 16 },
});
