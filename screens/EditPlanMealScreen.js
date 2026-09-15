import React, { useEffect, useState } from 'react';
import { Alert, ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { apiRequest, cacheMealPlan, getCachedMealPlan } from '../constants/api';
import { colors } from '../constants/colors';

export default function EditPlanMealScreen() {
    const router = useRouter();
    const params = useLocalSearchParams();
    const [calories, setCalories] = useState(String(params.calories || ''));
    const [protein, setProtein] = useState(String(params.protein || ''));
    const [carbs, setCarbs] = useState(String(params.carbs || ''));
    const [fat, setFat] = useState(String(params.fat || ''));
    const [isSaving, setIsSaving] = useState(false);
    const [recipes, setRecipes] = useState([]);
    const [selectedRecipeId, setSelectedRecipeId] = useState(params.recipeId || '');
    const [selectedSpoonacularRecipeId, setSelectedSpoonacularRecipeId] = useState(
        params.spoonacularRecipeId || ''
    );

    useEffect(() => {
        apiRequest('/recipes?language=fr&limit=100')
            .then((data) => setRecipes(data.items || []))
            .catch((error) => {
                if (__DEV__) console.warn('[edit-plan] recettes indisponibles:', error.message);
            });
    }, []);

    const save = async () => {
        const values = {
            target_calories_kcal: Number(calories),
            target_protein_g: Number(protein),
            target_carbs_g: Number(carbs),
            target_fat_g: Number(fat),
        };
        if (Object.values(values).some((value) => !Number.isFinite(value) || value <= 0)) {
            Alert.alert('Valeurs invalides', 'Toutes les valeurs doivent être supérieures à 0.');
            return;
        }
        setIsSaving(true);
        try {
            if (selectedRecipeId) values.recipe_id = selectedRecipeId;
            if (selectedSpoonacularRecipeId) {
                values.spoonacular_recipe_id = Number(selectedSpoonacularRecipeId);
            }
            const updatedMeal = await apiRequest(`/nutrition/meal-plan/${params.userId}/meal/${params.mealId}`, {
                method: 'PATCH',
                body: JSON.stringify(values),
            });
            const cachedPlan = await getCachedMealPlan(params.userId);
            if (cachedPlan) {
                const nextPlan = {
                    ...cachedPlan,
                    days: cachedPlan.days.map((day) => ({
                        ...day,
                        meals: day.meals.map((meal) => meal.id === params.mealId
                            ? {
                                ...meal,
                                ...updatedMeal,
                                recipe: selectedRecipeId || selectedSpoonacularRecipeId
                                    ? null
                                    : meal.recipe,
                            }
                            : meal),
                    })),
                };
                await cacheMealPlan(params.userId, nextPlan);
            }
            router.back();
        } catch (error) {
            Alert.alert('Erreur', error.message);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <SafeAreaView style={styles.safeArea}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.iconButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={styles.title}>Modifier le repas</Text>
                <View style={styles.iconButton} />
            </View>
            <View style={styles.content}>
                <Text style={styles.sectionTitle}>Recette du repas</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recipeRow}>
                    {recipes.map((recipe) => (
                        <TouchableOpacity
                            key={recipe.id}
                            style={[styles.recipeButton, selectedRecipeId === recipe.id && styles.selectedRecipe]}
                            onPress={() => setSelectedRecipeId(recipe.id)}
                        >
                            <Text style={[styles.recipeText, selectedRecipeId === recipe.id && styles.selectedText]}>
                                {recipe.name}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>
                {[
                    ['Calories (kcal)', calories, setCalories],
                    ['Protéines (g)', protein, setProtein],
                    ['Glucides (g)', carbs, setCarbs],
                    ['Lipides (g)', fat, setFat],
                ].map(([label, value, setter]) => (
                    <View key={label}>
                        <Text style={styles.label}>{label}</Text>
                        <TextInput style={styles.input} value={value} onChangeText={setter} keyboardType="decimal-pad" />
                    </View>
                ))}
                <TouchableOpacity style={styles.saveButton} onPress={save} disabled={isSaving}>
                    {isSaving ? <ActivityIndicator color={colors.white} /> : <Text style={styles.saveText}>Enregistrer les modifications</Text>}
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: { flex: 1, backgroundColor: colors.background },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
    iconButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
    title: { fontSize: 20, fontWeight: '800', color: colors.text },
    content: { padding: 20 },
    label: { color: colors.text, fontWeight: '700', marginTop: 14, marginBottom: 7 },
    sectionTitle: { color: colors.text, fontSize: 17, fontWeight: '800', marginBottom: 4 },
    recipeRow: { gap: 8, paddingVertical: 8 },
    recipeButton: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10 },
    selectedRecipe: { backgroundColor: colors.primary, borderColor: colors.primary },
    recipeText: { color: colors.text, fontSize: 13 },
    input: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 13, fontSize: 16, color: colors.text },
    saveButton: { backgroundColor: colors.primary, minHeight: 50, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 30 },
    saveText: { color: colors.white, fontWeight: '800', fontSize: 16 },
});
