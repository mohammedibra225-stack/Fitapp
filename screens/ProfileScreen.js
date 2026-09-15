
import React, { useCallback, useEffect, useState } from 'react';

import {
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    TextInput,
    StyleSheet,
    Alert,
    ActivityIndicator,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

// --- Options affichees (cles i18n dans profile.*) ---

const WEIGHT_UNITS = ['kg', 'lb'];
const HEIGHT_UNITS = ['cm', 'in'];
const DISTANCE_UNITS = ['km', 'mi'];

// Régimes alimentaires – le halal est mis en premier pour les utilisateurs musulmans
const DIETS = ['halal', 'none', 'vegetarian', 'vegan', 'pescatarian', 'keto'];

const COMMON_ALLERGENS = [
    'peanuts',
    'tree_nuts',
    'milk',
    'eggs',
    'gluten',
    'soy',
    'fish',
    'shellfish',
    'lactose',
];

// Niveaux sportifs (SportLevel cote backend, app/models/enums.py) et
// frequences d'entrainement proposees (UserSport.frequency_per_week).
const SPORT_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert', 'professional'];
const FREQUENCY_OPTIONS = [1, 2, 3, 4, 5, 6, 7];

// --- Infos onboarding (memes ids que OnboardingScreen.js et
// app/routes/onboarding.py, cote backend, pour rester coherent) ---

const GENDERS = [
    { id: 'male', key: 'gender_man' },
    { id: 'female', key: 'gender_woman' },
];

const ACTIVITIES = [
    { id: 'sedentary', key: 'activity_sedentary' },
    { id: 'light', key: 'activity_light' },
    { id: 'active', key: 'activity_active' },
    { id: 'very-active', key: 'activity_very_active' },
    { id: 'athlete', key: 'activity_athlete' },
];

const GOALS = [
    { id: 'eat-healthier', key: 'goal_eat_healthier' },
    { id: 'build-muscle', key: 'goal_build_muscle' },
    { id: 'lose-fat', key: 'goal_lose_fat' },
    { id: 'maintain-weight', key: 'goal_maintain_weight' },
    { id: 'improve-performance', key: 'goal_improve_performance' },
    { id: 'healthy-lifestyle', key: 'goal_healthy_lifestyle' },
];

export default function ProfileScreen() {
    const router = useRouter();
    const { t, isRTL } = useI18n();
    const { user, updatePreferences, updateIdentity } = useUser();

    const prefs = user?.preferences ?? {};

    // --- Brouillon des infos onboarding (identite + Profile), rempli
    // depuis GET /profile/{userId} et envoye en une fois via PATCH au
    // clic sur "Enregistrer" (pas de sauvegarde silencieuse a chaque tap). ---
    const [draft, setDraft] = useState(null);
    const [isLoadingProfile, setIsLoadingProfile] = useState(true);
    const [isSavingProfile, setIsSavingProfile] = useState(false);

    const updateDraft = (values) => setDraft((current) => ({ ...current, ...values }));

    useEffect(() => {
        let isMounted = true;

        async function loadProfile() {
            if (!user?.userId) {
                if (isMounted) setIsLoadingProfile(false);
                return;
            }
            try {
                const data = await apiRequest(`/profile/${user.userId}`);
                if (!isMounted) return;
                setDraft({
                    name: data.name || '',
                    gender: data.gender || null,
                    weight: data.weight != null ? String(data.weight) : '',
                    height: data.height != null ? String(data.height) : '',
                    age: data.age != null ? String(data.age) : '',
                    activity: data.activity || null,
                    goal: data.goals?.[0] || null,
                    diet: data.diet || 'none',
                    allergies: data.allergies || [],
                    budgetPerWeek: data.budget_per_week != null ? String(data.budget_per_week) : '',
                });
            } catch (error) {
                // Silencieux : l'utilisateur peut quand meme naviguer, il verra
                // juste un formulaire vide qu'il pourra remplir puis enregistrer.
                if (isMounted) setDraft({
                    name: user.username || '',
                    gender: null,
                    weight: '',
                    height: '',
                    age: '',
                    activity: null,
                    goal: null,
                    diet: prefs.diet || 'none',
                    allergies: prefs.allergies || [],
                    budgetPerWeek: prefs.budgetPerWeek || '',
                });
            } finally {
                if (isMounted) setIsLoadingProfile(false);
            }
        }

        loadProfile();
        return () => { isMounted = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.userId]);

    const saveProfile = useCallback(async () => {
        if (!user?.userId || !draft || isSavingProfile) return;

        const weightNumber = parseFloat(String(draft.weight).replace(',', '.'));
        const heightNumber = parseFloat(String(draft.height).replace(',', '.'));
        const ageNumber = parseInt(draft.age, 10);
        const budgetNumber = parseFloat(String(draft.budgetPerWeek).replace(',', '.'));

        setIsSavingProfile(true);
        try {
            const updated = await apiRequest(`/profile/${user.userId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    name: draft.name?.trim() || undefined,
                    gender: draft.gender || undefined,
                    weight: Number.isFinite(weightNumber) ? weightNumber : undefined,
                    weightUnit: prefs.weightUnit ?? 'kg',
                    height: Number.isFinite(heightNumber) ? heightNumber : undefined,
                    heightUnit: prefs.heightUnit ?? 'cm',
                    age: Number.isFinite(ageNumber) ? ageNumber : undefined,
                    activity: draft.activity || undefined,
                    goals: draft.goal ? [draft.goal] : undefined,
                    diet: draft.diet || undefined,
                    allergies: draft.allergies || [],
                    budget_per_week: Number.isFinite(budgetNumber) ? budgetNumber : undefined,
                }),
            });

            updateIdentity({
                username: updated.name,
                gender: updated.gender,
                weight: updated.weight,
                height: updated.height,
                age: updated.age,
                activity: updated.activity,
                goals: updated.goals,
            });
            updatePreferences({
                diet: updated.diet,
                allergies: updated.allergies,
                budgetPerWeek: updated.budget_per_week != null ? String(updated.budget_per_week) : '',
            });

            Alert.alert(t('common.save'), t('profile.save_success'));
        } catch (error) {
            Alert.alert(t('profile.save_error'), error.message);
        } finally {
            setIsSavingProfile(false);
        }
    }, [user?.userId, draft, isSavingProfile, prefs.weightUnit, prefs.heightUnit, updateIdentity, updatePreferences, t]);

    // --- Profil sportif (niveau + frequence), backend uniquement : le
    // sport pratique lui-meme (user.sport) reste choisi a l'onboarding,
    // seuls level/frequency_per_week se modifient ici (POST /sports/profile/{user_id}).
    // "other" est exclu : routes/onboarding.py ne cree jamais de UserSport
    // pour ce choix (Sport "other" n'existe pas en base), donc POST
    // /sports/profile echouerait avec 404 "Sport inconnu".
    const hasTrackedSport = Boolean(user?.sport) && user.sport !== 'other';
    const [sportLevel, setSportLevel] = useState(null);
    const [sportFrequency, setSportFrequency] = useState(null);
    const [isLoadingSport, setIsLoadingSport] = useState(true);
    const [isSavingSport, setIsSavingSport] = useState(false);

    useEffect(() => {
        let isMounted = true;

        async function loadSportProfile() {
            if (!user?.userId || !hasTrackedSport) {
                if (isMounted) setIsLoadingSport(false);
                return;
            }
            try {
                const sports = await apiRequest(`/sports/profile/${user.userId}`);
                const primary = sports.find((s) => s.is_primary) || sports[0];
                if (isMounted && primary) {
                    setSportLevel(primary.level);
                    setSportFrequency(primary.frequency_per_week);
                }
            } catch (error) {
                // Silencieux : la section reste utilisable (l'utilisateur peut
                // quand meme choisir et enregistrer un niveau/une frequence).
            } finally {
                if (isMounted) setIsLoadingSport(false);
            }
        }

        loadSportProfile();
        return () => {
            isMounted = false;
        };
    }, [user?.userId, hasTrackedSport]);

    const saveSportProfile = useCallback(async () => {
        if (!user?.userId || !hasTrackedSport || isSavingSport) return;
        setIsSavingSport(true);
        try {
            await apiRequest(`/sports/profile/${user.userId}`, {
                method: 'POST',
                body: JSON.stringify({
                    sport_slug: user.sport,
                    level: sportLevel,
                    frequency_per_week: sportFrequency,
                    is_primary: true,
                }),
            });
            Alert.alert(t('profile.sport_save_success'));
        } catch (error) {
            Alert.alert(t('profile.sport_save_error'), error.message);
        } finally {
            setIsSavingSport(false);
        }
    }, [user?.userId, hasTrackedSport, user?.sport, sportLevel, sportFrequency, isSavingSport, t]);

    const toggleDraftAllergy = (key) => {
        const current = draft?.allergies ?? [];
        const next = current.includes(key)
            ? current.filter((item) => item !== key)
            : [...current, key];
        updateDraft({ allergies: next });
    };

    if (isLoadingProfile || !draft) {
        return (
            <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
                <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />
            </SafeAreaView>
        );
    }

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

                <Text style={styles.headerTitle}>{t('profile.title')}</Text>

                <View style={styles.backButton} />
            </View>

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.content}
                keyboardShouldPersistTaps="handled"
            >
                {/* IDENTITE */}
                <View style={styles.identityCard}>
                    <View style={styles.avatar}>
                        <Ionicons name="person" size={30} color={colors.white} />
                    </View>

                    <View style={styles.identityText}>
                        <Text style={styles.username}>
                            {user?.username || 'Fitapp'}
                        </Text>

                        <Text style={styles.identityMeta}>
                            {user?.age ? `${user.age} ans · ` : ''}
                            {user?.weight
                                ? `${user.weight} ${prefs.weightUnit ?? 'kg'}`
                                : ''}
                        </Text>
                    </View>
                </View>

                {/* INFOS PERSONNELLES (onboarding) */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('profile.personal_info')}
                </Text>

                <View style={styles.card}>
                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('onboarding.name_title')}
                        </Text>
                        <TextInput
                            style={[styles.textInput, isRTL && styles.textRTL]}
                            value={draft.name}
                            onChangeText={(value) => updateDraft({ name: value })}
                            placeholder={t('onboarding.name_placeholder')}
                            placeholderTextColor={colors.secondaryText}
                        />
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('onboarding.choose_gender')}
                        </Text>
                        <View style={styles.chipRow}>
                            {GENDERS.map((gender) => (
                                <Chip
                                    key={gender.id}
                                    label={t(`onboarding.${gender.key}`)}
                                    active={draft.gender === gender.id}
                                    onPress={() => updateDraft({ gender: gender.id })}
                                />
                            ))}
                        </View>
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('onboarding.age')}
                        </Text>
                        <TextInput
                            style={[styles.numberInput, isRTL && styles.textRTL]}
                            value={draft.age}
                            onChangeText={(value) => updateDraft({ age: value.replace(/[^0-9]/g, '') })}
                            keyboardType="numeric"
                            placeholder="—"
                            placeholderTextColor={colors.secondaryText}
                        />
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {`${t('onboarding.weight')} (${prefs.weightUnit ?? 'kg'})`}
                        </Text>
                        <TextInput
                            style={[styles.numberInput, isRTL && styles.textRTL]}
                            value={draft.weight}
                            onChangeText={(value) => updateDraft({ weight: value.replace(',', '.').replace(/[^0-9.]/g, '') })}
                            keyboardType="decimal-pad"
                            placeholder="—"
                            placeholderTextColor={colors.secondaryText}
                        />
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {`${t('onboarding.height')} (${prefs.heightUnit ?? 'cm'})`}
                        </Text>
                        <TextInput
                            style={[styles.numberInput, isRTL && styles.textRTL]}
                            value={draft.height}
                            onChangeText={(value) => updateDraft({ height: value.replace(',', '.').replace(/[^0-9.]/g, '') })}
                            keyboardType="decimal-pad"
                            placeholder="—"
                            placeholderTextColor={colors.secondaryText}
                        />
                    </View>
                </View>

                {/* NIVEAU D'ACTIVITE */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('onboarding.activity_level')}
                </Text>

                <View style={styles.card}>
                    <View style={styles.chipWrap}>
                        {ACTIVITIES.map((activity) => (
                            <Chip
                                key={activity.id}
                                label={t(`onboarding.${activity.key}`)}
                                active={draft.activity === activity.id}
                                onPress={() => updateDraft({ activity: activity.id })}
                                large
                            />
                        ))}
                    </View>
                </View>

                {/* OBJECTIF PRINCIPAL */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('onboarding.goal')}
                </Text>

                <View style={styles.card}>
                    <View style={styles.chipWrap}>
                        {GOALS.map((goal) => (
                            <Chip
                                key={goal.id}
                                label={t(`onboarding.${goal.key}`)}
                                active={draft.goal === goal.id}
                                onPress={() => updateDraft({ goal: goal.id })}
                                large
                            />
                        ))}
                    </View>
                </View>

                {/* SPORT (niveau + frequence, module Sport) -- masque pour un
                    utilisateur sans sport principal (sedentaire a l'onboarding) */}
                {hasTrackedSport && (
                    <>
                        <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                            {t('profile.sport')}
                        </Text>

                        <View style={styles.card}>
                            <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                                <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                                    {t('profile.sport_level')}
                                </Text>
                            </View>
                            <View style={styles.chipWrap}>
                                {SPORT_LEVELS.map((level) => (
                                    <Chip
                                        key={level}
                                        label={t(`profile.sport_level_${level}`)}
                                        active={sportLevel === level}
                                        onPress={() => setSportLevel(level)}
                                        large
                                    />
                                ))}
                            </View>

                            <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                                <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                                    {t('profile.sport_frequency')}
                                </Text>
                            </View>
                            <View style={styles.chipWrap}>
                                {FREQUENCY_OPTIONS.map((freq) => (
                                    <Chip
                                        key={freq}
                                        label={t('profile.sport_frequency_value', { count: freq })}
                                        active={sportFrequency === freq}
                                        onPress={() => setSportFrequency(freq)}
                                    />
                                ))}
                            </View>

                            <TouchableOpacity
                                style={[styles.sportSaveButton, isSavingSport && styles.sportSaveButtonDisabled]}
                                onPress={saveSportProfile}
                                disabled={isSavingSport || isLoadingSport}
                                activeOpacity={0.8}
                            >
                                <Text style={styles.sportSaveButtonText}>
                                    {isSavingSport ? '...' : t('common.save')}
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </>
                )}

                {/* UNITES UTILISEES */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('profile.units')}
                </Text>

                <View style={styles.card}>
                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('profile.weight_unit')}
                        </Text>

                        <View style={styles.chipRow}>
                            {WEIGHT_UNITS.map((unit) => (
                                <Chip
                                    key={unit}
                                    label={unit}
                                    active={prefs.weightUnit === unit}
                                    onPress={() => updatePreferences({ weightUnit: unit })}
                                />
                            ))}
                        </View>
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('profile.height_unit')}
                        </Text>

                        <View style={styles.chipRow}>
                            {HEIGHT_UNITS.map((unit) => (
                                <Chip
                                    key={unit}
                                    label={unit}
                                    active={prefs.heightUnit === unit}
                                    onPress={() => updatePreferences({ heightUnit: unit })}
                                />
                            ))}
                        </View>
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('profile.distance_unit')}
                        </Text>

                        <View style={styles.chipRow}>
                            {DISTANCE_UNITS.map((unit) => (
                                <Chip
                                    key={unit}
                                    label={unit}
                                    active={prefs.distanceUnit === unit}
                                    onPress={() => updatePreferences({ distanceUnit: unit })}
                                />
                            ))}
                        </View>
                    </View>
                </View>

                {/* PREFERENCES ALIMENTAIRES */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('profile.dietary')}
                </Text>

                <View style={styles.card}>
                    <View style={styles.chipWrap}>
                        {DIETS.map((diet) => (
                            <Chip
                                key={diet}
                                label={t(`profile.diet_${diet}`)}
                                active={draft.diet === diet}
                                onPress={() => updateDraft({ diet })}
                                large
                            />
                        ))}
                    </View>
                </View>

                {/* ALLERGIES / INTOLERANCES */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('profile.allergies')}
                </Text>

                <View style={styles.card}>
                    <View style={styles.chipWrap}>
                        {COMMON_ALLERGENS.map((key) => (
                            <Chip
                                key={key}
                                label={t(`profile.allergen_${key}`)}
                                active={(draft.allergies ?? []).includes(key)}
                                onPress={() => toggleDraftAllergy(key)}
                                large
                            />
                        ))}
                    </View>

                    <View style={[styles.row, isRTL && styles.rowRTL, styles.rowBorder]}>
                        <Text style={[styles.rowDescription, isRTL && styles.textRTL]}>
                            {t('profile.allergies_hint')}
                        </Text>
                    </View>
                </View>

                {/* BUDGET ALIMENTAIRE */}
                <Text style={[styles.sectionTitle, isRTL && styles.textRTL]}>
                    {t('profile.budget')}
                </Text>

                <View style={styles.card}>
                    <View style={[styles.row, isRTL && styles.rowRTL]}>
                        <Text style={[styles.rowLabel, isRTL && styles.textRTL]}>
                            {t('profile.budget_per_week')}
                        </Text>

                        <TextInput
                            style={[styles.budgetInput, isRTL && styles.textRTL]}
                            value={draft.budgetPerWeek ?? ''}
                            onChangeText={(value) =>
                                updateDraft({ budgetPerWeek: value.replace(',', '.').replace(/[^0-9.]/g, '') })
                            }
                            placeholder="0"
                            placeholderTextColor={colors.secondaryText}
                            keyboardType="numeric"
                        />
                    </View>
                </View>

                {/* ENREGISTRER (identite + infos onboarding + regime/allergies/budget) */}
                <TouchableOpacity
                    style={[styles.saveButton, isSavingProfile && styles.saveButtonDisabled]}
                    onPress={saveProfile}
                    disabled={isSavingProfile}
                    activeOpacity={0.85}
                >
                    <Text style={styles.saveButtonText}>
                        {isSavingProfile ? '...' : t('common.save')}
                    </Text>
                </TouchableOpacity>
            </ScrollView>
        </SafeAreaView>
    );
}

function Chip({ label, active, onPress, large }) {
    return (
        <TouchableOpacity
            style={[styles.chip, large && styles.chipLarge, active && styles.chipActive]}
            onPress={onPress}
            activeOpacity={0.7}
        >
            <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {label}
            </Text>
        </TouchableOpacity>
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

    identityCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.white,
        borderRadius: 18,
        borderWidth: 1,
        borderColor: colors.border,
        padding: 18,
        marginBottom: 24,
        gap: 14,
    },

    avatar: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: colors.primary,
        alignItems: 'center',
        justifyContent: 'center',
    },

    identityText: {
        flex: 1,
    },

    username: {
        fontSize: 19,
        fontWeight: '800',
        color: colors.text,
    },

    identityMeta: {
        fontSize: 13,
        color: colors.secondaryText,
        marginTop: 2,
    },

    sectionTitle: {
        fontSize: 15,
        fontWeight: '700',
        color: colors.secondaryText,
        marginBottom: 10,
        textTransform: 'uppercase',
    },

    textRTL: {
        textAlign: 'right',
    },

    card: {
        backgroundColor: colors.white,
        borderRadius: 18,
        borderWidth: 1,
        borderColor: colors.border,
        marginBottom: 24,
        overflow: 'hidden',
    },

    row: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 14,
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

    rowLabel: {
        fontSize: 16,
        color: colors.text,
        fontWeight: '600',
        flex: 1,
    },

    rowDescription: {
        fontSize: 13,
        color: colors.secondaryText,
        flex: 1,
    },

    chipRow: {
        flexDirection: 'row',
        gap: 8,
    },

    chipWrap: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
        padding: 14,
    },

    chip: {
        paddingHorizontal: 12,
        paddingVertical: 7,
        borderRadius: 14,
        backgroundColor: colors.background,
        borderWidth: 1,
        borderColor: colors.border,
    },

    chipLarge: {
        paddingHorizontal: 14,
        paddingVertical: 9,
    },

    chipActive: {
        backgroundColor: colors.primaryLight,
        borderColor: colors.primary,
    },

    chipText: {
        fontSize: 13,
        color: colors.secondaryText,
        fontWeight: '600',
    },

    chipTextActive: {
        color: colors.primary,
    },

    textInput: {
        minWidth: 140,
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: colors.border,
        fontSize: 16,
        color: colors.text,
        textAlign: 'right',
    },

    numberInput: {
        minWidth: 90,
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: colors.border,
        fontSize: 16,
        color: colors.text,
        textAlign: 'right',
    },

    budgetInput: {
        minWidth: 90,
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: colors.border,
        fontSize: 16,
        color: colors.text,
        textAlign: 'right',
    },

    sportSaveButton: {
        margin: 14,
        marginTop: 4,
        paddingVertical: 12,
        borderRadius: 14,
        backgroundColor: colors.primary,
        alignItems: 'center',
    },

    sportSaveButtonDisabled: {
        opacity: 0.6,
    },

    sportSaveButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: colors.white,
    },

    saveButton: {
        marginTop: 4,
        paddingVertical: 16,
        borderRadius: 16,
        backgroundColor: colors.primary,
        alignItems: 'center',
    },

    saveButtonDisabled: {
        opacity: 0.6,
    },

    saveButtonText: {
        fontSize: 16,
        fontWeight: '800',
        color: colors.white,
    },
});
