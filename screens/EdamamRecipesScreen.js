import React, { useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    FlatList,
    Image,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { apiRequest } from '../constants/api';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';

export default function SpoonacularRecipesScreen() {
    const router = useRouter();
    const { language } = useI18n();
    const [query, setQuery] = useState('');
    const [recipes, setRecipes] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [fromIndex, setFromIndex] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [error, setError] = useState(null);

    const search = async (append = false) => {
        if (query.trim().length < 2) return;
        setIsLoading(true);
        setError(null);
        try {
            const start = append ? fromIndex : 0;
            const data = await apiRequest(
                `/recipes/spoonacular/search?q=${encodeURIComponent(query.trim())}&offset=${start}&number=20`
            );
            const items = data.items || [];
            setRecipes((current) => append ? [...current, ...items] : items);
            setFromIndex(start + items.length);
            setHasMore(items.length === 20);
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsLoading(false);
        }
    };

    const showDetails = (recipe) => {
        const ingredients = (recipe.ingredient_lines || []).join('\n• ');
        const steps = (recipe.steps || []).map((s) => `${s.number}. ${s.step}`).join('\n\n');
        Alert.alert(
            recipe.label || recipe.name || 'Recette',
            `${Math.round(recipe.calories || 0)} kcal\n${Math.round(recipe.protein_g || 0)}g protéines | ${Math.round(recipe.carbs_g || 0)}g glucides | ${Math.round(recipe.fat_g || 0)}g lipides\n\nIngrédients:\n• ${ingredients || 'Non disponibles'}\n\nÉtapes:\n${steps || 'Non disponibles'}`,
            [{ text: 'Fermer' }]
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={styles.title}>Recettes</Text>
                <View style={styles.iconButton} />
            </View>
            <View style={styles.searchRow}>
                <TextInput
                    style={styles.searchInput}
                    value={query}
                    onChangeText={setQuery}
                    onSubmitEditing={search}
                    placeholder="Rechercher une recette"
                    placeholderTextColor={colors.secondaryText}
                    returnKeyType="search"
                />
                <TouchableOpacity style={styles.searchButton} onPress={search}>
                    <Ionicons name="search" size={21} color={colors.white} />
                </TouchableOpacity>
            </View>
            {isLoading && <ActivityIndicator style={styles.loader} color={colors.primary} />}
            {error && <Text style={styles.error}>{error}</Text>}
            <FlatList
                data={recipes}
                keyExtractor={(item) => String(item.id ?? item.label)}
                contentContainerStyle={styles.list}
                ListEmptyComponent={!isLoading ? <Text style={styles.empty}>Recherche une recette pour commencer.</Text> : null}
                renderItem={({ item }) => (
                    <TouchableOpacity style={styles.card} onPress={() => showDetails(item)} activeOpacity={0.85}>
                        {item.image ? <Image source={{ uri: item.image }} style={styles.image} /> : <View style={styles.imageFallback} />}
                        <View style={styles.cardContent}>
                            <Text style={styles.recipeName} numberOfLines={2}>{item.label}</Text>
                            <Text style={styles.source}>{item.source}</Text>
                            <Text style={styles.nutrition}>{Math.round(item.calories)} kcal | {Math.round(item.protein_g)}g protéines</Text>
                            <Text style={styles.detailHint}>Voir les ingrédients</Text>
                        </View>
                    </TouchableOpacity>
                )}
            />
            {hasMore && !isLoading && (
                <TouchableOpacity style={styles.moreButton} onPress={() => search(true)}>
                    <Text style={styles.moreText}>Charger plus de recettes</Text>
                </TouchableOpacity>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
    iconButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
    title: { color: colors.text, fontSize: 20, fontWeight: '800' },
    searchRow: { flexDirection: 'row', gap: 8, paddingHorizontal: 20, marginBottom: 12 },
    searchInput: { flex: 1, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingHorizontal: 14, color: colors.text, fontSize: 16 },
    searchButton: { width: 50, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary },
    loader: { marginVertical: 16 },
    list: { padding: 20, paddingTop: 4 },
    card: { flexDirection: 'row', backgroundColor: colors.white, borderRadius: 16, overflow: 'hidden', marginBottom: 12 },
    image: { width: 110, height: 130 },
    imageFallback: { width: 110, height: 130, backgroundColor: colors.primaryLight },
    cardContent: { flex: 1, padding: 13 },
    recipeName: { color: colors.text, fontSize: 16, fontWeight: '800' },
    source: { color: colors.secondaryText, fontSize: 12, marginTop: 4 },
    nutrition: { color: colors.text, fontSize: 13, marginTop: 12 },
    detailHint: { color: colors.primary, fontSize: 12, fontWeight: '700', marginTop: 8 },
    error: { color: colors.red, textAlign: 'center', paddingHorizontal: 20 },
    empty: { color: colors.secondaryText, textAlign: 'center', marginTop: 50 },
    moreButton: { marginHorizontal: 20, marginBottom: 20, minHeight: 46, borderRadius: 12, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' },
    moreText: { color: colors.white, fontWeight: '800' },
});
