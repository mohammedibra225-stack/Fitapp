"""
Traductions en 4 langues (fr, en, es, ar) pour l'ensemble des programmes, séances et exercices.
Couvre tous les profils (Combat, Musculation, Endurance, Sports collectifs, Sédentaire)
et toutes les adaptations d'objectifs (lose-fat, build-muscle, improve-performance, healthy-lifestyle).
"""

SESSION_NAME_TRANSLATIONS = {
    # 1. COMBAT
    "Initiation & conditionnement de base": {
        "fr": "Initiation & conditionnement de base",
        "en": "Initiation & basic conditioning",
        "es": "Iniciación y acondicionamiento básico",
        "ar": "المبتدئين واللياقة الأساسية",
    },
    "Agilité & cardio doux": {
        "fr": "Agilité & cardio doux",
        "en": "Agility & low-impact cardio",
        "es": "Agilidad y cardio suave",
        "ar": "الرشاقة وتمارين الكارديو الخفيفة",
    },
    "Cardio-musculaire & light sparring": {
        "fr": "Cardio-musculaire & light sparring",
        "en": "Cardio-muscular & light sparring",
        "es": "Cardio-muscular y combate ligero",
        "ar": "كارديو-عضلي وملاكمة خفيفة",
    },
    "Lower body & simulation combat": {
        "fr": "Lower body & simulation combat",
        "en": "Lower body & fight simulation",
        "es": "Tren inferior y simulación de combate",
        "ar": "الجزء السفلي ومحاكاة القتال",
    },
    "Musculation, agilité & flexibilité": {
        "fr": "Musculation, agilité & flexibilité",
        "en": "Strength, agility & flexibility",
        "es": "Fuerza, agilidad y flexibilidad",
        "ar": "القوة، الرشاقة والمرونة",
    },
    "Pliométrie & puissance": {
        "fr": "Pliométrie & puissance",
        "en": "Plyometrics & explosive power",
        "es": "Pliometría y potencia",
        "ar": "تمارين البليومتريك والقوة الانفجارية",
    },
    "Force lourde": {
        "fr": "Force lourde",
        "en": "Heavy strength",
        "es": "Fuerza pesada",
        "ar": "تمارين القوة الثقيلة",
    },
    "Sparring & haute intensité": {
        "fr": "Sparring & haute intensité",
        "en": "High-intensity sparring",
        "es": "Combate y alta intensidad",
        "ar": "نزال تدريبي وكثافة عالية",
    },
    "Mobilité profonde & prévention": {
        "fr": "Mobilité profonde & prévention",
        "en": "Deep mobility & injury prevention",
        "es": "Movilidad profunda y prevención",
        "ar": "المرونة العميقة والوقاية من الإصابات",
    },
    "Récupération active": {
        "fr": "Récupération active",
        "en": "Active recovery",
        "es": "Recuperación activa",
        "ar": "التعافي النشط",
    },

    # 2. MUSCULATION
    "Full-Body A": {
        "fr": "Full-Body A",
        "en": "Full-Body A",
        "es": "Cuerpo Completo A",
        "ar": "كامل الجسم (أ)",
    },
    "Full-Body B": {
        "fr": "Full-Body B",
        "en": "Full-Body B",
        "es": "Cuerpo Completo B",
        "ar": "كامل الجسم (ب)",
    },
    "Full-Body C": {
        "fr": "Full-Body C",
        "en": "Full-Body C",
        "es": "Cuerpo Completo C",
        "ar": "كامل الجسم (ج)",
    },
    "Upper (haut du corps)": {
        "fr": "Upper (haut du corps)",
        "en": "Upper Body",
        "es": "Tren superior",
        "ar": "الجزء العلوي من الجسم",
    },
    "Lower (bas du corps)": {
        "fr": "Lower (bas du corps)",
        "en": "Lower Body",
        "es": "Tren inferior",
        "ar": "الجزء السفلي من الجسم",
    },
    "Push (poussée)": {
        "fr": "Push (poussée)",
        "en": "Push",
        "es": "Empuje (Push)",
        "ar": "تمارين الدفع (Push)",
    },
    "Pull (tirage)": {
        "fr": "Pull (tirage)",
        "en": "Pull",
        "es": "Tracción (Pull)",
        "ar": "تمارين السحب (Pull)",
    },
    "Legs (jambes)": {
        "fr": "Legs (jambes)",
        "en": "Legs",
        "es": "Piernas (Legs)",
        "ar": "تمارين الأرجل (Legs)",
    },
    "Cardio / mobilité légère": {
        "fr": "Cardio / mobilité légère",
        "en": "Cardio / light mobility",
        "es": "Cardio / movilidad ligera",
        "ar": "كارديو ومرونة خفيفة",
    },

    # 3. ENDURANCE
    "VMA / fractionné (HIIT)": {
        "fr": "VMA / fractionné (HIIT)",
        "en": "Interval training (HIIT)",
        "es": "Entrenamiento a intervalos (HIIT)",
        "ar": "التدريب المتقطع عالي الكثافة (HIIT)",
    },
    "PPG & renforcement spécifique endurance": {
        "fr": "PPG & renforcement spécifique endurance",
        "en": "Specific strength & conditioning for endurance",
        "es": "Acondicionamiento y fuerza para resistencia",
        "ar": "اللياقة العامة وتقوية التحمل",
    },
    "Sortie longue (Zone 2)": {
        "fr": "Sortie longue (Zone 2)",
        "en": "Long endurance session (Zone 2)",
        "es": "Sesión larga de resistencia (Zona 2)",
        "ar": "تمرين التحمل الطويل (المنطقة 2)",
    },
    "Sortie au seuil": {
        "fr": "Sortie au seuil",
        "en": "Threshold training",
        "es": "Entrenamiento de umbral",
        "ar": "تمرين عتبة الجهد",
    },
    "Mobilité & étirements profonds": {
        "fr": "Mobilité & étirements profonds",
        "en": "Mobility & deep stretches",
        "es": "Movilidad y estiramientos profundos",
        "ar": "المرونة والاستطالة العميقة",
    },

    # 4. FOOTBALL & COLLECTIFS
    "Vitesse, explosivité & agilité (PMA)": {
        "fr": "Vitesse, explosivité & agilité (PMA)",
        "en": "Speed, explosiveness & agility",
        "es": "Velocidad, explosividad y agilidad",
        "ar": "السرعة، القوة الانفجارية والرشاقة",
    },
    "Musculation de prévention des blessures": {
        "fr": "Musculation de prévention des blessures",
        "en": "Injury prevention strength training",
        "es": "Entrenamiento de prevención de lesiones",
        "ar": "تمارين القوة للوقاية من الإصابات",
    },
    "Match ou simulation haute intensité": {
        "fr": "Match ou simulation haute intensité",
        "en": "Match or high-intensity match play",
        "es": "Partido o simulación de alta intensidad",
        "ar": "مباراة أو محاكاة عالية الكثافة",
    },
    "Entraînement terrain / tactique": {
        "fr": "Entraînement terrain / tactique",
        "en": "Field & tactical training",
        "es": "Entrenamiento de campo y táctico",
        "ar": "تدريب ميداني وتكتيكي",
    },

    # 5. SÉDENTAIRE
    "Mobilité & mouvement doux": {
        "fr": "Mobilité & mouvement doux",
        "en": "Gentle mobility & movement",
        "es": "Movilidad y movimiento suave",
        "ar": "المرونة والحركة اللطيفة",
    },
    "Renforcement au poids du corps (adapté)": {
        "fr": "Renforcement au poids du corps (adapté)",
        "en": "Adapted bodyweight strengthening",
        "es": "Fortalecimiento con peso corporal adaptado",
        "ar": "تقوية بوزن الجسم بطريقة ميسرة",
    },
    "Full-body élastiques / léger": {
        "fr": "Full-body élastiques / léger",
        "en": "Light / resistance band full-body",
        "es": "Cuerpo completo con gomas / ligero",
        "ar": "كامل الجسم بالأشرطة المطاطية أو أوزان خفيفة",
    },
    "Renforcement fonctionnel poids du corps": {
        "fr": "Renforcement fonctionnel poids du corps",
        "en": "Functional bodyweight strength",
        "es": "Fuerza funcional con peso corporal",
        "ar": "تقوية وظيفية بوزن الجسم",
    },
    "Cardio polyvalent": {
        "fr": "Cardio polyvalent",
        "en": "Versatile cardio",
        "es": "Cardio polivalente",
        "ar": "تمارين كارديو متعددة الاستخدامات",
    },
    "Mobilité & étirements": {
        "fr": "Mobilité & étirements",
        "en": "Mobility & stretching",
        "es": "Movilidad y estiramientos",
        "ar": "المرونة والاستطالة",
    },
}

def translate_session_name(name: str, language: str = "fr") -> str:
    if not name:
        return name
    item = SESSION_NAME_TRANSLATIONS.get(name)
    if not item:
        return name
    return item.get(language) or item.get("en") or name
