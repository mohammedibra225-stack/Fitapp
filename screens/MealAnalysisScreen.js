import React, { useEffect, useState, useCallback } from 'react';
import {
    ActivityIndicator,
    Alert,
    Image,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
// uploadAsync / FileSystemUploadType ont ete deplaces dans le sous-module
// "legacy" depuis expo-file-system SDK 54+ (l'import racine ne les expose plus).
import * as FileSystem from 'expo-file-system/legacy';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_BASE_URL, apiRequest } from '../constants/api';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { requestNutritionRefresh } from '../constants/refreshBus';

// Types MIME/extension pour construire le fichier envoyé au backend.
function guessFileMeta(uri) {
    const extMatch = /\.(\w+)$/.exec(uri.split('?')[0]);
    const ext = (extMatch ? extMatch[1] : 'jpg').toLowerCase();
    const mimeByExt = {
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
        webp: 'image/webp',
        heic: 'image/heic',
        heif: 'image/heif',
    };
    return {
        name: `meal.${ext}`,
        type: mimeByExt[ext] || 'image/jpeg',
    };
}

export default function MealAnalysisScreen() {
    const router = useRouter();
    const { t, language } = useI18n();
    const { user } = useUser();

    const [imageUri, setImageUri] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysis, setAnalysis] = useState(null);
    const [isAdding, setIsAdding] = useState(false);
    const [quota, setQuota] = useState(null); // { limit, used, remaining }
    const [serviceStatus, setServiceStatus] = useState(null); // { available, model_installed, detail }
    const [elapsedSeconds, setElapsedSeconds] = useState(0);

    const fetchQuota = useCallback(async () => {
        if (!user?.userId) return;
        try {
            const data = await apiRequest(`/api/v1/meal-analysis/quota/${user.userId}`);
            setQuota(data);
        } catch (error) {
            // Non bloquant : si le quota ne charge pas, le backend fera de toute facon
            // respecter la limite au moment de l'analyse.
        }
    }, [user?.userId]);

    // Le modele de vision tourne en local (Ollama) : verifier qu'il repond
    // AVANT de laisser l'utilisateur prendre une photo evite une longue
    // attente qui se termine par une erreur si le service est eteint ou si
    // le modele n'est pas installe.
    const fetchServiceStatus = useCallback(async () => {
        try {
            const data = await apiRequest('/api/v1/meal-analysis/health');
            setServiceStatus(data);
        } catch (error) {
            // Si /health lui-meme ne repond pas, le backend est probablement
            // injoignable (mauvaise IP/Wi-Fi) : meme traitement qu'un service
            // indisponible, l'utilisateur voit le meme bandeau d'avertissement.
            setServiceStatus({ available: false, model_installed: false, detail: null });
        }
    }, []);

    useEffect(() => {
        fetchQuota();
        fetchServiceStatus();
    }, [fetchQuota, fetchServiceStatus]);

    // Chrono affiche pendant l'analyse : un modele CPU peut prendre
    // 30 a 90s, un simple spinner sans indication de temps donne
    // l'impression que l'app est figee.
    useEffect(() => {
        if (!isAnalyzing) {
            setElapsedSeconds(0);
            return undefined;
        }
        const intervalId = setInterval(() => {
            setElapsedSeconds((current) => current + 1);
        }, 1000);
        return () => clearInterval(intervalId);
    }, [isAnalyzing]);

    const serviceUnavailable = serviceStatus && (!serviceStatus.available || !serviceStatus.model_installed);

    const reset = () => {
        setImageUri(null);
        setAnalysis(null);
    };

    const analyzeImage = async (uri) => {
        if (!user?.userId) {
            Alert.alert(t('meal_analysis.error_title'), t('meal_analysis.error_generic'));
            return;
        }

        if (quota && quota.remaining <= 0) {
            Alert.alert(t('meal_analysis.quota_exhausted_title'), t('meal_analysis.quota_exhausted_message', { limit: quota.limit }));
            return;
        }

        setImageUri(uri);
        setAnalysis(null);
        setIsAnalyzing(true);

        try {
            const { type } = guessFileMeta(uri);

            // FileSystem.uploadAsync fait un vrai upload multipart natif,
            // sans passer par Blob/FormData JS : evite les images
            // corrompues envoyees au modele et le warning de performance
            // du Blob de React Native.
            const uploadResult = await FileSystem.uploadAsync(
                `${API_BASE_URL}/api/v1/meal-analysis/analyze`,
                uri,
                {
                    httpMethod: 'POST',
                    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
                    fieldName: 'image',
                    mimeType: type,
                    parameters: {
                        language: language || 'fr',
                        user_id: user.userId,
                    },
                }
            );

            let body = null;
            try {
                body = JSON.parse(uploadResult.body);
            } catch (parseError) {
                body = null;
            }

            if (uploadResult.status === 429) {
                Alert.alert(t('meal_analysis.quota_exhausted_title'), typeof body?.detail === 'string' ? body.detail : t('meal_analysis.quota_exhausted_message', { limit: quota?.limit ?? '' }));
                reset();
                fetchQuota();
                return;
            }

            if (uploadResult.status < 200 || uploadResult.status >= 300) {
                const detail = typeof body?.detail === 'string'
                    ? body.detail
                    : `Erreur serveur (${uploadResult.status})`;
                throw new Error(detail);
            }

            setAnalysis(body.analysis);
            fetchQuota();
        } catch (error) {
            Alert.alert(t('meal_analysis.error_title'), error.message || t('meal_analysis.error_generic'));
            reset();
            // L'erreur peut venir d'Ollama qui vient de tomber : on rafraichit
            // le statut pour que le bandeau d'avertissement soit a jour au
            // prochain essai plutot que de laisser l'utilisateur retenter a l'aveugle.
            fetchServiceStatus();
        } finally {
            setIsAnalyzing(false);
        }
    };

    const takePhoto = async () => {
        if (serviceUnavailable) {
            Alert.alert(
                t('meal_analysis.service_unavailable_title'),
                serviceStatus?.detail || t('meal_analysis.service_unavailable_message'),
            );
            return;
        }

        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
            Alert.alert(t('meal_analysis.permission_denied'), t('meal_analysis.camera_permission_message'));
            return;
        }

        const result = await ImagePicker.launchCameraAsync({
            mediaTypes: ['images'],
            quality: 0.7,
            allowsEditing: false,
        });

        if (!result.canceled && result.assets?.length) {
            analyzeImage(result.assets[0].uri);
        }
    };

    const pickFromGallery = async () => {
        if (serviceUnavailable) {
            Alert.alert(
                t('meal_analysis.service_unavailable_title'),
                serviceStatus?.detail || t('meal_analysis.service_unavailable_message'),
            );
            return;
        }

        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
            Alert.alert(t('meal_analysis.permission_denied'), t('meal_analysis.gallery_permission_message'));
            return;
        }

        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
            quality: 0.7,
            allowsEditing: false,
        });

        if (!result.canceled && result.assets?.length) {
            analyzeImage(result.assets[0].uri);
        }
    };

    const addToLog = async () => {
        if (!analysis) return;

        if (!user?.userId) {
            Alert.alert(t('meal_analysis.error_title'), t('meal_analysis.added_error'));
            return;
        }

        const items = analysis.foods
            .filter((food) => food.matched && food.matched_food_slug && food.calculated_grams)
            .map((food) => ({
                food_slug: food.matched_food_slug,
                quantity: food.calculated_grams,
                unit: 'g',
            }));

        if (items.length === 0) {
            Alert.alert(t('meal_analysis.error_title'), t('meal_analysis.no_matched_items'));
            return;
        }

        setIsAdding(true);
        try {
            await apiRequest(`/nutrition-tracking/meals/${user.userId}`, {
                method: 'POST',
                body: JSON.stringify({
                    meal_type: analysis.meal_type,
                    items,
                }),
            });
            requestNutritionRefresh();
            Alert.alert(t('meal_analysis.results_title'), t('meal_analysis.added_success'), [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (error) {
            Alert.alert(t('meal_analysis.error_title'), error.message || t('meal_analysis.added_error'));
        } finally {
            setIsAdding(false);
        }
    };

    const mealTypeLabel = (mealType) => {
        const key = `nutrition.${mealType}`;
        const translated = t(key);
        return translated === key ? mealType : translated;
    };

    const confidenceColor = (confidence) => {
        if (confidence >= 0.8) return colors.primary;
        if (confidence >= 0.5) return colors.orange;
        return colors.red;
    };

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            <View style={styles.header}>
                <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={styles.title}>{t('meal_analysis.title')}</Text>
                <View style={styles.iconButton} />
            </View>

            <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">

                {!imageUri && (
                    <View style={styles.captureBox}>
                        <MaterialCommunityIcons name="camera-outline" size={64} color={colors.primary} />
                        <Text style={styles.intro}>{t('meal_analysis.intro')}</Text>

                        {quota && (
                            <View style={[styles.quotaBadge, quota.remaining <= 0 && styles.quotaBadgeExhausted]}>
                                <Ionicons
                                    name={quota.remaining <= 0 ? 'alert-circle-outline' : 'flash-outline'}
                                    size={16}
                                    color={quota.remaining <= 0 ? colors.red : colors.primary}
                                />
                                <Text style={[styles.quotaText, quota.remaining <= 0 && styles.quotaTextExhausted]}>
                                    {quota.remaining <= 0
                                        ? t('meal_analysis.quota_exhausted_message', { limit: quota.limit })
                                        : t('meal_analysis.quota_remaining', { remaining: quota.remaining, limit: quota.limit })}
                                </Text>
                            </View>
                        )}

                        {serviceUnavailable && (
                            <View style={styles.serviceWarningBox}>
                                <Ionicons name="warning-outline" size={18} color={colors.orange} />
                                <Text style={styles.serviceWarningText}>
                                    {serviceStatus?.detail || t('meal_analysis.service_unavailable_message')}
                                </Text>
                                <TouchableOpacity onPress={fetchServiceStatus}>
                                    <Text style={styles.serviceWarningRetry}>{t('meal_analysis.service_retry')}</Text>
                                </TouchableOpacity>
                            </View>
                        )}

                        <TouchableOpacity
                            style={[styles.primaryButton, (quota?.remaining <= 0 || serviceUnavailable) && styles.buttonDisabled]}
                            onPress={takePhoto}
                            disabled={quota?.remaining <= 0 || !!serviceUnavailable}
                        >
                            <Ionicons name="camera" size={20} color={colors.white} />
                            <Text style={styles.primaryButtonText}>{t('meal_analysis.take_photo')}</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.secondaryButton, (quota?.remaining <= 0 || serviceUnavailable) && styles.buttonDisabled]}
                            onPress={pickFromGallery}
                            disabled={quota?.remaining <= 0 || !!serviceUnavailable}
                        >
                            <Ionicons name="images-outline" size={20} color={colors.primary} />
                            <Text style={styles.secondaryButtonText}>{t('meal_analysis.choose_gallery')}</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {imageUri && (
                    <Image source={{ uri: imageUri }} style={styles.preview} />
                )}

                {isAnalyzing && (
                    <View style={styles.analyzingBox}>
                        <ActivityIndicator color={colors.primary} size="large" />
                        <Text style={styles.analyzingText}>{t('meal_analysis.analyzing')}</Text>
                        <Text style={styles.analyzingChrono}>
                            {t('meal_analysis.analyzing_elapsed', { seconds: elapsedSeconds })}
                        </Text>
                        <Text style={styles.analyzingHint}>{t('meal_analysis.analyzing_patience')}</Text>
                    </View>
                )}

                {analysis && !isAnalyzing && (
                    <View style={styles.results}>

                        <View style={styles.mealTypeRow}>
                            <Text style={styles.sectionLabel}>{t('meal_analysis.meal_type')}</Text>
                            <View style={styles.mealTypeBadge}>
                                <Text style={styles.mealTypeBadgeText}>{mealTypeLabel(analysis.meal_type)}</Text>
                            </View>
                        </View>

                        <Text style={styles.sectionLabel}>{t('meal_analysis.detected_foods')}</Text>

                        {analysis.foods.map((food, index) => (
                            <View key={`${food.detected_name}-${index}`} style={styles.foodCard}>
                                <View style={styles.foodCardHeader}>
                                    <Text style={styles.foodName} numberOfLines={1}>
                                        {food.matched_food_name || food.detected_name}
                                    </Text>
                                    <View style={[styles.confidenceDot, { backgroundColor: confidenceColor(food.confidence) }]} />
                                </View>

                                <Text style={styles.foodQuantity}>
                                    {food.calculated_grams
                                        ? t('meal_analysis.quantity_grams', { value: Math.round(food.calculated_grams) })
                                        : `${food.estimated_quantity} ${food.estimated_unit}`}
                                </Text>

                                {food.matched ? (
                                    <Text style={styles.foodMacros}>
                                        {Math.round(food.calories_kcal || 0)} kcal · {Math.round(food.protein_g || 0)}g P · {Math.round(food.carbs_g || 0)}g G · {Math.round(food.fat_g || 0)}g L
                                    </Text>
                                ) : (
                                    <Text style={styles.foodWarning}>{t('meal_analysis.not_found_in_db')}</Text>
                                )}

                                {food.needs_correction ? (
                                    <Text style={styles.foodWarning}>{t('meal_analysis.needs_correction')}</Text>
                                ) : food.needs_confirmation ? (
                                    <Text style={styles.foodNotice}>{t('meal_analysis.needs_confirmation')}</Text>
                                ) : null}
                            </View>
                        ))}

                        <View style={styles.totalsCard}>
                            <Text style={styles.sectionLabel}>{t('meal_analysis.totals')}</Text>
                            <Text style={styles.totalsMacros}>
                                {Math.round(analysis.totals.calories)} kcal · {Math.round(analysis.totals.protein_g)}g P · {Math.round(analysis.totals.carbs_g)}g G · {Math.round(analysis.totals.fat_g)}g L
                            </Text>
                        </View>

                        <TouchableOpacity style={styles.primaryButton} onPress={addToLog} disabled={isAdding}>
                            {isAdding ? (
                                <ActivityIndicator color={colors.white} />
                            ) : (
                                <Text style={styles.primaryButtonText}>{t('meal_analysis.add_to_log')}</Text>
                            )}
                        </TouchableOpacity>

                        <TouchableOpacity style={styles.secondaryButton} onPress={reset}>
                            <Ionicons name="camera-reverse-outline" size={20} color={colors.primary} />
                            <Text style={styles.secondaryButtonText}>{t('meal_analysis.retake')}</Text>
                        </TouchableOpacity>
                    </View>
                )}

            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: { flex: 1, backgroundColor: colors.background },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 10 },
    iconButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
    title: { fontSize: 20, fontWeight: '800', color: colors.text },
    content: { padding: 20, paddingBottom: 40 },

    captureBox: { alignItems: 'center', paddingVertical: 30, gap: 14 },
    intro: { color: colors.secondaryText, fontSize: 15, textAlign: 'center', lineHeight: 21, marginBottom: 10, paddingHorizontal: 10 },

    quotaBadge: {
        flexDirection: 'row', alignItems: 'center', gap: 6,
        backgroundColor: colors.primaryLight, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, marginBottom: 4,
    },
    quotaBadgeExhausted: { backgroundColor: '#FDECEC' },
    quotaText: { color: colors.primary, fontSize: 13, fontWeight: '600' },
    quotaTextExhausted: { color: colors.red },

    buttonDisabled: { opacity: 0.4 },

    primaryButton: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
        minHeight: 52, width: '100%', backgroundColor: colors.primary, borderRadius: 14, marginTop: 6,
    },
    primaryButtonText: { color: colors.white, fontSize: 16, fontWeight: '800' },

    secondaryButton: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
        minHeight: 52, width: '100%', backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderRadius: 14, marginTop: 6,
    },
    secondaryButtonText: { color: colors.primary, fontSize: 16, fontWeight: '700' },

    preview: { width: '100%', height: 260, borderRadius: 20, marginBottom: 16, backgroundColor: colors.white },

    analyzingBox: { alignItems: 'center', paddingVertical: 30, gap: 12 },
    analyzingText: { color: colors.secondaryText, fontSize: 15 },
    analyzingChrono: { color: colors.text, fontSize: 17, fontWeight: '700', fontVariant: ['tabular-nums'] },
    analyzingHint: {
        color: colors.secondaryText,
        fontSize: 13,
        textAlign: 'center',
        paddingHorizontal: 24,
        lineHeight: 18,
    },

    serviceWarningBox: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        backgroundColor: colors.orangeLight ?? '#FFF4E5',
        borderColor: colors.orange,
        borderWidth: 1,
        borderRadius: 10,
        padding: 10,
        marginBottom: 14,
    },
    serviceWarningText: { flex: 1, color: colors.text, fontSize: 13, lineHeight: 17 },
    serviceWarningRetry: { color: colors.primary, fontSize: 13, fontWeight: '700' },

    results: { gap: 4 },
    sectionLabel: { color: colors.text, fontSize: 15, fontWeight: '700', marginTop: 16, marginBottom: 8 },
    mealTypeRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    mealTypeBadge: { backgroundColor: colors.primaryLight, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 6, marginTop: 12 },
    mealTypeBadgeText: { color: colors.primary, fontWeight: '700', fontSize: 13, textTransform: 'capitalize' },

    foodCard: { backgroundColor: colors.white, borderRadius: 14, borderWidth: 1, borderColor: colors.border, padding: 14, marginBottom: 10 },
    foodCardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    foodName: { color: colors.text, fontSize: 15, fontWeight: '800', flex: 1, marginRight: 8, textTransform: 'capitalize' },
    confidenceDot: { width: 10, height: 10, borderRadius: 5 },
    foodQuantity: { color: colors.secondaryText, fontSize: 13, marginTop: 4 },
    foodMacros: { color: colors.text, fontSize: 13, marginTop: 6, fontWeight: '600' },
    foodWarning: { color: colors.red, fontSize: 12, marginTop: 6, fontWeight: '600' },
    foodNotice: { color: colors.orange, fontSize: 12, marginTop: 6, fontWeight: '600' },

    totalsCard: { backgroundColor: colors.primaryLight, borderRadius: 14, padding: 14, marginTop: 4, marginBottom: 6 },
    totalsMacros: { color: colors.text, fontSize: 15, fontWeight: '800' },
});
