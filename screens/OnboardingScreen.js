import React, { useState } from 'react';

import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    Alert,
} from 'react-native';

import { SafeAreaView } from 'react-native-safe-area-context';
import { useI18n } from '../i18n/I18nContext';
import { API_BASE_URL } from '../constants/api';

const COLORS = {
    primary: '#22C55E',
    background: '#F8FAFC',
    text: '#262135',
    white: '#FFFFFF',
    border: '#D9D9D9',
    gray: '#9B9B9B',
    lightGray: '#D1D1D1',
    shadow: 'rgba(38, 33, 53, 0.08)',
    scr:'#cddefb',
};

const TOTAL_STEPS = 9;
const SEDENTARY_STEP_COUNT = 8;

const LANGUAGES = [
    { id: 'fr', label: 'Français', emoji: '🇫🇷' },
    { id: 'en', label: 'English', emoji: '🇬🇧' },
    { id: 'ar', label: 'العربية', emoji: '🇩🇿' },
    { id: 'es', label: 'Español', emoji: '🇪🇸' },
];

const GENDERS = [
    { id: 'male', key: 'gender_man', emoji: '👨' },
    { id: 'female', key: 'gender_woman', emoji: '👩' },
];

const SPORTS = [
    { id: 'football', key: 'sport_football', emoji: '⚽' },
    { id: 'weight', key: 'sport_weight', emoji: '🏋️' },
    { id: 'running', key: 'sport_running', emoji: '🏃' },
    { id: 'cycling', key: 'sport_cycling', emoji: '🚴' },
    { id: 'combat', key: 'sport_combat', emoji: '🥊' },
    { id: 'swimming', key: 'sport_swimming', emoji: '🏊' },
    { id: 'other', key: 'sport_other', emoji: '➕' },
];

const GOALS = [
    { id: 'eat-healthier', key: 'goal_eat_healthier' },
    { id: 'build-muscle', key: 'goal_build_muscle' },
    { id: 'lose-fat', key: 'goal_lose_fat' },
    { id: 'maintain-weight', key: 'goal_maintain_weight' },
    { id: 'improve-performance', key: 'goal_improve_performance' },
    { id: 'healthy-lifestyle', key: 'goal_healthy_lifestyle' },
];

const ACTIVITIES = [
    { id: 'sedentary', key: 'activity_sedentary', emoji: '🛋️' },
    { id: 'light', key: 'activity_light', emoji: '🚶' },
    { id: 'active', key: 'activity_active', emoji: '🏃' },
    { id: 'very-active', key: 'activity_very_active', emoji: '🔥' },
    { id: 'athlete', key: 'activity_athlete', emoji: '🏆' },
];

export default function OnboardingScreen({ onFinish }) {
    const { t, setLanguage, isRTL } = useI18n();
    const [step, setStep] = useState(0);
    const [focusedField, setFocusedField] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [data, setData] = useState({
        language: null,
        gender: null,
        name: '',
        weight: 70,
        weightUnit: 'kg',
        height: 170,
        heightUnit: 'cm',
        age: 25,
        activity: null,
        sport: null,
        goals: [],
    });

    const updateData = (values) => {
        setData((prev) => ({
            ...prev,
            ...values,
        }));
    };

    const nextStep = async () => {
        // Une personne sédentaire n'a pas besoin de renseigner un sport.
        // On passe directement de l'activité aux objectifs.
        if (step === 6 && data.activity === 'sedentary') {
            setStep(8);
            return;
        }

        if (step < TOTAL_STEPS - 1) {
            setStep((current) => current + 1);
            return;
        }

        // Dernier step : on envoie tout le questionnaire au backend
        // (POST /onboarding) avant de laisser l'utilisateur continuer.
        setIsSubmitting(true);

        // Sans timeout explicite, fetch() peut rester en attente tres
        // longtemps (reseau injoignable, Neon qui se reveille apres une
        // mise en veille...) et le bouton reste bloque sur "..." sans
        // jamais afficher d'erreur. On coupe apres 15s.
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);

        try {
            const response = await fetch(`${API_BASE_URL}/onboarding`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                signal: controller.signal,
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => null);

                // FastAPI (validation Pydantic) renvoie detail comme un
                // TABLEAU d'objets -> [object Object] si on l'affiche tel quel.
                let detail = errorBody?.detail;
                if (detail && typeof detail !== 'string') {
                    detail = detail
                        .map(
                            (e) =>
                                `${(e.loc || []).join('.')} : ${e.msg}`
                        )
                        .join(' | ');
                }

                throw new Error(
                    detail || `Erreur serveur (${response.status})`
                );
            }

            const created = await response.json();

            if (onFinish) {
                onFinish({ ...data, userId: created.user_id });
            }
        } catch (error) {
            const isTimeout = error.name === 'AbortError';

            // Un objet leak mal gere finirait affiche "[object Object]" :
            // on force une representation lisible en dernier recours.
            const rawMessage =
                typeof error.message === 'string'
                    ? error.message
                    : JSON.stringify(error);

            Alert.alert(
                t('onboarding.error_title') || 'Erreur',
                isTimeout
                    ? t('onboarding.error_timeout')
                    : rawMessage ||
                      t('onboarding.error_generic')
            );

            // Log console pour le debug sans polluer l'UI.
            console.log('[onboarding] erreur:', error);
        } finally {
            clearTimeout(timeoutId);
            setIsSubmitting(false);
        }
    };

    const previousStep = () => {
        if (step === 8 && data.activity === 'sedentary') {
            setStep(6);
            return;
        }
        if (step > 0) {
            setStep((current) => current - 1);
        }
    };

    const toggleGoal = (goalId) => {
        setData((prev) => {
            const alreadySelected = prev.goals.includes(goalId);

            if (alreadySelected) {
                return {
                    ...prev,
                    goals: prev.goals.filter((item) => item !== goalId),
                };
            }

            return {
                ...prev,
                goals: [...prev.goals, goalId],
            };
        });
    };

    const renderOption = (item, selected, onPress) => {
        return (
            <TouchableOpacity
                key={item.id}
                style={[
                    styles.option,
                    isRTL && styles.optionRTL,
                    selected && styles.optionSelected,
                ]}
                onPress={onPress}
                activeOpacity={0.8}
            >
                <Text style={styles.optionEmoji}>{item.emoji}</Text>

                <Text style={styles.optionText} numberOfLines={2}>
                    {item.label || t(`onboarding.${item.key}`)}
                </Text>

                {selected && (
                    <View style={styles.check}>
                        <Text style={styles.checkText}>✓</Text>
                    </View>
                )}
            </TouchableOpacity>
        );
    };

    const renderStep = () => {
        // STEP 1 — LANGUAGE
        if (step === 0) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.choose_language')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_language')}
                    </Text>

                    <View style={styles.optionsWrapper}>
                        {LANGUAGES.map((language) =>
                            renderOption(
                                language,
                                data.language === language.id,
                                () => {
                                    updateData({ language: language.id });
                                    // La langue s'applique immediatement, RTL inclus,
                                    // pour que le reste de l'onboarding en beneficie.
                                    setLanguage(language.id);
                                }
                            )
                        )}
                    </View>
                </ScrollView>
            );
        }

        // STEP 2 — GENDER
        if (step === 1) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.choose_gender')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_gender')}
                    </Text>

                    <View style={styles.genderContainer}>
                        {GENDERS.map((gender) =>
                            renderOption(
                                gender,
                                data.gender === gender.id,
                                () => updateData({ gender: gender.id })
                            )
                        )}
                    </View>
                </ScrollView>
            );
        }

        // STEP 3 — NAME
        if (step === 2) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.name_title')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_name')}
                    </Text>

                    <TextInput
                        style={[
                            styles.input,
                            focusedField === 'name' && styles.inputFocused,
                        ]}
                        value={data.name}
                        onChangeText={(text) => updateData({ name: text })}
                        onFocus={() => setFocusedField('name')}
                        onBlur={() => setFocusedField(null)}
                        placeholder={t('onboarding.name_placeholder')}
                        placeholderTextColor={COLORS.gray}
                        autoCapitalize="words"
                        returnKeyType="done"
                    />
                </ScrollView>
            );
        }

        // STEP 4 — WEIGHT
        if (step === 3) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.weight')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_weight')}
                    </Text>

                    <View style={styles.valueCard}>
                        <TouchableOpacity
                            style={styles.controlTouchable}
                            onPress={() =>
                                updateData({
                                    weight: Math.max(1, data.weight - 1),
                                })
                            }
                            activeOpacity={0.7}
                            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                        >
                            <Text style={styles.controlButton}>−</Text>
                        </TouchableOpacity>

                        <View style={styles.valueContainer}>
                            <Text style={styles.bigValue}>
                                {data.weight}
                            </Text>

                            <Text style={styles.unit}>
                                {data.weightUnit}
                            </Text>
                        </View>

                        <TouchableOpacity
                            style={styles.controlTouchable}
                            onPress={() =>
                                updateData({
                                    weight: data.weight + 1,
                                })
                            }
                            activeOpacity={0.7}
                            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                        >
                            <Text style={styles.controlButton}>+</Text>
                        </TouchableOpacity>
                    </View>

                    <View style={styles.unitContainer}>
                        <TouchableOpacity
                            style={[
                                styles.unitButton,
                                data.weightUnit === 'kg' &&
                                styles.unitButtonSelected,
                            ]}
                            onPress={() =>
                                updateData({ weightUnit: 'kg' })
                            }
                            activeOpacity={0.85}
                        >
                            <Text
                                style={[
                                    styles.unitText,
                                    data.weightUnit === 'kg' &&
                                    styles.unitTextSelected,
                                ]}
                            >
                                kg
                            </Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[
                                styles.unitButton,
                                data.weightUnit === 'lb' &&
                                styles.unitButtonSelected,
                            ]}
                            onPress={() =>
                                updateData({ weightUnit: 'lb' })
                            }
                            activeOpacity={0.85}
                        >
                            <Text
                                style={[
                                    styles.unitText,
                                    data.weightUnit === 'lb' &&
                                    styles.unitTextSelected,
                                ]}
                            >
                                lb
                            </Text>
                        </TouchableOpacity>
                    </View>
                </ScrollView>
            );
        }

        // STEP 5 — HEIGHT
        if (step === 4) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.height')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_height')}
                    </Text>

                    <View style={styles.valueCard}>
                        <TouchableOpacity
                            style={styles.controlTouchable}
                            onPress={() =>
                                updateData({
                                    height: Math.max(1, data.height - 1),
                                })
                            }
                            activeOpacity={0.7}
                            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                        >
                            <Text style={styles.controlButton}>−</Text>
                        </TouchableOpacity>

                        <View style={styles.valueContainer}>
                            <Text style={styles.bigValue}>
                                {data.height}
                            </Text>

                            <Text style={styles.unit}>
                                {data.heightUnit}
                            </Text>
                        </View>

                        <TouchableOpacity
                            style={styles.controlTouchable}
                            onPress={() =>
                                updateData({
                                    height: data.height + 1,
                                })
                            }
                            activeOpacity={0.7}
                            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                        >
                            <Text style={styles.controlButton}>+</Text>
                        </TouchableOpacity>
                    </View>

                    <View style={styles.unitContainer}>
                        <TouchableOpacity
                            style={[
                                styles.unitButton,
                                data.heightUnit === 'cm' &&
                                styles.unitButtonSelected,
                            ]}
                            onPress={() =>
                                updateData({ heightUnit: 'cm' })
                            }
                            activeOpacity={0.85}
                        >
                            <Text
                                style={[
                                    styles.unitText,
                                    data.heightUnit === 'cm' &&
                                    styles.unitTextSelected,
                                ]}
                            >
                                cm
                            </Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[
                                styles.unitButton,
                                data.heightUnit === 'in' &&
                                styles.unitButtonSelected,
                            ]}
                            onPress={() =>
                                updateData({ heightUnit: 'in' })
                            }
                            activeOpacity={0.85}
                        >
                            <Text
                                style={[
                                    styles.unitText,
                                    data.heightUnit === 'in' &&
                                    styles.unitTextSelected,
                                ]}
                            >
                                inches
                            </Text>
                        </TouchableOpacity>
                    </View>
                </ScrollView>
            );
        }

        // STEP 6 — AGE
        if (step === 5) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.age')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_age')}
                    </Text>

                    <TextInput
                        style={[
                            styles.ageInput,
                            focusedField === 'age' && styles.inputFocused,
                        ]}
                        value={String(data.age)}
                        onChangeText={(text) => {
                            const numericValue = text.replace(
                                /[^0-9]/g,
                                ''
                            );

                            updateData({
                                age:
                                    numericValue === ''
                                        ? ''
                                        : Number(numericValue),
                            });
                        }}
                        onFocus={() => setFocusedField('age')}
                        onBlur={() => setFocusedField(null)}
                        keyboardType="numeric"
                        maxLength={3}
                        returnKeyType="done"
                    />

                    <Text style={styles.ageUnit}>
                        {t('onboarding.years_old')}
                    </Text>
                </ScrollView>
            );
        }

        // STEP 7 — ACTIVITY
        if (step === 6) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.activity_level')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_activity')}
                    </Text>

                    <View style={styles.optionsWrapper}>
                        {ACTIVITIES.map((activity) =>
                            renderOption(
                                activity,
                                data.activity === activity.id,
                                () =>
                                    updateData({
                                        activity: activity.id,
                                        ...(activity.id === 'sedentary' ? { sport: null } : {}),
                                    })
                            )
                        )}
                    </View>
                </ScrollView>
            );
        }

        // STEP 8 — SPORT
        if (step === 7) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.sport')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_sport')}
                    </Text>

                    <View style={styles.optionsWrapper}>
                        {SPORTS.map((sport) =>
                            renderOption(
                                sport,
                                data.sport === sport.id,
                                () =>
                                    updateData({
                                        sport: sport.id,
                                    })
                            )
                        )}
                    </View>
                </ScrollView>
            );
        }

        // STEP 9 — GOALS
        if (step === 8) {
            return (
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    keyboardShouldPersistTaps="handled"
                    contentContainerStyle={styles.scrollContent}
                >
                    <Text style={styles.title}>
                        {t('onboarding.goal')}
                    </Text>

                    <Text style={styles.subtitle}>
                        {t('onboarding.subtitle_goal')}
                    </Text>

                    {GOALS.map((goal) => {
                        const selected =
                            data.goals.includes(goal.id);

                        return (
                            <TouchableOpacity
                                key={goal.id}
                                style={[
                                    styles.goalCard,
                                    isRTL && styles.optionRTL,
                                    selected &&
                                    styles.goalCardSelected,
                                ]}
                                onPress={() => toggleGoal(goal.id)}
                                activeOpacity={0.8}
                            >
                                <Text style={styles.goalText} numberOfLines={2}>
                                    {t(`onboarding.${goal.key}`)}
                                </Text>

                                {selected && (
                                    <View style={styles.check}>
                                        <Text style={styles.checkText}>
                                            ✓
                                        </Text>
                                    </View>
                                )}
                            </TouchableOpacity>
                        );
                    })}
                </ScrollView>
            );
        }

        return null;
    };

    const displayedStep = data.activity === 'sedentary' && step === 8 ? SEDENTARY_STEP_COUNT : step + 1;
    const displayedTotalSteps = data.activity === 'sedentary' ? SEDENTARY_STEP_COUNT : TOTAL_STEPS;
    const progressPercent = (displayedStep / displayedTotalSteps) * 100;

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
            <KeyboardAvoidingView
                style={styles.container}
                behavior={
                    Platform.OS === 'ios'
                        ? 'padding'
                        : undefined
                }
                keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}
            >
                {/* PROGRESS */}
                <View style={styles.progressContainer}>
                    <View style={styles.progressTrack}>
                        <View
                            style={[
                                styles.progressFill,
                                { width: `${progressPercent}%` },
                            ]}
                        />
                    </View>

                    <Text style={styles.progressLabel}>
                        {displayedStep}/{displayedTotalSteps}
                    </Text>
                </View>

                {/* MAIN CONTENT */}
                <View style={[styles.main, isRTL && styles.mainRTL]}>
                    {renderStep()}
                </View>

                {/* BOTTOM NAVIGATION */}
                <View style={[styles.bottom, isRTL && styles.bottomRTL]}>
                    <TouchableOpacity
                        style={[
                            styles.backButton,
                            step === 0 && styles.backButtonDisabled,
                        ]}
                        onPress={previousStep}
                        disabled={step === 0}
                        activeOpacity={0.8}
                    >
                        <Text
                            style={[
                                styles.backArrow,
                                step === 0 && { opacity: 0.3 },
                            ]}
                        >
                            ←
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.nextButton}
                        onPress={nextStep}
                        activeOpacity={0.85}
                        disabled={isSubmitting}
                    >
                        <Text style={styles.nextText}>
                            {isSubmitting
                                ? '...'
                                : step === TOTAL_STEPS - 1
                                ? t('onboarding.start_now')
                                : t('common.next')}
                        </Text>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: COLORS.background,
    },

    container: {
        flex: 1,
        backgroundColor: COLORS.background,
        paddingHorizontal: 20,
    },

    progressContainer: {
        height: 45,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },

    progressTrack: {
        flex: 1,
        height: 6,
        borderRadius: 10,
        backgroundColor: COLORS.lightGray,
        overflow: 'hidden',
    },

    progressFill: {
        height: '100%',
        borderRadius: 10,
        backgroundColor: COLORS.primary,
    },

    progressLabel: {
        fontSize: 13,
        fontWeight: '600',
        color: COLORS.gray,
        width: 34,
        textAlign: 'right',
    },

    main: {
        flex: 1,
        minHeight: 0,
    },

    scrollContent: {
        flexGrow: 1,
        paddingTop: 28,
        paddingBottom: 24,
    },

    title: {
        fontSize: 24,
        lineHeight: 32,
        fontWeight: '700',
        color: COLORS.text,
        marginBottom: 8,
    },

    subtitle: {
        fontSize: 15,
        lineHeight: 21,
        color: COLORS.gray,
        marginBottom: 28,
    },

    input: {
        height: 60,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        borderRadius: 18,
        paddingHorizontal: 20,
        fontSize: 17,
        color: COLORS.text,
        backgroundColor: COLORS.white,
    },

    inputFocused: {
        borderColor: COLORS.primary,
    },

    optionsWrapper: {
        gap: 12,
    },

    genderContainer: {
        gap: 12,
    },

    option: {
        minHeight: 64,
        borderRadius: 18,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        backgroundColor: COLORS.white,
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 14,
        paddingHorizontal: 16,
        shadowColor: COLORS.shadow,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 1,
        shadowRadius: 6,
        elevation: 1,
    },

    optionSelected: {
        borderColor: COLORS.primary,
        borderWidth: 2,
        backgroundColor: COLORS.white,
    },

    optionEmoji: {
        fontSize: 24,
        width: 40,
        textAlign: 'center',
    },

    optionText: {
        flex: 1,
        fontSize: 16,
        color: COLORS.text,
        paddingRight: 8,
    },

    optionRTL: {
        flexDirection: 'row-reverse',
    },

    bottomRTL: {
        flexDirection: 'row-reverse',
    },

    check: {
        width: 26,
        height: 26,
        borderRadius: 13,
        backgroundColor: COLORS.primary,
        alignItems: 'center',
        justifyContent: 'center',
    },

    checkText: {
        color: COLORS.white,
        fontSize: 14,
        fontWeight: '700',
    },

    valueCard: {
        marginTop: 20,
        height: 170,
        borderRadius: 26,
        backgroundColor: COLORS.scr,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-around',
        shadowColor: COLORS.shadow,
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 1,
        shadowRadius: 8,
        elevation: 1,

    },

    controlTouchable: {
        width: 60,
        height: 80,
        alignItems: 'center',
        justifyContent: 'center',
    },

    valueContainer: {
        alignItems: 'center',
    },

    bigValue: {
        fontSize: 48,
        fontWeight: '700',
        color: COLORS.text,
    },

    unit: {
        fontSize: 16,
        color: COLORS.gray,
        marginTop: 2,
    },

    controlButton: {
        fontSize: 32,
        color: COLORS.primary,
        fontWeight: '600',
    },

    unitContainer: {
        flexDirection: 'row',
        justifyContent: 'center',
        marginTop: 20,
        gap: 10,
    },

    unitButton: {
        paddingVertical: 12,
        paddingHorizontal: 26,
        borderRadius: 14,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        backgroundColor: COLORS.white,
    },

    unitButtonSelected: {
        backgroundColor: COLORS.primary,
        borderColor: COLORS.primary,
    },

    unitText: {
        fontSize: 15,
        fontWeight: '600',
        color: COLORS.text,
    },

    unitTextSelected: {
        color: COLORS.white,
    },

    ageInput: {
        alignSelf: 'center',
        width: 170,
        height: 96,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        borderRadius: 24,
        textAlign: 'center',
        fontSize: 42,
        fontWeight: '600',
        color: COLORS.text,
        backgroundColor: COLORS.white,
        marginTop: 12,
    },

    ageUnit: {
        textAlign: 'center',
        marginTop: 14,
        color: COLORS.gray,
        fontSize: 15,
        fontWeight: '500',
    },

    goalCard: {
        minHeight: 64,
        borderRadius: 18,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        backgroundColor: COLORS.white,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 14,
        paddingHorizontal: 16,
        marginBottom: 12,
        shadowColor: COLORS.shadow,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 1,
        shadowRadius: 6,
        elevation: 1,
    },

    goalCardSelected: {
        borderColor: COLORS.primary,
        borderWidth: 2,
    },

    goalText: {
        flex: 1,
        fontSize: 16,
        color: COLORS.text,
        paddingRight: 12,
    },

    bottom: {
        flexDirection: 'row',
        gap: 16,
        paddingTop: 12,
        paddingBottom: 8,
    },

    backButton: {
        width: 72,
        height: 72,
        borderRadius: 22,
        borderWidth: 1.5,
        borderColor: COLORS.border,
        backgroundColor: COLORS.white,
        alignItems: 'center',
        justifyContent: 'center',
    },

    backButtonDisabled: {
        backgroundColor: COLORS.background,
    },

    backArrow: {
        fontSize: 28,
        color: COLORS.text,
    },

    nextButton: {
        flex: 1,
        height: 72,
        borderRadius: 22,
        backgroundColor: COLORS.primary,
        alignItems: 'center',
        justifyContent: 'center',
        shadowColor: COLORS.primary,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.25,
        shadowRadius: 10,
        elevation: 3,
    },

    nextText: {
        fontSize: 20,
        fontWeight: '700',
        color: COLORS.white,
    },
});