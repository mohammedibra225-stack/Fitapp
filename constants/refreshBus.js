// Marqueur simple pour ne rafraîchir la page Nutrition que
// lorsqu'un repas vient d'être enregistré (pas à chaque bascule).
let nutritionRefreshRequested = false;

export function requestNutritionRefresh() {
    nutritionRefreshRequested = true;
}

export function consumeNutritionRefresh() {
    const value = nutritionRefreshRequested;
    nutritionRefreshRequested = false;
    return value;
}
