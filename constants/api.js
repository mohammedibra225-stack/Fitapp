

import AsyncStorage from '@react-native-async-storage/async-storage';

export const API_BASE_URL = 'https://fitapp-api-7grb.onrender.com';

const MEAL_PLAN_CACHE_PREFIX = '@fitapp/meal-plan/';

export function mealPlanCacheKey(userId) {
	return `${MEAL_PLAN_CACHE_PREFIX}${userId}`;
}

export async function getCachedMealPlan(userId) {
	if (!userId) return null;
	const raw = await AsyncStorage.getItem(mealPlanCacheKey(userId));
	return raw ? JSON.parse(raw) : null;
}

export async function cacheMealPlan(userId, mealPlan) {
	if (!userId || !mealPlan) return;
	await AsyncStorage.setItem(mealPlanCacheKey(userId), JSON.stringify(mealPlan));
}

export async function clearCachedMealPlan(userId) {
	if (!userId) return;
	await AsyncStorage.removeItem(mealPlanCacheKey(userId));
}

export async function apiRequest(path, options = {}) {
	const controller = new AbortController();
	// La creation d'un plan peut scorer plusieurs recettes locales ;
	// laisser au backend jusqu'a 30 secondes avant d'abandonner la requete.
	const timeoutId = setTimeout(() => controller.abort(), 30000);

	try {
		const response = await fetch(`${API_BASE_URL}${path}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...(options.headers || {}),
			},
			signal: controller.signal,
		});

		const body = await response.json().catch(() => null);
		if (!response.ok) {
			const detail = typeof body?.detail === 'string'
				? body.detail
				: `Erreur serveur (${response.status})`;
			const error = new Error(detail);
			// Permet a l'appelant de distinguer un 404 (ressource absente)
			// d'une panne reseau : sans ce champ, les deux cas remontent
			// comme un simple Error indifferenciable.
			error.status = response.status;
			throw error;
		}

		return body;
	} catch (error) {
		if (error.name === 'AbortError') {
			throw new Error('Le serveur ne repond pas.');
		}
		throw error;
	} finally {
		clearTimeout(timeoutId);
	}
}


export async function apiUploadRequest(path, formData, options = {}) {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 60000);

	try {
		const response = await fetch(`${API_BASE_URL}${path}`, {
			method: 'POST',
			...options,
			body: formData,
			headers: {
				...(options.headers || {}),
			},
			signal: controller.signal,
		});

		const body = await response.json().catch(() => null);
		if (!response.ok) {
			const detail = typeof body?.detail === 'string'
				? body.detail
				: `Erreur serveur (${response.status})`;
			throw new Error(detail);
		}

		return body;
	} catch (error) {
		if (error.name === 'AbortError') {
			throw new Error("L'analyse prend trop de temps, reessaie.");
		}
		throw error;
	} finally {
		clearTimeout(timeoutId);
	}
}
