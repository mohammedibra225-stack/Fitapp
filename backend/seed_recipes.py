"""
Seed de quelques recettes de test, pour pouvoir tester le lien
Recettes <-> Inventaire (endpoint /recipes/{recipe_id}/can-cook/{user_id}).

Utilise des aliments deja presents via seed_foods.py (oeuf, huile_olive,
riz, poulet, tomate, oignon). Lance seed_foods.py AVANT ce script.

Idempotent : si une recette existe deja (meme slug), elle est ignoree.
"""

from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.enums import HalalStatus, MeasurementUnit, MealType, RecipeNutritionStatus
from app.models.food import Food
from app.models.recipe import Recipe, RecipeIngredient, RecipeStep, RecipeStepTranslation, RecipeTranslation


RECIPES = [
    {
        "slug": "omelette-simple",
        "prep_time_minutes": 5,
        "cook_time_minutes": 5,
        "difficulty": "easy",
        "servings": 1,
        "is_vegetarian": True,
        "is_vegan": False,
        "is_halal": True,
        "is_gluten_free": True,
        "estimated_cost_level": 1,
        "translations": {
            "fr": {"name": "Omelette simple", "description": "Une omelette rapide et economique."},
            "en": {"name": "Simple omelette", "description": "A quick, cheap omelette."},
            "es": {"name": "Tortilla simple", "description": "Una tortilla rapida y economica."},
            "ar": {"name": "أومليت بسيط", "description": "أومليت سريع واقتصادي."},
        },
        "ingredients": [
            {"food_slug": "oeuf", "quantity": 3, "unit": MeasurementUnit.PIECE},
            {"food_slug": "huile_olive", "quantity": 10, "unit": MeasurementUnit.ML},
        ],
        "steps": [
            {"fr": "Battre les œufs dans un bol.", "en": "Beat the eggs in a bowl.", "es": "Batir los huevos en un bol.", "ar": "اخفق البيض في وعاء."},
            {"fr": "Faire chauffer l'huile puis cuire l'omelette 3 minutes.", "en": "Heat the oil then cook the omelette for 3 minutes.", "es": "Calentar el aceite y cocinar la tortilla 3 minutos.", "ar": "سخّن الزيت ثم اطبخ الأومليت لمدة 3 دقائق."},
        ],
    },
    {
        "slug": "riz-au-poulet",
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "difficulty": "medium",
        "servings": 2,
        "is_vegetarian": False,
        "is_vegan": False,
        "is_halal": True,
        "is_gluten_free": True,
        "estimated_cost_level": 2,
        "calories_kcal": 575,
        "protein_g": 58,
        "carbs_g": 60,
        "fat_g": 12,
        "meal_type": "lunch",
        "translations": {
            "fr": {"name": "Riz au poulet", "description": "Un plat complet riche en proteines."},
            "en": {"name": "Chicken and rice", "description": "A complete, protein-rich meal."},
            "es": {"name": "Arroz con pollo", "description": "Un plato completo rico en proteinas."},
            "ar": {"name": "أرز بالدجاج", "description": "طبق كامل غني بالبروتين."},
        },
        "ingredients": [
            {"food_slug": "riz", "quantity": 300, "unit": MeasurementUnit.G},
            {"food_slug": "poulet", "quantity": 400, "unit": MeasurementUnit.G},
            {"food_slug": "huile_olive", "quantity": 15, "unit": MeasurementUnit.ML},
        ],
        "steps": [
            {"fr": "Faire cuire le riz dans l'eau bouillante.", "en": "Cook the rice in boiling water.", "es": "Cocinar el arroz en agua hirviendo.", "ar": "اطبخ الأرز في ماء مغلي."},
            {"fr": "Faire revenir le poulet dans l'huile jusqu'a cuisson complete.", "en": "Sear the chicken in the oil until fully cooked.", "es": "Sofreir el pollo en el aceite hasta que este totalmente cocido.", "ar": "شوّح الدجاج في الزيت حتى ينضج تماما."},
            {"fr": "Melanger le riz et le poulet, servir chaud.", "en": "Mix the rice and chicken, serve hot.", "es": "Mezclar el arroz y el pollo, servir caliente.", "ar": "اخلط الأرز والدجاج وقدّمه ساخنا."},
        ],
    },
]


def _recipe(slug, fr, en, meal_type, ingredients, calories, protein, carbs, fat,
            vegetarian=False, vegan=False, gluten_free=True, cost=1,
            es=None, ar=None):
    return {
        "slug": slug, "prep_time_minutes": 10, "cook_time_minutes": 20,
        "difficulty": "easy", "servings": 1, "is_vegetarian": vegetarian,
        "is_vegan": vegan, "is_halal": True, "is_gluten_free": gluten_free,
        "estimated_cost_level": cost, "meal_type": meal_type,
        "calories_kcal": calories, "protein_g": protein, "carbs_g": carbs,
        "fat_g": fat,
        "translations": {
            "fr": {"name": fr, "description": "Recette adaptee a votre objectif nutritionnel."},
            "en": {"name": en, "description": "A recipe adapted to your nutrition goal."},
            "es": {"name": es or en, "description": "Una receta adaptada a tu objetivo nutricional."},
            "ar": {"name": ar or en, "description": "وصفة مناسبة لهدفك الغذائي."},
        },
        "ingredients": ingredients,
        "steps": [
            {"fr": "Preparer les ingredients puis cuire jusqu'a ce qu'ils soient tendres.",
             "en": "Prepare the ingredients and cook until tender.",
             "es": "Preparar los ingredientes y cocinar hasta que esten tiernos.",
             "ar": "حضّر المكونات ثم اطبخها حتى تصبح طرية."},
        ],
    }

# Recettes locales variees : elles sont filtrees ensuite par le profil et
# selectionnees selon les cibles de chaque repas.
RECIPES.extend([
    _recipe("porridge-banane", "Porridge banane avoine", "Banana oat porridge", "breakfast",
            [{"food_slug": "avoine", "quantity": 60, "unit": MeasurementUnit.G}, {"food_slug": "banane", "quantity": 1, "unit": MeasurementUnit.PIECE}, {"food_slug": "lait", "quantity": 200, "unit": MeasurementUnit.ML}], 430, 16, 68, 11, vegetarian=True),
    _recipe("omelette-legumes", "Omelette aux legumes", "Vegetable omelette", "breakfast",
            [{"food_slug": "oeuf", "quantity": 3, "unit": MeasurementUnit.PIECE}, {"food_slug": "tomate", "quantity": 100, "unit": MeasurementUnit.G}, {"food_slug": "oignon", "quantity": 50, "unit": MeasurementUnit.G}], 320, 22, 12, 19, vegetarian=True),
    _recipe("salade-quinoa-pois-chiches", "Salade quinoa pois chiches", "Quinoa chickpea salad", "lunch",
            [{"food_slug": "quinoa", "quantity": 100, "unit": MeasurementUnit.G}, {"food_slug": "pois_chiches", "quantity": 120, "unit": MeasurementUnit.G}, {"food_slug": "tomate", "quantity": 120, "unit": MeasurementUnit.G}], 520, 22, 78, 14, vegetarian=True, vegan=True),
    _recipe("poulet-patate-douce", "Poulet et patate douce", "Chicken sweet potato bowl", "lunch",
            [{"food_slug": "blanc_de_poulet", "quantity": 180, "unit": MeasurementUnit.G}, {"food_slug": "patate_douce", "quantity": 250, "unit": MeasurementUnit.G}, {"food_slug": "huile_olive", "quantity": 10, "unit": MeasurementUnit.ML}], 610, 52, 55, 18, cost=2),
    _recipe("saumon-quinoa", "Saumon et quinoa", "Salmon with quinoa", "dinner",
            [{"food_slug": "saumon", "quantity": 160, "unit": MeasurementUnit.G}, {"food_slug": "quinoa", "quantity": 100, "unit": MeasurementUnit.G}, {"food_slug": "courgette", "quantity": 150, "unit": MeasurementUnit.G}], 590, 43, 48, 24, cost=3),
    _recipe("tofu-legumes", "Tofu aux legumes", "Tofu vegetable stir-fry", "dinner",
            [{"food_slug": "tofu", "quantity": 180, "unit": MeasurementUnit.G}, {"food_slug": "courgette", "quantity": 150, "unit": MeasurementUnit.G}, {"food_slug": "carotte", "quantity": 100, "unit": MeasurementUnit.G}], 350, 28, 27, 16, vegetarian=True, vegan=True),
    _recipe("salade-thon-oeuf", "Salade thon et oeuf", "Tuna egg salad", "lunch",
            [{"food_slug": "thon_conserve", "quantity": 120, "unit": MeasurementUnit.G}, {"food_slug": "oeuf", "quantity": 2, "unit": MeasurementUnit.PIECE}, {"food_slug": "salade", "quantity": 100, "unit": MeasurementUnit.G}], 390, 43, 8, 20, cost=2),
    _recipe("yaourt-fruits-noix", "Yaourt fruits et noix", "Yogurt fruit and walnuts", "snack",
            [{"food_slug": "yaourt_nature", "quantity": 200, "unit": MeasurementUnit.G}, {"food_slug": "fraise", "quantity": 100, "unit": MeasurementUnit.G}, {"food_slug": "noix", "quantity": 15, "unit": MeasurementUnit.G}], 260, 12, 22, 14, vegetarian=True),
    _recipe("smoothie-banane", "Smoothie banane", "Banana smoothie", "snack",
            [{"food_slug": "banane", "quantity": 1, "unit": MeasurementUnit.PIECE}, {"food_slug": "lait", "quantity": 250, "unit": MeasurementUnit.ML}], 210, 9, 37, 5, vegetarian=True),
])


def _generate_recipe_catalog() -> list[dict]:
    # Genere 160 recettes distinctes avec des aliments presents dans Food DB.
    proteins = [
        ("blanc_de_poulet", "Poulet", "Chicken", 31, False, False),
        ("poulet", "Poulet roti", "Roast chicken", 27, False, False),
        ("dinde", "Dinde", "Turkey", 29, False, False),
        ("viande_hachee", "Boeuf hache", "Ground beef", 25, False, False),
        ("saumon", "Saumon", "Salmon", 20, False, False),
        ("thon_conserve", "Thon", "Tuna", 29, False, False),
        ("tofu", "Tofu", "Tofu", 8, True, True),
        ("pois_chiches", "Pois chiches", "Chickpeas", 9, True, True),
    ]
    bases = [
        ("riz", "Riz", "Rice", 75, MeasurementUnit.G),
        ("pates", "Pates", "Pasta", 70, MeasurementUnit.G),
        ("quinoa", "Quinoa", "Quinoa", 40, MeasurementUnit.G),
        ("patate_douce", "Patate douce", "Sweet potato", 35, MeasurementUnit.G),
    ]
    vegetables = [
        ("tomate", "Tomate", "Tomato", 120),
        ("carotte", "Carotte", "Carrot", 120),
        ("courgette", "Courgette", "Zucchini", 150),
        ("oignon", "Oignon", "Onion", 80),
        ("salade", "Salade verte", "Green salad", 100),
    ]
    catalog = []
    # Traductions es/ar des proteines, bases et legumes.
    protein_es = {"blanc_de_poulet": "Pechuga de pollo", "poulet": "Pollo asado", "dinde": "Pavo",
                  "viande_hachee": "Carne molida", "saumon": "Salmon", "thon_conserve": "Atun",
                  "tofu": "Tofu", "pois_chiches": "Garbanzos"}
    protein_ar = {"blanc_de_poulet": "صدر الدجاج", "poulet": "دجاج مشوي", "dinde": "ديك رومي",
                  "viande_hachee": "لحم مفروم", "saumon": "سلمون", "thon_conserve": "تونة",
                  "tofu": "توفو", "pois_chiches": "حمص"}
    base_es = {"riz": "Arroz", "pates": "Pasta", "quinoa": "Quinoa", "patate_douce": "Batata"}
    base_ar = {"riz": "أرز", "pates": "معكرونة", "quinoa": "كينوا", "patate_douce": "بطاطا حلوة"}
    vegetable_es = {"tomate": "Tomate", "carotte": "Zanahoria", "courgette": "Calabacin",
                    "oignon": "Cebolla", "salade": "Ensalada verde"}
    vegetable_ar = {"tomate": "طماطم", "carotte": "جزر", "courgette": "كوسا",
                    "oignon": "بصل", "salade": "سلطة خضراء"}
    for protein_slug, protein_fr, protein_en, protein_g, is_vegan, is_vegetarian in proteins:
        for base_slug, base_fr, base_en, base_carbs, base_unit in bases:
            for vegetable_slug, vegetable_fr, vegetable_en, vegetable_qty in vegetables:
                slug = f"bowl-{protein_slug}-{base_slug}-{vegetable_slug}"
                fr = f"Bowl {protein_fr}, {base_fr} et {vegetable_fr}"
                en = f"{protein_en}, {base_en} and {vegetable_en} bowl"
                es = f"Bowl de {protein_es[protein_slug]}, {base_es[base_slug]} y {vegetable_es[vegetable_slug]}"
                ar = f"طبق {protein_ar[protein_slug]} و{base_ar[base_slug]} و{vegetable_ar[vegetable_slug]}"
                calories = 360 + protein_g * 5 + base_carbs * 2
                catalog.append(_recipe(
                    slug, fr, en, "dinner" if base_slug in ("pates", "patate_douce") else "lunch",
                    [
                        {"food_slug": protein_slug, "quantity": 150, "unit": MeasurementUnit.G},
                        {"food_slug": base_slug, "quantity": 100, "unit": base_unit},
                        {"food_slug": vegetable_slug, "quantity": vegetable_qty, "unit": MeasurementUnit.G},
                    ], calories, protein_g + 8, base_carbs, 12 if is_vegan else 18,
                    vegetarian=is_vegetarian, vegan=is_vegan, cost=2 if protein_slug in ("saumon", "thon_conserve") else 1,
                    es=es, ar=ar,
                ))
    return catalog
# 8 proteines x 4 bases x 5 legumes = 160 recettes supplementaires.
RECIPES.extend(_generate_recipe_catalog())


def _generate_breakfast_snack_catalog() -> list[dict]:
    recipes = []
    breakfast_items = [
        ("avoine-banane", "Porridge avoine banane", "Banana oat porridge", "avoine", "banane", 420, 15, 66, 10),
        ("avoine-pomme", "Porridge avoine pomme", "Apple oat porridge", "avoine", "pomme", 390, 14, 63, 9),
        ("yaourt-fraise", "Bol yaourt fraise", "Strawberry yogurt bowl", "yaourt_nature", "fraise", 250, 13, 28, 9),
        ("yaourt-pomme-amande", "Yaourt pomme amande", "Apple almond yogurt", "yaourt_nature", "pomme", 310, 15, 32, 13),
        ("oeufs-tomate", "Oeufs et tomate", "Eggs with tomato", "oeuf", "tomate", 300, 21, 10, 18),
        ("pancake-banane", "Pancake banane avoine", "Banana oat pancakes", "banane", "avoine", 410, 16, 59, 12),
        ("fromage-frais-fruit", "Fromage frais aux fruits", "Fresh cheese with fruit", "fromage_frais", "fraise", 280, 19, 25, 11),
    ]
    snack_items = [
        ("snack-banane-amande", "Banane et amandes", "Banana and almonds", "banane", "amandes", 250, 7, 30, 13),
        ("snack-pomme-noix", "Pomme et noix", "Apple and walnuts", "pomme", "noix", 270, 4, 28, 17),
        ("snack-yaourt-miel", "Yaourt au miel", "Honey yogurt", "yaourt_nature", "miel", 210, 9, 30, 6),
        ("snack-fraise-yaourt", "Fraises et yaourt", "Strawberries and yogurt", "fraise", "yaourt_nature", 180, 10, 24, 5),
        ("snack-fromage-pomme", "Fromage frais et pomme", "Fresh cheese and apple", "fromage_frais", "pomme", 230, 13, 25, 9),
        ("snack-banane-lait", "Lait banane", "Banana milk", "lait", "banane", 220, 9, 38, 5),
        ("snack-amande-fraise", "Amandes et fraises", "Almonds and strawberries", "amandes", "fraise", 240, 8, 18, 16),
    ]
    # Traductions es/ar des noms d'aliments utilises dans les catalogues.
    food_es = {"avoine": "avena", "banane": "platano", "pomme": "manzana", "yaourt_nature": "yogur natural",
               "fraise": "fresa", "fromage_frais": "queso fresco", "amandes": "almendras", "noix": "nueces",
               "miel": "miel", "oeuf": "huevos", "tomate": "tomate", "lait": "leche"}
    food_ar = {"avoine": "شوفان", "banane": "موز", "pomme": "تفاح", "yaourt_nature": "زبادي طبيعي",
               "fraise": "فراولة", "fromage_frais": "جبن طري", "amandes": "لوز", "noix": "جوز",
               "miel": "عسل", "oeuf": "بيض", "tomate": "طماطم", "lait": "حليب"}
    for index, (slug, fr, en, first, second, calories, protein, carbs, fat) in enumerate(breakfast_items):
        recipes.append(_recipe(slug, fr, en, "breakfast", [
            {"food_slug": first, "quantity": 80 if first == "avoine" else 150, "unit": MeasurementUnit.G},
            {"food_slug": second, "quantity": 1 if second in ("banane", "pomme") else 100, "unit": MeasurementUnit.PIECE if second in ("banane", "pomme") else MeasurementUnit.G},
        ], calories, protein, carbs, fat, vegetarian=True,
            es=f"{food_es[first].capitalize()} con {food_es[second]}",
            ar=f"{food_ar[first]} مع {food_ar[second]}"))
    for slug, fr, en, first, second, calories, protein, carbs, fat in snack_items:
        recipes.append(_recipe(slug, fr, en, "snack", [
            {"food_slug": first, "quantity": 150, "unit": MeasurementUnit.G},
            {"food_slug": second, "quantity": 100, "unit": MeasurementUnit.G},
        ], calories, protein, carbs, fat, vegetarian=True,
            es=f"{food_es[first].capitalize()} con {food_es[second]}",
            ar=f"{food_ar[first]} مع {food_ar[second]}"))
    return recipes
RECIPES.extend(_generate_breakfast_snack_catalog())


def seed_recipes():
    db = SessionLocal()

    created = 0
    skipped = 0

    try:
        for data in RECIPES:

            existing = db.query(Recipe).filter(Recipe.slug == data["slug"]).first()
            if existing is not None:
                # Les seeds sont idempotents, mais les champs nutritionnels
                # et le type de repas doivent rester synchronises.
                if data.get("calories_kcal"):
                    existing.calories_kcal = data["calories_kcal"]
                    existing.protein_g = data["protein_g"]
                    existing.carbs_g = data["carbs_g"]
                    existing.fat_g = data["fat_g"]
                    existing.nutrition_status = RecipeNutritionStatus.COMPLETE
                if data.get("meal_type"):
                    existing.meal_type = MealType(data["meal_type"])
                # Mise a jour des traductions manquantes (ex. ajout de es/ar)
                # sans ecraser celles qui existent deja.
                existing_translations = {
                    t.language_code: t for t in existing.translations
                }
                for lang_code, tr in data["translations"].items():
                    if lang_code in existing_translations:
                        existing_translations[lang_code].name = tr["name"]
                        existing_translations[lang_code].description = tr["description"]
                    else:
                        db.add(RecipeTranslation(
                            recipe_id=existing.id,
                            language_code=lang_code,
                            name=tr["name"],
                            description=tr["description"],
                        ))
                # Idem pour les etapes : on complete les langues manquantes.
                existing_steps = sorted(existing.steps, key=lambda s: s.step_number)
                for step_number, translations in enumerate(data["steps"], start=1):
                    step = existing_steps[step_number - 1] if step_number <= len(existing_steps) else None
                    if step is None:
                        continue
                    step_by_lang = {t.language_code: t for t in step.translations}
                    for lang_code, instruction in translations.items():
                        if lang_code in step_by_lang:
                            step_by_lang[lang_code].instruction = instruction
                        else:
                            db.add(RecipeStepTranslation(
                                recipe_step_id=step.id,
                                language_code=lang_code,
                                instruction=instruction,
                            ))
                skipped += 1
                continue

            recipe = Recipe(
                slug=data["slug"],
                prep_time_minutes=data["prep_time_minutes"],
                cook_time_minutes=data["cook_time_minutes"],
                difficulty=data["difficulty"],
                servings=data["servings"],
                is_vegetarian=data["is_vegetarian"],
                is_vegan=data["is_vegan"],
                is_halal=data["is_halal"],
                halal_status=HalalStatus.HALAL if data["is_halal"] else HalalStatus.UNKNOWN,
                is_gluten_free=data["is_gluten_free"],
                estimated_cost_level=data["estimated_cost_level"],
                calories_kcal=data.get("calories_kcal"),
                protein_g=data.get("protein_g"),
                carbs_g=data.get("carbs_g"),
                fat_g=data.get("fat_g"),
                nutrition_status=RecipeNutritionStatus.COMPLETE if data.get("calories_kcal") else RecipeNutritionStatus.UNKNOWN,
                meal_type=MealType(data["meal_type"]) if data.get("meal_type") else None,
            )
            db.add(recipe)
            db.flush()

            for lang_code, t in data["translations"].items():
                db.add(
                    RecipeTranslation(
                        recipe_id=recipe.id,
                        language_code=lang_code,
                        name=t["name"],
                        description=t["description"],
                    )
                )

            for order, ing in enumerate(data["ingredients"]):
                food = db.query(Food).filter(Food.slug == ing["food_slug"]).first()
                if food is None:
                    raise ValueError(
                        f"Aliment '{ing['food_slug']}' introuvable. "
                        "Lance seed_foods.py avant seed_recipes.py."
                    )
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        food_id=food.id,
                        quantity=Decimal(str(ing["quantity"])),
                        unit=ing["unit"],
                        display_order=order,
                    )
                )

            for step_number, translations in enumerate(data["steps"], start=1):
                step = RecipeStep(recipe_id=recipe.id, step_number=step_number)
                db.add(step)
                db.flush()
                for lang_code, instruction in translations.items():
                    db.add(
                        RecipeStepTranslation(
                            recipe_step_id=step.id,
                            language_code=lang_code,
                            instruction=instruction,
                        )
                    )

            created += 1

        db.commit()

        print("=" * 60)
        print("SEED RECIPES TERMINE")
        print("=" * 60)
        print(f"Recettes créées  : {created}")
        print(f"Recettes ignorées (déjà présentes) : {skipped}")
        print("=" * 60)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_recipes()
