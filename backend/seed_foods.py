from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.enums import HalalStatus
from app.models.food import Food, FoodPrice, FoodTranslation


# ============================================================
# ALIMENTS
# ============================================================

FOODS = [

    # ========================================================
    # CEREALES / FECULENTS
    # ========================================================

    {
        "slug": "riz",
        "is_liquid": False,
        "calories_kcal": 360,
        "protein_g": 7.0,
        "carbs_g": 80.0,
        "fat_g": 0.7,
        "fiber_g": 1.3,
        "sugar_g": 0.1,
        "sodium_mg": 1,
        "saturated_fat_g": 0.2,
        "category": "cereals",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 180,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Riz",
            "en": "Rice",
            "ar": "أرز",
            "es": "Arroz",
        },
    },

    {
        "slug": "pates",
        "is_liquid": False,
        "calories_kcal": 350,
        "protein_g": 12.0,
        "carbs_g": 72.0,
        "fat_g": 1.5,
        "fiber_g": 3.0,
        "sugar_g": 3.0,
        "sodium_mg": 5,
        "saturated_fat_g": 0.3,
        "category": "cereals",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 120,
        "price_quantity": 500,
        "price_unit": "g",
        "translations": {
            "fr": "Pâtes",
            "en": "Pasta",
            "ar": "معكرونة",
            "es": "Pasta",
        },
    },

    {
        "slug": "avoine",
        "is_liquid": False,
        "calories_kcal": 389,
        "protein_g": 16.9,
        "carbs_g": 66.3,
        "fat_g": 6.9,
        "fiber_g": 10.6,
        "sugar_g": 0.9,
        "sodium_mg": 2,
        "saturated_fat_g": 1.2,
        "category": "cereals",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 350,
        "price_quantity": 500,
        "price_unit": "g",
        "translations": {
            "fr": "Flocons d'avoine",
            "en": "Oats",
            "ar": "شوفان",
            "es": "Avena",
        },
    },

    {
        "slug": "semoule",
        "is_liquid": False,
        "calories_kcal": 360,
        "protein_g": 12.7,
        "carbs_g": 72.8,
        "fat_g": 1.1,
        "fiber_g": 3.9,
        "sugar_g": 0.4,
        "sodium_mg": 1,
        "saturated_fat_g": 0.2,
        "category": "cereals",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 70,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Semoule",
            "en": "Semolina",
            "ar": "سميد",
            "es": "Sémola",
        },
    },

    {
        "slug": "pain",
        "is_liquid": False,
        "calories_kcal": 265,
        "protein_g": 9.0,
        "carbs_g": 49.0,
        "fat_g": 3.2,
        "fiber_g": 2.7,
        "sugar_g": 5.0,
        "sodium_mg": 491,
        "saturated_fat_g": 0.7,
        "category": "bakery",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 25,
        "price_quantity": 1,
        "price_unit": "piece",
        "translations": {
            "fr": "Pain",
            "en": "Bread",
            "ar": "خبز",
            "es": "Pan",
        },
    },

    {
        "slug": "pomme_de_terre",
        "is_liquid": False,
        "calories_kcal": 77,
        "protein_g": 2.0,
        "carbs_g": 17.0,
        "fat_g": 0.1,
        "fiber_g": 2.2,
        "sugar_g": 0.8,
        "sodium_mg": 6,
        "saturated_fat_g": 0.0,
        "category": "starchy_vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 80,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Pomme de terre",
            "en": "Potato",
            "ar": "بطاطا",
            "es": "Patata",
        },
    },


    # ========================================================
    # PROTEINES ANIMALES
    # ========================================================

    {
        "slug": "blanc_de_poulet",
        "is_liquid": False,
        "calories_kcal": 165,
        "protein_g": 31.0,
        "carbs_g": 0.0,
        "fat_g": 3.6,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 74,
        "saturated_fat_g": 1.0,
        "category": "meat",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 750,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Blanc de poulet",
            "en": "Chicken breast",
            "ar": "صدر الدجاج",
            "es": "Pechuga de pollo",
        },
    },

    {
        "slug": "poulet",
        "is_liquid": False,
        "calories_kcal": 215,
        "protein_g": 27.0,
        "carbs_g": 0.0,
        "fat_g": 11.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 70,
        "saturated_fat_g": 3.0,
        "category": "meat",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 520,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Poulet",
            "en": "Chicken",
            "ar": "دجاج",
            "es": "Pollo",
        },
    },

    {
        "slug": "boeuf_maigre",
        "is_liquid": False,
        "calories_kcal": 170,
        "protein_g": 26.0,
        "carbs_g": 0.0,
        "fat_g": 7.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 55,
        "saturated_fat_g": 2.8,
        "category": "meat",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 1800,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Bœuf maigre",
            "en": "Lean beef",
            "ar": "لحم بقري قليل الدهن",
            "es": "Carne de vacuno magra",
        },
    },

    {
        "slug": "thon_conserve",
        "is_liquid": False,
        "calories_kcal": 132,
        "protein_g": 29.0,
        "carbs_g": 0.0,
        "fat_g": 1.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 350,
        "saturated_fat_g": 0.3,
        "category": "fish",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 180,
        "price_quantity": 160,
        "price_unit": "g",
        "translations": {
            "fr": "Thon en conserve",
            "en": "Canned tuna",
            "ar": "تونة معلبة",
            "es": "Atún en conserva",
        },
    },

    {
        "slug": "sardines",
        "is_liquid": False,
        "calories_kcal": 208,
        "protein_g": 24.6,
        "carbs_g": 0.0,
        "fat_g": 11.5,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 307,
        "saturated_fat_g": 1.5,
        "category": "fish",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 500,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Sardines",
            "en": "Sardines",
            "ar": "سردين",
            "es": "Sardinas",
        },
    },

    {
        "slug": "oeuf",
        "is_liquid": False,
        "calories_kcal": 143,
        "protein_g": 12.6,
        "carbs_g": 0.7,
        "fat_g": 9.5,
        "fiber_g": 0.0,
        "sugar_g": 0.4,
        "sodium_mg": 142,
        "saturated_fat_g": 3.1,
        "category": "eggs",
        "default_unit": "piece",
        "unit_weight_g": 50,
        "price_da": 250,
        "price_quantity": 10,
        "price_unit": "piece",
        "translations": {
            "fr": "Œuf",
            "en": "Egg",
            "ar": "بيض",
            "es": "Huevo",
        },
    },


    # ========================================================
    # PRODUITS LAITIERS
    # ========================================================

    {
        "slug": "lait",
        "is_liquid": True,
        "calories_kcal": 61,
        "protein_g": 3.2,
        "carbs_g": 4.8,
        "fat_g": 3.3,
        "fiber_g": 0.0,
        "sugar_g": 5.0,
        "sodium_mg": 43,
        "saturated_fat_g": 1.9,
        "category": "dairy",
        "default_unit": "ml",
        "unit_weight_g": None,
        "price_da": 120,
        "price_quantity": 1,
        "price_unit": "l",
        "translations": {
            "fr": "Lait",
            "en": "Milk",
            "ar": "حليب",
            "es": "Leche",
        },
    },

    {
        "slug": "yaourt_nature",
        "is_liquid": False,
        "calories_kcal": 61,
        "protein_g": 3.5,
        "carbs_g": 4.7,
        "fat_g": 3.3,
        "fiber_g": 0.0,
        "sugar_g": 4.7,
        "sodium_mg": 46,
        "saturated_fat_g": 2.1,
        "category": "dairy",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 35,
        "price_quantity": 100,
        "price_unit": "g",
        "translations": {
            "fr": "Yaourt nature",
            "en": "Plain yogurt",
            "ar": "زبادي طبيعي",
            "es": "Yogur natural",
        },
    },

    {
        "slug": "fromage_frais",
        "is_liquid": False,
        "calories_kcal": 98,
        "protein_g": 11.0,
        "carbs_g": 4.0,
        "fat_g": 4.0,
        "fiber_g": 0.0,
        "sugar_g": 3.0,
        "sodium_mg": 350,
        "saturated_fat_g": 2.5,
        "category": "dairy",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 80,
        "price_quantity": 100,
        "price_unit": "g",
        "translations": {
            "fr": "Fromage frais",
            "en": "Fresh cheese",
            "ar": "جبن طازج",
            "es": "Queso fresco",
        },
    },


    # ========================================================
    # LEGUMINEUSES
    # ========================================================

    {
        "slug": "lentilles",
        "is_liquid": False,
        "calories_kcal": 116,
        "protein_g": 9.0,
        "carbs_g": 20.0,
        "fat_g": 0.4,
        "fiber_g": 7.9,
        "sugar_g": 1.8,
        "sodium_mg": 2,
        "saturated_fat_g": 0.1,
        "category": "legumes",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 220,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Lentilles",
            "en": "Lentils",
            "ar": "عدس",
            "es": "Lentejas",
        },
    },

    {
        "slug": "pois_chiches",
        "is_liquid": False,
        "calories_kcal": 164,
        "protein_g": 8.9,
        "carbs_g": 27.4,
        "fat_g": 2.6,
        "fiber_g": 7.6,
        "sugar_g": 4.8,
        "sodium_mg": 7,
        "saturated_fat_g": 0.3,
        "category": "legumes",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 280,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Pois chiches",
            "en": "Chickpeas",
            "ar": "حمص",
            "es": "Garbanzos",
        },
    },

    {
        "slug": "haricots_secs",
        "is_liquid": False,
        "calories_kcal": 127,
        "protein_g": 8.7,
        "carbs_g": 22.8,
        "fat_g": 0.5,
        "fiber_g": 6.4,
        "sugar_g": 0.3,
        "sodium_mg": 1,
        "saturated_fat_g": 0.1,
        "category": "legumes",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 300,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Haricots secs",
            "en": "Dry beans",
            "ar": "فاصوليا جافة",
            "es": "Frijoles secos",
        },
    },


    # ========================================================
    # FRUITS
    # ========================================================

    {
        "slug": "banane",
        "is_liquid": False,
        "calories_kcal": 89,
        "protein_g": 1.1,
        "carbs_g": 22.8,
        "fat_g": 0.3,
        "fiber_g": 2.6,
        "sugar_g": 12.2,
        "sodium_mg": 1,
        "saturated_fat_g": 0.1,
        "category": "fruit",
        "default_unit": "piece",
        "unit_weight_g": 118,
        "price_da": 280,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Banane",
            "en": "Banana",
            "ar": "موز",
            "es": "Plátano",
        },
    },

    {
        "slug": "pomme",
        "is_liquid": False,
        "calories_kcal": 52,
        "protein_g": 0.3,
        "carbs_g": 13.8,
        "fat_g": 0.2,
        "fiber_g": 2.4,
        "sugar_g": 10.4,
        "sodium_mg": 1,
        "saturated_fat_g": 0.0,
        "category": "fruit",
        "default_unit": "piece",
        "unit_weight_g": 182,
        "price_da": 250,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Pomme",
            "en": "Apple",
            "ar": "تفاح",
            "es": "Manzana",
        },
    },

    {
        "slug": "orange",
        "is_liquid": False,
        "calories_kcal": 47,
        "protein_g": 0.9,
        "carbs_g": 11.8,
        "fat_g": 0.1,
        "fiber_g": 2.4,
        "sugar_g": 9.4,
        "sodium_mg": 0,
        "saturated_fat_g": 0.0,
        "category": "fruit",
        "default_unit": "piece",
        "unit_weight_g": 130,
        "price_da": 220,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Orange",
            "en": "Orange",
            "ar": "برتقال",
            "es": "Naranja",
        },
    },

    {
        "slug": "dattes",
        "is_liquid": False,
        "calories_kcal": 282,
        "protein_g": 2.5,
        "carbs_g": 75.0,
        "fat_g": 0.4,
        "fiber_g": 8.0,
        "sugar_g": 63.0,
        "sodium_mg": 2,
        "saturated_fat_g": 0.0,
        "category": "fruit",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 450,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Dattes",
            "en": "Dates",
            "ar": "تمر",
            "es": "Dátiles",
        },
    },


    # ========================================================
    # LEGUMES
    # ========================================================

    {
        "slug": "tomate",
        "is_liquid": False,
        "calories_kcal": 18,
        "protein_g": 0.9,
        "carbs_g": 3.9,
        "fat_g": 0.2,
        "fiber_g": 1.2,
        "sugar_g": 2.6,
        "sodium_mg": 5,
        "saturated_fat_g": 0.0,
        "category": "vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 150,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Tomate",
            "en": "Tomato",
            "ar": "طماطم",
            "es": "Tomate",
        },
    },

    {
        "slug": "carotte",
        "is_liquid": False,
        "calories_kcal": 41,
        "protein_g": 0.9,
        "carbs_g": 9.6,
        "fat_g": 0.2,
        "fiber_g": 2.8,
        "sugar_g": 4.7,
        "sodium_mg": 69,
        "saturated_fat_g": 0.0,
        "category": "vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 120,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Carotte",
            "en": "Carrot",
            "ar": "جزر",
            "es": "Zanahoria",
        },
    },

    {
        "slug": "oignon",
        "is_liquid": False,
        "calories_kcal": 40,
        "protein_g": 1.1,
        "carbs_g": 9.3,
        "fat_g": 0.1,
        "fiber_g": 1.7,
        "sugar_g": 4.2,
        "sodium_mg": 4,
        "saturated_fat_g": 0.0,
        "category": "vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 100,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Oignon",
            "en": "Onion",
            "ar": "بصل",
            "es": "Cebolla",
        },
    },

    {
        "slug": "courgette",
        "is_liquid": False,
        "calories_kcal": 17,
        "protein_g": 1.2,
        "carbs_g": 3.1,
        "fat_g": 0.3,
        "fiber_g": 1.0,
        "sugar_g": 2.5,
        "sodium_mg": 8,
        "saturated_fat_g": 0.1,
        "category": "vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 160,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Courgette",
            "en": "Zucchini",
            "ar": "كوسة",
            "es": "Calabacín",
        },
    },

    {
        "slug": "salade",
        "is_liquid": False,
        "calories_kcal": 15,
        "protein_g": 1.4,
        "carbs_g": 2.9,
        "fat_g": 0.2,
        "fiber_g": 1.3,
        "sugar_g": 0.8,
        "sodium_mg": 28,
        "saturated_fat_g": 0.0,
        "category": "vegetables",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 120,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Salade verte",
            "en": "Lettuce",
            "ar": "خس",
            "es": "Lechuga",
        },
    },


    # ========================================================
    # MATIERES GRASSES / OLEAGINEUX
    # ========================================================

    {
        "slug": "huile_olive",
        "is_liquid": True,
        "calories_kcal": 884,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 100.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0,
        "saturated_fat_g": 14.0,
        "category": "oils",
        "default_unit": "ml",
        "unit_weight_g": None,
        "price_da": 900,
        "price_quantity": 1,
        "price_unit": "l",
        "translations": {
            "fr": "Huile d'olive",
            "en": "Olive oil",
            "ar": "زيت الزيتون",
            "es": "Aceite de oliva",
        },
    },

    {
        "slug": "huile_tournesol",
        "is_liquid": True,
        "calories_kcal": 884,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 100.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0,
        "saturated_fat_g": 10.0,
        "category": "oils",
        "default_unit": "ml",
        "unit_weight_g": None,
        "price_da": 220,
        "price_quantity": 1,
        "price_unit": "l",
        "translations": {
            "fr": "Huile de tournesol",
            "en": "Sunflower oil",
            "ar": "زيت دوار الشمس",
            "es": "Aceite de girasol",
        },
    },

    {
        "slug": "arachides",
        "is_liquid": False,
        "calories_kcal": 567,
        "protein_g": 25.8,
        "carbs_g": 16.1,
        "fat_g": 49.2,
        "fiber_g": 8.5,
        "sugar_g": 4.7,
        "sodium_mg": 18,
        "saturated_fat_g": 6.8,
        "category": "nuts",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 600,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Arachides",
            "en": "Peanuts",
            "ar": "فول سوداني",
            "es": "Cacahuetes",
        },
    },

    {
        "slug": "amandes",
        "is_liquid": False,
        "calories_kcal": 579,
        "protein_g": 21.2,
        "carbs_g": 21.6,
        "fat_g": 49.9,
        "fiber_g": 12.5,
        "sugar_g": 4.4,
        "sodium_mg": 1,
        "saturated_fat_g": 3.8,
        "category": "nuts",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 1800,
        "price_quantity": 1,
        "price_unit": "kg",
        "translations": {
            "fr": "Amandes",
            "en": "Almonds",
            "ar": "لوز",
            "es": "Almendras",
        },
    },


    # ========================================================
    # AUTRES
    # ========================================================

    {
        "slug": "miel",
        "is_liquid": True,
        "calories_kcal": 304,
        "protein_g": 0.3,
        "carbs_g": 82.4,
        "fat_g": 0.0,
        "fiber_g": 0.2,
        "sugar_g": 82.1,
        "sodium_mg": 4,
        "saturated_fat_g": 0.0,
        "category": "sweeteners",
        "default_unit": "g",
        "unit_weight_g": None,
        "price_da": 900,
        "price_quantity": 500,
        "price_unit": "g",
        "translations": {
            "fr": "Miel",
            "en": "Honey",
            "ar": "عسل",
            "es": "Miel",
        },
    },

]

# ============================================================
# EXTENSION DE LA FOOD DB
# ============================================================
# Aliments frequents dans les recettes externes. Les donnees sont exprimees
# pour 100 g (ou 100 ml pour les liquides). Les traductions EN/FR couvrent
# les formulations les plus courantes du mapper.


def _extra_food(
    slug, category, calories, protein, carbs, fat, fiber, sugar,
    sodium, saturated_fat, default_unit, price_da, price_quantity,
    price_unit, fr, en, unit_weight_g=None, is_liquid=False,
):
    return {
        "slug": slug,
        "is_liquid": is_liquid,
        "calories_kcal": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "sugar_g": sugar,
        "sodium_mg": sodium,
        "saturated_fat_g": saturated_fat,
        "category": category,
        "default_unit": default_unit,
        "unit_weight_g": unit_weight_g,
        "price_da": price_da,
        "price_quantity": price_quantity,
        "price_unit": price_unit,
        "translations": {"fr": fr, "en": en},
    }

FOODS.extend([
    # Aromates, epicerie et condiments
    _extra_food("ail", "vegetables", 149, 6.4, 33.1, 0.5, 2.1, 1.0, 17, 0.1, "piece", 600, 1, "kg", "Ail", "Garlic", 3),
    _extra_food("gingembre", "vegetables", 80, 1.8, 17.8, 0.8, 2.0, 1.7, 13, 0.2, "g", 700, 1, "kg", "Gingembre", "Ginger"),
    _extra_food("persil", "herbs", 36, 3.0, 6.3, 0.8, 3.3, 0.9, 56, 0.1, "g", 150, 100, "g", "Persil", "Parsley"),
    _extra_food("coriandre", "herbs", 23, 2.1, 3.7, 0.5, 2.8, 0.9, 46, 0.0, "g", 150, 100, "g", "Coriandre", "Cilantro"),
    _extra_food("sel", "condiments", 0, 0, 0, 0, 0, 0, 38758, 0, "g", 40, 1, "kg", "Sel", "Salt"),
    _extra_food("poivre_noir", "condiments", 251, 10.4, 63.9, 3.3, 25.3, 0.6, 20, 1.4, "g", 250, 100, "g", "Poivre noir", "Black pepper"),
    _extra_food("cumin", "spices", 375, 17.8, 44.2, 17.8, 10.5, 2.3, 168, 1.5, "g", 300, 100, "g", "Cumin", "Cumin"),
    _extra_food("paprika", "spices", 282, 14.1, 53.9, 12.9, 34.9, 10.3, 68, 2.1, "g", 300, 100, "g", "Paprika", "Paprika"),
    _extra_food("sauce_soja", "condiments", 53, 8.1, 4.9, 0.6, 0.8, 0.4, 5493, 0.1, "ml", 250, 150, "ml", "Sauce soja", "Soy sauce", is_liquid=True),
    _extra_food("vinaigre", "condiments", 18, 0, 0.9, 0, 0, 0.4, 5, 0, "ml", 120, 500, "ml", "Vinaigre", "Vinegar", is_liquid=True),

    # Legumes, feculents et proteines vegetales
    _extra_food("quinoa", "cereals", 368, 14.1, 64.2, 6.1, 7.0, 0, 5, 0.7, "g", 700, 500, "g", "Quinoa", "Quinoa"),
    _extra_food("patate_douce", "starchy_vegetables", 86, 1.6, 20.1, 0.1, 3.0, 4.2, 55, 0.0, "g", 180, 1, "kg", "Patate douce", "Sweet potato"),
    _extra_food("mais", "vegetables", 86, 3.3, 18.7, 1.4, 2.0, 6.3, 15, 0.2, "g", 180, 400, "g", "Maïs", "Corn"),
    _extra_food("tofu", "legumes", 76, 8.1, 0.9, 4.8, 0.3, 0.6, 7, 0.7, "g", 500, 400, "g", "Tofu", "Tofu"),
    _extra_food("farine", "flours", 364, 10.3, 76.3, 1.0, 2.7, 0.3, 2, 0.2, "g", 100, 1, "kg", "Farine", "All-purpose flour"),
    _extra_food("chapelure", "bakery", 395, 13.4, 71.2, 5.3, 4.5, 6.0, 732, 1.1, "g", 180, 500, "g", "Chapelure", "Breadcrumbs"),

    # Viandes, poissons et produits laitiers
    _extra_food("viande_hachee", "meat", 254, 17.2, 0, 20.0, 0, 0, 66, 7.7, "g", 1400, 1, "kg", "Viande hachée", "Ground beef"),
    _extra_food("dinde", "meat", 135, 29.0, 0, 1.6, 0, 0, 70, 0.4, "g", 900, 1, "kg", "Dinde", "Turkey"),
    _extra_food("saumon", "fish", 208, 20.4, 0, 13.4, 0, 0, 59, 3.1, "g", 1800, 1, "kg", "Saumon", "Salmon"),
    _extra_food("crevettes", "fish", 99, 24.0, 0.2, 0.3, 0, 0, 111, 0.1, "g", 1600, 1, "kg", "Crevettes", "Shrimp"),
    _extra_food("beurre", "dairy", 717, 0.9, 0.1, 81.1, 0, 0.1, 11, 51.4, "g", 250, 250, "g", "Beurre", "Butter"),
    _extra_food("mozzarella", "dairy", 280, 28.0, 3.1, 17.1, 0, 1.2, 627, 10.9, "g", 800, 250, "g", "Mozzarella", "Mozzarella"),
    _extra_food("parmesan", "dairy", 431, 38.5, 4.1, 29.0, 0, 0.9, 1529, 18.7, "g", 1200, 200, "g", "Parmesan", "Parmesan"),

    # Fruits, noix et sauces
    _extra_food("citron", "fruit", 29, 1.1, 9.3, 0.3, 2.8, 2.5, 2, 0.0, "piece", 250, 1, "kg", "Citron", "Lemon", 80),
    _extra_food("fraise", "fruit", 32, 0.7, 7.7, 0.3, 2.0, 4.9, 1, 0.0, "g", 500, 500, "g", "Fraise", "Strawberry"),
    _extra_food("noix", "nuts", 654, 15.2, 13.7, 65.2, 6.7, 2.6, 2, 6.1, "g", 1400, 500, "g", "Noix", "Walnuts"),
    _extra_food("beurre_cacahuete", "nuts", 588, 25.1, 20.0, 50.4, 6.0, 9.2, 476, 10.0, "g", 700, 350, "g", "Beurre de cacahuète", "Peanut butter"),
    _extra_food("lait_de_coco", "dairy_alternatives", 230, 2.3, 5.5, 23.8, 2.2, 3.3, 15, 21.1, "ml", 350, 400, "ml", "Lait de coco", "Coconut milk", is_liquid=True),
    _extra_food("sauce_tomate", "sauces", 29, 1.3, 5.1, 0.3, 1.5, 3.5, 316, 0.0, "g", 180, 400, "g", "Sauce tomate", "Tomato sauce"),
])

# ============================================================
# ELARGISSEMENT V2 : legumes, epicerie/patisserie, viandes
# supplementaires, condiments et articles explicitement non-halal.
# (couvre les manques frequents lors de l'import Wikibooks Cookbook)
# ============================================================

FOODS.extend([
    # Legumes
    _extra_food("aubergine", "vegetables", 25, 1.0, 5.9, 0.2, 3.0, 3.5, 2, 0.0, "g", 120, 1, "kg", "Aubergine", "Eggplant"),
    _extra_food("epinards", "vegetables", 23, 2.9, 3.6, 0.4, 2.2, 0.4, 79, 0.1, "g", 200, 1, "kg", "Épinards", "Spinach"),
    _extra_food("concombre", "vegetables", 15, 0.7, 3.6, 0.1, 0.5, 1.7, 2, 0.0, "g", 100, 1, "kg", "Concombre", "Cucumber"),
    _extra_food("poivron", "vegetables", 31, 1.0, 6.0, 0.3, 2.1, 4.2, 4, 0.0, "g", 200, 1, "kg", "Poivron", "Bell pepper"),
    _extra_food("champignon", "vegetables", 22, 3.1, 3.3, 0.3, 1.0, 2.0, 5, 0.0, "g", 500, 250, "g", "Champignon", "Mushroom", 20),
    _extra_food("chou", "vegetables", 25, 1.3, 5.8, 0.1, 2.5, 3.2, 18, 0.0, "g", 70, 1, "kg", "Chou", "Cabbage"),
    _extra_food("poireau", "vegetables", 61, 1.5, 14.2, 0.3, 1.8, 3.9, 20, 0.0, "g", 150, 1, "kg", "Poireau", "Leek"),
    _extra_food("brocoli", "vegetables", 34, 2.8, 6.6, 0.4, 2.6, 1.7, 33, 0.0, "g", 350, 1, "kg", "Brocoli", "Broccoli"),
    _extra_food("chou_fleur", "vegetables", 25, 1.9, 5.0, 0.3, 2.0, 1.9, 30, 0.1, "g", 150, 1, "kg", "Chou-fleur", "Cauliflower"),
    _extra_food("haricots_verts", "vegetables", 31, 1.8, 7.0, 0.2, 3.4, 3.3, 6, 0.0, "g", 250, 1, "kg", "Haricots verts", "Green beans"),
    _extra_food("petits_pois", "legumes", 81, 5.4, 14.5, 0.4, 5.7, 5.7, 5, 0.1, "g", 300, 1, "kg", "Petits pois", "Green peas"),
    _extra_food("oignon_vert", "vegetables", 32, 1.8, 7.3, 0.2, 2.6, 2.3, 16, 0.0, "g", 80, 1, "kg", "Oignon vert", "Green onion", 15),

    # Epicerie sucree / patisserie
    _extra_food("sucre", "sweeteners", 387, 0.0, 100.0, 0.0, 0.0, 100.0, 1, 0.0, "g", 130, 1, "kg", "Sucre", "Sugar"),
    _extra_food("cassonade", "sweeteners", 380, 0.1, 98.1, 0.0, 0.0, 97.0, 28, 0.0, "g", 280, 500, "g", "Cassonade", "Brown sugar"),
    _extra_food("levure_chimique", "baking", 53, 0.0, 27.7, 0.0, 0.2, 0.0, 10600, 0.0, "g", 60, 100, "g", "Levure chimique", "Baking powder"),
    _extra_food("bicarbonate", "baking", 0, 0.0, 0.0, 0.0, 0.0, 0.0, 27360, 0.0, "g", 80, 200, "g", "Bicarbonate de soude", "Baking soda"),
    _extra_food("levure_boulangere", "baking", 325, 40.4, 41.2, 7.6, 26.9, 0.0, 51, 1.3, "g", 50, 100, "g", "Levure boulangère", "Baker's yeast"),
    _extra_food("cacao", "baking", 228, 19.6, 57.9, 13.7, 37.0, 1.8, 21, 8.1, "g", 400, 200, "g", "Cacao en poudre", "Cocoa powder"),
    _extra_food("chocolat_noir", "sweets", 598, 7.8, 45.9, 42.6, 10.9, 24.0, 20, 24.5, "g", 600, 200, "g", "Chocolat noir", "Dark chocolate"),
    _extra_food("noix_coco_rapee", "nuts", 660, 6.9, 23.7, 64.5, 16.3, 7.4, 37, 57.2, "g", 350, 200, "g", "Noix de coco râpée", "Shredded coconut"),
    _extra_food("raisins_secs", "fruit", 299, 3.1, 79.2, 0.5, 3.7, 59.2, 11, 0.1, "g", 500, 1, "kg", "Raisins secs", "Raisins"),
    _extra_food("vanille", "spices", 288, 0.1, 12.7, 0.1, 0.0, 12.7, 9, 0.0, "ml", 300, 50, "ml", "Extrait de vanille", "Vanilla extract", is_liquid=True),
    _extra_food("maizena", "flours", 381, 0.3, 91.3, 0.1, 0.9, 0.0, 9, 0.0, "g", 200, 400, "g", "Maïzena", "Cornstarch"),

    # Herbes et epices supplementaires
    _extra_food("feuille_laurier", "spices", 313, 7.6, 74.9, 8.4, 26.3, 0.0, 23, 2.3, "g", 100, 10, "g", "Feuille de laurier", "Bay leaf", 1),
    _extra_food("origan", "herbs", 265, 9.0, 68.9, 4.3, 42.5, 4.1, 25, 1.6, "g", 150, 20, "g", "Origan", "Oregano"),
    _extra_food("basilic", "herbs", 23, 3.2, 2.7, 0.6, 1.6, 0.3, 4, 0.0, "g", 120, 100, "g", "Basilic", "Basil"),
    _extra_food("cannelle", "spices", 247, 4.0, 80.6, 1.2, 53.1, 2.2, 10, 0.3, "g", 150, 50, "g", "Cannelle", "Cinnamon"),

    # Produits laitiers / sauces supplementaires
    _extra_food("creme_liquide", "dairy", 340, 2.1, 2.8, 36.1, 0.0, 2.9, 27, 22.5, "ml", 250, 200, "ml", "Crème liquide", "Heavy cream", is_liquid=True),
    _extra_food("creme_fraiche", "dairy", 292, 2.3, 3.4, 30.0, 0.0, 3.4, 32, 18.7, "g", 200, 200, "g", "Crème fraîche", "Sour cream"),
    _extra_food("cheddar", "dairy", 403, 25.0, 1.3, 33.3, 0.0, 0.5, 653, 21.0, "g", 900, 200, "g", "Cheddar", "Cheddar cheese"),
    _extra_food("mayonnaise", "sauces", 680, 1.0, 0.6, 75.0, 0.0, 0.6, 635, 11.7, "g", 350, 500, "g", "Mayonnaise", "Mayonnaise"),
    _extra_food("moutarde", "condiments", 66, 4.4, 5.8, 3.3, 3.3, 2.7, 1135, 0.2, "g", 250, 300, "g", "Moutarde", "Mustard"),
    _extra_food("ketchup", "condiments", 101, 1.2, 25.8, 0.2, 0.3, 21.3, 907, 0.0, "g", 280, 500, "g", "Ketchup", "Ketchup"),
    _extra_food("bouillon_cube", "condiments", 250, 8.0, 20.0, 15.0, 0.5, 2.0, 20000, 6.0, "piece", 100, 80, "g", "Cube de bouillon", "Stock cube", 10),

    # Viandes supplementaires (halal)
    _extra_food("cuisse_poulet", "meat", 209, 26.0, 0.0, 10.9, 0.0, 0.0, 84, 3.0, "g", 480, 1, "kg", "Cuisse de poulet", "Chicken thigh"),
    _extra_food("agneau", "meat", 258, 25.6, 0.0, 16.5, 0.0, 0.0, 72, 6.9, "g", 2200, 1, "kg", "Agneau", "Lamb"),

    # Articles explicitement NON-halal ou de statut incertain (regle 10 :
    # jamais suppose halal par defaut). Voir DEFAULT_HALAL_OVERRIDES plus bas.
    _extra_food("vin", "beverages", 85, 0.1, 2.6, 0.0, 0.0, 0.6, 4, 0.0, "ml", 1200, 750, "ml", "Vin", "Wine", is_liquid=True),
    _extra_food("bacon", "meat", 541, 37.0, 1.4, 42.0, 0.0, 0.0, 1717, 13.7, "g", 900, 200, "g", "Bacon", "Bacon"),
    _extra_food("jambon", "meat", 145, 21.0, 1.5, 5.5, 0.0, 1.5, 1203, 1.8, "g", 700, 200, "g", "Jambon", "Ham"),
    _extra_food("porc", "meat", 242, 27.3, 0.0, 14.0, 0.0, 0.0, 62, 5.1, "g", 1000, 1, "kg", "Porc", "Pork"),
    _extra_food("gelatine", "other", 335, 85.6, 0.0, 0.1, 0.0, 0.0, 127, 0.0, "g", 400, 100, "g", "Gélatine", "Gelatin"),
])

# ============================================================
# HALAL STATUS PAR DEFAUT
# ============================================================
# Regle 10 : ne jamais deviner "halal" a partir du nom seul. Ici,
# l'ensemble des aliments ci-dessus sont des produits de base courants
# (legumes, fruits, cereales, viandes usuelles en Algerie...) traites
# comme halal par defaut, SAUF la liste explicite ci-dessous (alcool,
# porc et derives, gelatine de source non precisee).

DEFAULT_HALAL_OVERRIDES: dict[str, HalalStatus] = {
    "vin": HalalStatus.NOT_HALAL,
    "bacon": HalalStatus.NOT_HALAL,
    "jambon": HalalStatus.NOT_HALAL,
    "porc": HalalStatus.NOT_HALAL,
    "gelatine": HalalStatus.UNKNOWN,
}

for _food_data in FOODS:
    _food_data.setdefault("halal_status", HalalStatus.HALAL)
    if _food_data["slug"] in DEFAULT_HALAL_OVERRIDES:
        _food_data["halal_status"] = DEFAULT_HALAL_OVERRIDES[_food_data["slug"]]

# ============================================================
# UTILITAIRE DECIMAL
# ============================================================

def decimal(value):
    """Convertit proprement les nombres en Decimal pour PostgreSQL."""
    return Decimal(str(value))


# ============================================================
# SEED
# ============================================================

def seed_foods():

    db = SessionLocal()

    created_foods = 0
    updated_foods = 0
    created_translations = 0
    updated_translations = 0
    created_prices = 0

    try:

        for data in FOODS:

            # ==================================================
            # 1. ALIMENT
            # ==================================================

            food = (
                db.query(Food)
                .filter(Food.slug == data["slug"])
                .first()
            )

            if food is None:

                food = Food(
                    slug=data["slug"],
                    is_liquid=data["is_liquid"],

                    halal_status=data["halal_status"],

                    calories_kcal=decimal(
                        data["calories_kcal"]
                    ),

                    protein_g=decimal(
                        data["protein_g"]
                    ),

                    carbs_g=decimal(
                        data["carbs_g"]
                    ),

                    fat_g=decimal(
                        data["fat_g"]
                    ),

                    fiber_g=(
                        decimal(data["fiber_g"])
                        if data["fiber_g"] is not None
                        else None
                    ),

                    sugar_g=(
                        decimal(data["sugar_g"])
                        if data["sugar_g"] is not None
                        else None
                    ),

                    sodium_mg=(
                        decimal(data["sodium_mg"])
                        if data["sodium_mg"] is not None
                        else None
                    ),

                    saturated_fat_g=(
                        decimal(data["saturated_fat_g"])
                        if data["saturated_fat_g"] is not None
                        else None
                    ),

                    category=data["category"],

                    default_unit=data["default_unit"],

                    unit_weight_g=(
                        decimal(data["unit_weight_g"])
                        if data.get("unit_weight_g") is not None
                        else None
                    ),
                )

                db.add(food)
                db.flush()

                created_foods += 1

            else:

                # ==================================================
                # Mise à jour
                # ==================================================

                food.is_liquid = data["is_liquid"]

                food.halal_status = data["halal_status"]

                food.calories_kcal = decimal(
                    data["calories_kcal"]
                )

                food.protein_g = decimal(
                    data["protein_g"]
                )

                food.carbs_g = decimal(
                    data["carbs_g"]
                )

                food.fat_g = decimal(
                    data["fat_g"]
                )

                food.fiber_g = (
                    decimal(data["fiber_g"])
                    if data["fiber_g"] is not None
                    else None
                )

                food.sugar_g = (
                    decimal(data["sugar_g"])
                    if data["sugar_g"] is not None
                    else None
                )

                food.sodium_mg = (
                    decimal(data["sodium_mg"])
                    if data["sodium_mg"] is not None
                    else None
                )

                food.saturated_fat_g = (
                    decimal(data["saturated_fat_g"])
                    if data["saturated_fat_g"] is not None
                    else None
                )

                food.category = data["category"]

                food.default_unit = data["default_unit"]

                food.unit_weight_g = (
                    decimal(data["unit_weight_g"])
                    if data.get("unit_weight_g") is not None
                    else None
                )

                updated_foods += 1


            # ==================================================
            # 2. TRADUCTIONS
            # ==================================================

            for language_code, name in data["translations"].items():

                translation = (
                    db.query(FoodTranslation)
                    .filter(
                        FoodTranslation.food_id == food.id,
                        FoodTranslation.language_code == language_code,
                    )
                    .first()
                )

                if translation is None:

                    translation = FoodTranslation(
                        food_id=food.id,
                        language_code=language_code,
                        name=name,
                    )

                    db.add(translation)

                    created_translations += 1

                else:

                    translation.name = name

                    updated_translations += 1


            # ==================================================
            # 3. PRIX
            # ==================================================

            price = (
                db.query(FoodPrice)
                .filter(
                    FoodPrice.food_id == food.id,
                    FoodPrice.is_active.is_(True),
                )
                .first()
            )

            if price is None:

                price = FoodPrice(
                    food_id=food.id,
                    price_da=decimal(data["price_da"]),
                    quantity=decimal(data["price_quantity"]),
                    unit=data["price_unit"],
                    is_active=True,
                )

                db.add(price)

                created_prices += 1

            else:

                price.price_da = decimal(
                    data["price_da"]
                )

                price.quantity = decimal(
                    data["price_quantity"]
                )

                price.unit = data["price_unit"]


        db.commit()


        # ========================================================
        # RESULTAT
        # ========================================================

        print("=" * 60)
        print("SEED FOODS TERMINE")
        print("=" * 60)

        print(
            f"Aliments créés       : {created_foods}"
        )

        print(
            f"Aliments mis à jour  : {updated_foods}"
        )

        print(
            f"Traductions créées   : {created_translations}"
        )

        print(
            f"Traductions mises à jour : {updated_translations}"
        )

        print(
            f"Prix créés           : {created_prices}"
        )

        print("=" * 60)


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    seed_foods()