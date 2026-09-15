import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { apiRequest } from '../constants/api';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';
import { useUser } from '../user/UserContext';
import { requestNutritionRefresh } from '../constants/refreshBus';

const MEAL_TYPES = [
    { value: 'breakfast', label: 'Petit-déjeuner' },
    { value: 'lunch', label: 'Déjeuner' },
    { value: 'dinner', label: 'Dîner' },
    { value: 'snack', label: 'Collation' },
];

const UNITS = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'cup', 'serving'];

export default function AddMealScreen() {
    const router = useRouter();
    const { user } = useUser();
    const { language } = useI18n();
    const params = useLocalSearchParams();
    const [mealType, setMealType] = useState(params.mealType || 'breakfast');

    // Champ 1 : repas recommandé (venant du plan alimentaire)
    const [recommended, setRecommended] = useState(
        params.recommendedName ? {
            name: params.recommendedName,
            calories_kcal: Number(params.recommendedCalories) || 0,
            protein_g: Number(params.recommendedProtein) || 0,
            carbs_g: Number(params.recommendedCarbs) || 0,
            fat_g: Number(params.recommendedFat) || 0,
        } : null,
    );
    const [useRecommended, setUseRecommended] = useState(Boolean(params.recommendedName));

    // Champ 2 : un autre aliment de son choix
    const [search, setSearch] = useState('');
    const [foods, setFoods] = useState([]);
    const [selectedFood, setSelectedFood] = useState(null);
    const [quantity, setQuantity] = useState('100');
    const [unit, setUnit] = useState('g');
    const [isSearching, setIsSearching] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!search.trim()) {
            setFoods([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsSearching(true);
            try {
                const data = await apiRequest(
                    `/api/v1/foods?search=${encodeURIComponent(search.trim())}&language=${language || 'fr'}&limit=10`
                );
                setFoods(data.items || []);
            } catch (error) {
                if (__DEV__) console.warn('[add-meal] recherche impossible:', error.message);
            } finally {
                setIsSearching(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [search, language]);

    const saveMeal = async () => {
        if (!user?.userId) {
            Alert.alert('Erreur', 'Utilisateur non connecté.');
            return;
        }

        const numericQuantity = Number(quantity.replace(',', '.'));
        if (selectedFood && (!Number.isFinite(numericQuantity) || numericQuantity <= 0)) {
            Alert.alert('Quantité invalide', 'Entre une quantité supérieure à 0.');
            return;
        }

        if (!selectedFood && !useRecommended) {
            Alert.alert('Repas incomplet', 'Ajoute le repas recommandé ou un autre aliment.');
            return;
        }

        setIsSaving(true);
        try {
            const body = { meal_type: mealType, items: [] };

            // Enregistrer sur la date du jour sélectionné dans la page Nutrition
            if (params.consumedOn) {
                body.consumed_on = params.consumedOn;
            }

            // Champ 1 : macros du repas recommandé (déjà calculées)
            if (useRecommended && recommended) {
                body.name = recommended.name;
                body.calories_kcal = recommended.calories_kcal;
                body.protein_g = recommended.protein_g;
                body.carbs_g = recommended.carbs_g;
                body.fat_g = recommended.fat_g;
            }

            // Champ 2 : aliment choisi, calculé côté serveur
            if (selectedFood) {
                body.items.push({
                    food_slug: selectedFood.slug,
                    quantity: numericQuantity,
                    unit,
                });
            }

            await apiRequest(`/nutrition-tracking/meals/${user.userId}`, {
                method: 'POST',
                body: JSON.stringify(body),
            });
            requestNutritionRefresh();
            Alert.alert('Repas enregistré', 'Le repas a été ajouté à ton suivi.', [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (error) {
            Alert.alert('Erreur', error.message);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            <View style={styles.header}>
                <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={styles.title}>Ajouter un repas</Text>
                <View style={styles.iconButton} />
            </View>

            <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
                <Text style={styles.label}>Type de repas</Text>
                <View style={styles.typeRow}>
                    {MEAL_TYPES.map((item) => (
                        <TouchableOpacity
                            key={item.value}
                            style={[styles.typeButton, mealType === item.value && styles.selectedButton]}
                            onPress={() => setMealType(item.value)}
                        >
                            <Text style={[styles.typeText, mealType === item.value && styles.selectedText]}>
                                {item.label}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* CHAMP 1 : REPAS RECOMMANDÉ */}

                <Text style={styles.label}>Repas recommandé</Text>
                {recommended ? (
                    <TouchableOpacity
                        style={[styles.typeButton, styles.recommendedCard, useRecommended && styles.selectedButton]}
                        onPress={() => setUseRecommended((value) => !value)}
                    >
                        <View style={{ flex: 1 }}>
                            <Text style={[styles.typeText, useRecommended && styles.selectedText, styles.recommendedName]}>
                                {recommended.name}
                            </Text>
                            <Text style={[styles.foodMeta, useRecommended && styles.selectedText]}>
                                {Math.round(recommended.calories_kcal)} kcal | {Math.round(recommended.protein_g)}g P | {Math.round(recommended.carbs_g)}g G | {Math.round(recommended.fat_g)}g L
                            </Text>
                            <Text style={[styles.foodMeta, useRecommended && styles.selectedText]}>
                                {useRecommended ? '✓ Inclus dans le repas' : 'Appuie pour inclure ce repas'}
                            </Text>
                        </View>
                    </TouchableOpacity>
                ) : (
                    <View style={styles.emptyRecommended}>
                        <Text style={styles.foodMeta}>Aucun repas recommandé pour ce type.</Text>
                    </View>
                )}

                {/* CHAMP 2 : AUTRE ALIMENT */}

                <Text style={styles.label}>Autre aliment</Text>
                <TextInput
                    style={styles.input}
                    value={selectedFood ? selectedFood.name : search}
                    onChangeText={(value) => {
                        setSelectedFood(null);
                        setSearch(value);
                    }}
                    placeholder="Rechercher un aliment"
                    placeholderTextColor={colors.secondaryText}
                />
                {isSearching && <ActivityIndicator color={colors.primary} style={styles.loader} />}
                {foods.map((food) => (
                    <TouchableOpacity
                        key={food.id}
                        style={styles.foodResult}
                        onPress={() => {
                            setSelectedFood(food);
                            setSearch(food.name);
                            setFoods([]);
                            setUnit(food.default_unit || 'g');
                        }}
                    >
                        <Text style={styles.foodName}>{food.name}</Text>
                        <Text style={styles.foodMeta}>{food.calories_kcal} kcal / 100 g</Text>
                    </TouchableOpacity>
                ))}

                <View style={styles.quantityRow}>
                    <View style={styles.quantityField}>
                        <Text style={styles.label}>Quantité</Text>
                        <TextInput
                            style={styles.input}
                            value={quantity}
                            onChangeText={setQuantity}
                            keyboardType="decimal-pad"
                        />
                    </View>
                    <View style={styles.unitField}>
                        <Text style={styles.label}>Unité</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.unitRow}>
                            {UNITS.map((item) => (
                                <TouchableOpacity
                                    key={item}
                                    style={[styles.unitButton, unit === item && styles.selectedButton]}
                                    onPress={() => setUnit(item)}
                                >
                                    <Text style={[styles.unitText, unit === item && styles.selectedText]}>{item}</Text>
                                </TouchableOpacity>
                            ))}
                        </ScrollView>
                    </View>
                </View>

                <TouchableOpacity style={styles.saveButton} onPress={saveMeal} disabled={isSaving}>
                    {isSaving ? <ActivityIndicator color={colors.white} /> : <Text style={styles.saveText}>Enregistrer le repas</Text>}
                </TouchableOpacity>
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
    label: { color: colors.text, fontSize: 15, fontWeight: '700', marginBottom: 8, marginTop: 16 },
    typeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
    typeButton: { borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10, backgroundColor: colors.white },
    selectedButton: { backgroundColor: colors.primary, borderColor: colors.primary },
    typeText: { color: colors.text, fontSize: 13 },
    selectedText: { color: colors.white, fontWeight: '700' },
    input: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, color: colors.text, fontSize: 16 },
    loader: { marginTop: 12 },
    foodResult: { backgroundColor: colors.white, borderBottomWidth: 1, borderBottomColor: colors.border, padding: 13 },
    foodName: { color: colors.text, fontWeight: '700' },
    foodMeta: { color: colors.secondaryText, fontSize: 12, marginTop: 3 },
    quantityRow: { flexDirection: 'row', gap: 12, alignItems: 'flex-end' },
    quantityField: { width: 110 },
    unitField: { flex: 1 },
    unitRow: { gap: 6 },
    unitButton: { borderWidth: 1, borderColor: colors.border, borderRadius: 9, paddingHorizontal: 10, paddingVertical: 9, backgroundColor: colors.white },
    unitText: { color: colors.text, fontSize: 13 },
    saveButton: { alignItems: 'center', justifyContent: 'center', minHeight: 50, backgroundColor: colors.primary, borderRadius: 14, marginTop: 30 },
    saveText: { color: colors.white, fontSize: 16, fontWeight: '800' },
    recommendedCard: { flexDirection: 'row', alignItems: 'center', padding: 14 },
    recommendedName: { fontSize: 16, fontWeight: '800', marginBottom: 4 },
    emptyRecommended: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderStyle: 'dashed', borderRadius: 12, padding: 14 },
});
