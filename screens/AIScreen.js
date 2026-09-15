import React, { useState, useEffect, useRef } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    FlatList,
    ActivityIndicator,
    Alert,
    ScrollView,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

const STORAGE_CONVERSATION_KEY = '@fitapp/assistant_conversation';


export default function AIScreen() {
    const router = useRouter();
    const { t, language, isRTL } = useI18n();
    const { user } = useUser();

    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState(null);

    const flatListRef = useRef(null);

    // Chargement de l'historique local ou initialisation
    useEffect(() => {
        let isMounted = true;
        AsyncStorage.getItem(STORAGE_CONVERSATION_KEY)
            .then((raw) => {
                if (isMounted && raw) {
                    try {
                        const parsed = JSON.parse(raw);
                        if (parsed.messages && Array.isArray(parsed.messages)) {
                            setMessages(parsed.messages);
                        }
                        if (parsed.conversationId) {
                            setConversationId(parsed.conversationId);
                        }
                    } catch (e) {
                        // ignore parse error
                    }
                }
            })
            .catch(() => {});

        return () => {
            isMounted = false;
        };
    }, []);

    // Sauvegarde de l'historique local lors des changements
    const persistConversation = async (newMessages, currentConvId) => {
        try {
            await AsyncStorage.setItem(
                STORAGE_CONVERSATION_KEY,
                JSON.stringify({
                    messages: newMessages,
                    conversationId: currentConvId,
                })
            );
        } catch (e) {
            // ignore
        }
    };

    // Réinitialiser la conversation
    const handleResetConversation = () => {
        Alert.alert(
            t('assistant.confirm_clear_title'),
            t('assistant.confirm_clear_msg'),
            [
                { text: t('common.cancel'), style: 'cancel' },
                {
                    text: t('common.continue'),
                    style: 'destructive',
                    onPress: async () => {
                        setMessages([]);
                        setConversationId(null);
                        await AsyncStorage.removeItem(STORAGE_CONVERSATION_KEY);
                    },
                },
            ]
        );
    };

    // Envoyer un message vers l'API Assistant FastAPI
    const handleSendMessage = async (textToSend) => {
        const queryText = (typeof textToSend === 'string' ? textToSend : inputMessage).trim();
        if (!queryText || isLoading) return;

        const userMsg = {
            id: Date.now().toString(),
            role: 'user',
            content: queryText,
            timestamp: new Date().toISOString(),
        };

        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setInputMessage('');
        setIsLoading(true);

        // Faire défiler vers le bas
        setTimeout(() => {
            flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);

        try {
            const payload = {
                message: queryText,
                user_id: user?.userId || null,
                conversation_id: conversationId || null,
                language: language || 'fr',
            };

            const response = await apiRequest('/api/v1/assistant/chat', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            const newConvId = response.conversation_id || conversationId;
            if (response.conversation_id) {
                setConversationId(response.conversation_id);
            }

            const aiMsg = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                tool_calls: response.tool_calls || [],
                timestamp: new Date().toISOString(),
            };

            const finalMessages = [...updatedMessages, aiMsg];
            setMessages(finalMessages);
            await persistConversation(finalMessages, newConvId);

            setTimeout(() => {
                flatListRef.current?.scrollToEnd({ animated: true });
            }, 100);
        } catch (error) {
            const errorMsg = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: error.message || t('assistant.error_generic'),
                isError: true,
                timestamp: new Date().toISOString(),
            };
            const finalMessages = [...updatedMessages, errorMsg];
            setMessages(finalMessages);
            await persistConversation(finalMessages, conversationId);
        } finally {
            setIsLoading(false);
        }
    };

    // Questions rapides suggérées
    const quickPrompts = [
        { id: '1', text: t('assistant.quick_protein'), icon: 'arm-flex' },
        { id: '2', text: t('assistant.quick_calories'), icon: 'food-apple' },
        { id: '3', text: t('assistant.quick_inventory'), icon: 'fridge' },
        { id: '4', text: t('assistant.quick_workout'), icon: 'dumbbell' },
    ];

    const renderMessage = ({ item }) => {
        const isUser = item.role === 'user';

        if (isUser) {
            return (
                <View style={[styles.messageRow, styles.userMessageRow, isRTL && styles.messageRowRTL]}>
                    <View style={[styles.messageBubble, styles.userBubble]}>
                        <Text style={styles.userMessageText}>{item.content}</Text>
                    </View>
                </View>
            );
        }

        const hasTools = item.tool_calls && item.tool_calls.length > 0;

        return (
            <View style={[styles.messageRow, isRTL && styles.messageRowRTL]}>
                <View style={styles.aiAvatar}>
                    <MaterialCommunityIcons name="robot" size={16} color={colors.white} />
                </View>
                <View style={styles.aiMessageWrapper}>
                    <View
                        style={[
                            styles.messageBubble,
                            styles.aiBubble,
                            item.isError && styles.errorBubble,
                        ]}
                    >
                        <Text style={[styles.messageText, item.isError && styles.errorText]}>
                            {item.content}
                        </Text>
                    </View>

                    {hasTools && (
                        <View style={styles.toolBadge}>
                            <MaterialCommunityIcons name="check-circle" size={13} color={colors.primary} />
                            <Text style={styles.toolBadgeText}>{t('assistant.tool_used')}</Text>
                        </View>
                    )}
                </View>
            </View>
        );
    };

    const renderEmptyState = () => (
        <View style={styles.emptyContainer}>
            <View style={styles.emptyIconContainer}>
                <MaterialCommunityIcons name="robot" size={48} color={colors.primary} />
            </View>
            <Text style={styles.emptyTitle}>{t('assistant.welcome_title')}</Text>
            <Text style={styles.emptySubtitle}>{t('assistant.welcome_subtitle')}</Text>

            <View style={styles.quickPromptsContainer}>
                {quickPrompts.map((p) => (
                    <TouchableOpacity
                        key={p.id}
                        style={styles.quickPromptButton}
                        activeOpacity={0.7}
                        onPress={() => handleSendMessage(p.text)}
                    >
                        <MaterialCommunityIcons name={p.icon} size={18} color={colors.primary} />
                        <Text style={styles.quickPromptText}>{p.text}</Text>
                    </TouchableOpacity>
                ))}
            </View>
        </View>
    );

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.container}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
        >
            {/* Header avec action retour & menu nouvelle conversation */}
            <View style={[styles.header, isRTL && styles.headerRTL]}>
                <View style={styles.headerContent}>
                    <View style={styles.aiHeaderAvatar}>
                        <MaterialCommunityIcons name="robot" size={20} color={colors.white} />
                    </View>
                    <View style={styles.headerText}>
                        <Text style={styles.headerTitle}>{t('assistant.title')}</Text>
                        <View style={styles.statusRow}>
                            <View style={styles.onlineDot} />
                            <Text style={styles.headerStatus}>{t('assistant.listening')}</Text>
                        </View>
                    </View>
                </View>
                <View style={styles.headerActions}>
                    <TouchableOpacity
                        style={styles.headerIconButton}
                        onPress={handleResetConversation}
                        accessibilityLabel={t('assistant.clear_history')}
                    >
                        <MaterialCommunityIcons name="refresh" size={22} color={colors.text} />
                    </TouchableOpacity>
                </View>
            </View>

            {/* Liste de conversation */}
            <FlatList
                ref={flatListRef}
                data={messages}
                renderItem={renderMessage}
                keyExtractor={(item) => item.id}
                contentContainerStyle={[
                    styles.chatContent,
                    messages.length === 0 && styles.chatContentEmpty,
                ]}
                showsVerticalScrollIndicator={false}
                ListEmptyComponent={renderEmptyState}
                onContentSizeChange={() => {
                    if (messages.length > 0) {
                        flatListRef.current?.scrollToEnd({ animated: true });
                    }
                }}
            />

            {/* Indicateur de chargement */}
            {isLoading && (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="small" color={colors.primary} />
                    <Text style={styles.loadingText}>{t('assistant.thinking')}</Text>
                </View>
            )}

            {/* Zone de saisie et bouton d'envoi */}
            <View style={[styles.inputContainer, isRTL && styles.inputContainerRTL]}>
                <TextInput
                    style={[styles.input, isRTL && styles.inputRTL]}
                    placeholder={t('assistant.placeholder')}
                    placeholderTextColor={colors.secondaryText}
                    value={inputMessage}
                    onChangeText={setInputMessage}
                    multiline
                    maxLength={1000}
                    editable={!isLoading}
                />
                <TouchableOpacity
                    style={[
                        styles.sendButton,
                        (!inputMessage.trim() || isLoading) && styles.sendButtonDisabled,
                    ]}
                    onPress={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || isLoading}
                    activeOpacity={0.7}
                >
                    <MaterialCommunityIcons
                        name="send"
                        size={20}
                        color={colors.white}
                        style={isRTL ? { transform: [{ rotate: '180deg' }] } : null}
                    />
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: colors.white,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    headerRTL: {
        flexDirection: 'row-reverse',
    },
    headerContent: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    aiHeaderAvatar: {
        width: 38,
        height: 38,
        borderRadius: 19,
        backgroundColor: colors.primary,
        justifyContent: 'center',
        alignItems: 'center',
    },
    headerText: {
        gap: 2,
    },
    headerTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.text,
    },
    statusRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    onlineDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.primary,
    },
    headerStatus: {
        fontSize: 12,
        color: colors.secondaryText,
    },
    headerActions: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    headerIconButton: {
        padding: 6,
        borderRadius: 20,
    },
    chatContent: {
        padding: 16,
        paddingBottom: 20,
    },
    chatContentEmpty: {
        flexGrow: 1,
        justifyContent: 'center',
    },
    messageRow: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        gap: 8,
        marginBottom: 14,
    },
    messageRowRTL: {
        flexDirection: 'row-reverse',
    },
    userMessageRow: {
        justifyContent: 'flex-end',
    },
    aiAvatar: {
        width: 30,
        height: 30,
        borderRadius: 15,
        backgroundColor: colors.primary,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 4,
    },
    aiMessageWrapper: {
        maxWidth: '80%',
    },
    messageBubble: {
        paddingHorizontal: 14,
        paddingVertical: 10,
        borderRadius: 16,
    },
    aiBubble: {
        backgroundColor: colors.white,
        borderBottomLeftRadius: 4,
        borderWidth: 1,
        borderColor: colors.border,
    },
    errorBubble: {
        backgroundColor: '#FEE2E2',
        borderColor: '#FCA5A5',
    },
    errorText: {
        color: colors.red,
    },
    userBubble: {
        maxWidth: '80%',
        backgroundColor: colors.primary,
        borderBottomRightRadius: 4,
    },
    messageText: {
        fontSize: 15,
        lineHeight: 22,
        color: colors.text,
    },
    userMessageText: {
        fontSize: 15,
        lineHeight: 22,
        color: colors.white,
    },
    toolBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        marginTop: 4,
        marginLeft: 2,
    },
    toolBadgeText: {
        fontSize: 11,
        color: colors.primary,
        fontWeight: '500',
    },
    emptyContainer: {
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 30,
    },
    emptyIconContainer: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: colors.primaryLight,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 16,
    },
    emptyTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.text,
        textAlign: 'center',
        marginBottom: 8,
    },
    emptySubtitle: {
        fontSize: 14,
        color: colors.secondaryText,
        textAlign: 'center',
        lineHeight: 20,
        marginBottom: 24,
    },
    quickPromptsContainer: {
        width: '100%',
        gap: 10,
    },
    quickPromptButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        paddingHorizontal: 14,
        paddingVertical: 12,
        backgroundColor: colors.white,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: colors.border,
    },
    quickPromptText: {
        fontSize: 14,
        fontWeight: '500',
        color: colors.text,
        flex: 1,
    },
    loadingContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingHorizontal: 20,
        paddingVertical: 6,
    },
    loadingText: {
        fontSize: 13,
        color: colors.secondaryText,
        fontStyle: 'italic',
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        paddingHorizontal: 12,
        paddingVertical: 10,
        backgroundColor: colors.white,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        gap: 10,
    },
    inputContainerRTL: {
        flexDirection: 'row-reverse',
    },
    input: {
        flex: 1,
        maxHeight: 100,
        minHeight: 40,
        paddingHorizontal: 14,
        paddingVertical: 10,
        backgroundColor: colors.lightGray || '#F3F4F6',
        borderRadius: 20,
        fontSize: 15,
        color: colors.text,
    },
    inputRTL: {
        textAlign: 'right',
    },
    sendButton: {
        width: 42,
        height: 42,
        borderRadius: 21,
        backgroundColor: colors.primary,
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonDisabled: {
        backgroundColor: colors.secondaryText,
        opacity: 0.5,
    },
});
