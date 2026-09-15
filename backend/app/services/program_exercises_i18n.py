"""
Catalogue complet multilingue (FR, EN, ES, AR) pour tous les exercices du répertoire Fitapp.
Fournit le dictionnaire 4 langues pour chaque exercice du système afin d'alimenter seed_sports.py.
"""

EXERCISE_I18N = {
    # ------------------------------------------------------------
    # 1. COMBAT & CONTACT
    # ------------------------------------------------------------
    "rotations_poignets_chevilles": {
        "fr": ("Rotations poignets et chevilles", "Mobilisation articulaire légère en échauffement."),
        "en": ("Wrist and ankle circles", "Light joint mobility used as a warm-up."),
        "es": ("Rotaciones de muñecas y tobillos", "Movilización articular ligera como calentamiento."),
        "ar": ("دوران المعصمين والكاحلين", "تحريك لطيف للمفاصل كإحماء."),
    },
    "directs_jab_cross": {
        "fr": ("Directs jab/cross en déplacement", "Coups directs en avançant, reculant et pivotant."),
        "en": ("Jab/cross on the move", "Straight punches while stepping and pivoting."),
        "es": ("Directos jab/cross en desplazamiento", "Golpes directos avanzando, retrocediendo y pivotando."),
        "ar": ("لكمات مستقيمة جاب/كروس أثناء الحركة", "لكمات أمامية مستقيمة مع التقدم، الرجوع والالتفاف."),
    },
    "pompes_genoux": {
        "fr": ("Pompes sur les genoux", "Pompes adaptées, genoux au sol."),
        "en": ("Knee push-ups", "Regressed push-up with knees on the floor."),
        "es": ("Flexiones sobre rodillas", "Flexiones adaptadas con rodillas en el suelo."),
        "ar": ("تمرين الضغط على الركبتين", "ضغط ميسر بوضع الركبتين على الأرض."),
    },
    "squats_poids_corps": {
        "fr": ("Squats au poids du corps", "Flexions de jambes sans charge."),
        "en": ("Bodyweight squats", "Unloaded squat pattern."),
        "es": ("Sentadillas con peso corporal", "Flexiones de piernas sin peso añadido."),
        "ar": ("سكوات بوزن الجسم", "ثني الركبتين دون أوزان إضافية."),
    },
    "gainage_coudes": {
        "fr": ("Gainage frontal sur les coudes", "Planche basse, alignement tête-bassin-talons."),
        "en": ("Forearm plank", "Low plank holding a straight body line."),
        "es": ("Plancha frontal sobre antebrazos", "Plancha baja alineando cabeza, pelvis y talones."),
        "ar": ("لوح بلانك على الساعدين", "بلانك منخفض مع استقامة الرأس، الحوض والكعبين."),
    },
    "pas_chasses_croises": {
        "fr": ("Pas chassés et pas croisés", "Déplacements latéraux sur échelle ou cônes."),
        "en": ("Shuffle and crossover steps", "Lateral footwork on a ladder or cones."),
        "es": ("Pasos laterales y cruzados", "Desplazamientos laterales en escalera o conos."),
        "ar": ("خطوات جانبية ومتقاطعة", "حركات قدم جانبية على سلم الرشاقة أو الأقماع."),
    },
    "birddog": {
        "fr": ("Bird dog", "Extension opposée bras/jambe à quatre pattes."),
        "en": ("Bird dog", "Opposite arm and leg reach from quadruped."),
        "es": ("Bird dog", "Extensión opuesta de brazo y pierna en cuadrupedia."),
        "ar": ("تمرين بيرد دوج", "مد الذراع والساق المعاكسة في وضعية الأربع أطراف."),
    },
    "thrusters": {
        "fr": ("Thrusters", "Squat + développé explosif en un seul mouvement."),
        "en": ("Thrusters", "Squat into an explosive overhead press."),
        "es": ("Thrusters", "Sentadilla y press sobre la cabeza en un solo movimiento."),
        "ar": ("تمرين ثروسترز", "سكوات متبوع بدفع علوي انفجاري في حركة واحدة."),
    },
    "slam_ball": {
        "fr": ("Slam ball", "Lancer violent du ballon au sol, toute la chaîne."),
        "en": ("Slam ball", "Explosive overhead slam into the floor."),
        "es": ("Slam ball", "Lanzamiento explosivo del balón medicinal al suelo."),
        "ar": ("رمي الكرة الطبية بقوة (سلام بول)", "رمي انفجاري للكرة الطبية على الأرض بكامل الجسم."),
    },
    "pompes_explosives": {
        "fr": ("Pompes explosives", "Poussée rapide jusqu'à décoller les mains."),
        "en": ("Explosive push-ups", "Fast press until the hands leave the floor."),
        "es": ("Flexiones explosivas", "Empuje rápido despegando las manos del suelo."),
        "ar": ("ضغط انفجاري", "دفع سريع وقوي حتى ترتفع اليدان عن الأرض."),
    },
    "gainage_dynamique": {
        "fr": ("Gainage dynamique", "Planche avec mouvements contrôlés du tronc."),
        "en": ("Dynamic plank", "Plank with controlled torso movement."),
        "es": ("Plancha dinámica", "Plancha con movimientos controlados del tronco."),
        "ar": ("بلانك ديناميكي", "تمرين لوح مع حركات تحكم في الجذع."),
    },
    "light_sparring_paos": {
        "fr": ("Light sparring / travail aux paos", "Échanges contrôlés ou frappes sur cibles."),
        "en": ("Light sparring / pad work", "Controlled exchanges or pad striking."),
        "es": ("Sparring ligero / trabajo con manoplas", "Intercambios controlados o golpeo a objetivos."),
        "ar": ("ملاكمة خفيفة / تدريب على واقيات اللكم", "تبادلات تدريبية مضبوطة أو ضربات على الأهداف."),
    },
    "goblet_squat": {
        "fr": ("Goblet squat", "Squat tenu devant la poitrine, haltère ou kettlebell."),
        "en": ("Goblet squat", "Squat holding a weight at chest height."),
        "es": ("Goblet squat", "Sentadilla sujetando la carga frente al pecho."),
        "ar": ("جوبلت سكوات", "سكوات مع إمساك الوزن أمام الصدر."),
    },
    "sauts_verticaux": {
        "fr": ("Sauts verticaux", "Détente verticale maximale, réception souple."),
        "en": ("Vertical jumps", "Maximal vertical jump with a soft landing."),
        "es": ("Saltos verticales", "Salto vertical máximo con aterrizaje suave."),
        "ar": ("قفزات عمودية", "أقصى قفزة عمودية مع هبوط مرن."),
    },
    "broad_jumps": {
        "fr": ("Broad jumps", "Sauts en longueur sans élan, hanches explosives."),
        "en": ("Broad jumps", "Standing long jumps driven by the hips."),
        "es": ("Saltos de longitud sin impulso", "Salto horizontal explosivo impulsado por caderas."),
        "ar": ("قفزات طويلة أفقية (برود جمب)", "قفز طويل من الثبات بقوة الوركين."),
    },
    "rdl_roumain": {
        "fr": ("Soulevé de terre roumain", "Charnière de hanche, ischios et fessiers."),
        "en": ("Romanian deadlift", "Hip hinge targeting hamstrings and glutes."),
        "es": ("Peso muerto rumano", "Bisagra de cadera para isquiotibiales y glúteos."),
        "ar": ("ديدليفت روماني (RDL)", "حركة مفصل الورك لاستهداف أوتار الركبة والأرداف."),
    },
    "glute_bridge": {
        "fr": ("Pont fessier", "Extension de hanche au sol, fessiers serrés en haut."),
        "en": ("Glute bridge", "Hip extension on the floor, squeeze at the top."),
        "es": ("Puente de glúteos", "Extensión de cadera en el suelo apretando glúteos."),
        "ar": ("جسر الأرداف (جلوت بريدج)", "تمديد الورك على الأرض مع شد عضلات الأرداف في الأعلى."),
    },
    "rounds_shadow_lutte_sac": {
        "fr": ("Rounds shadow / lutte / sac / sprawls", "Simulation de combat en rounds mixtes."),
        "en": ("Shadow, clinch, bag and sprawl rounds", "Mixed fight-simulation rounds."),
        "es": ("Rounds de sombra / lucha / saco / sprawls", "Simulación de combate en asaltos mixtos."),
        "ar": ("جولات شادو / مصارعة / كيس / سبرول", "محاكاة قتالية في جولات تدريبية مختلطة."),
    },
    "box_jumps": {
        "fr": ("Box jumps", "Sauts sur une box, réception stable."),
        "en": ("Box jumps", "Jump onto a box and stick the landing."),
        "es": ("Saltos al cajón", "Salto sobre cajón pliométrico con aterrizaje estable."),
        "ar": ("القفز على الصندوق (بوكس جمب)", "قفز على الصندوق مع ثبات وتوازن عند الهبوط."),
    },
    "depth_jumps": {
        "fr": ("Depth jumps", "Saut en contrebas puis rebond vertical immédiat."),
        "en": ("Depth jumps", "Drop from a box then rebound into a vertical jump."),
        "es": ("Depth jumps", "Caída desde cajón y rebote vertical explosivo inmediato."),
        "ar": ("قفزات الهبوط والارتداد (ديبث جمب)", "هبوط من منصة مع ارتداد عمودي انفجاري فوري."),
    },
    "medball_chest_pass": {
        "fr": ("Chest pass médecine-ball contre mur", "Poussée explosive des pectoraux et des triceps."),
        "en": ("Medicine-ball chest pass", "Explosive chest pass into a wall."),
        "es": ("Pase de pecho con balón medicinal contra pared", "Empuje explosivo de pectorales y tríceps."),
        "ar": ("تمريرة الصدر بالكرة الطبية على الجدار", "دفع انفجاري من الصدر لعضلات الصدر والترايسبس."),
    },
    "pompes_clappees": {
        "fr": ("Pompes clappées", "Pompe plyométrique avec claquement des mains."),
        "en": ("Clapping push-ups", "Plyometric push-up with a clap."),
        "es": ("Flexiones con palmada", "Flexión pliométrica con palmada en el aire."),
        "ar": ("ضغط مع تصفيق", "ضغط بليومتري متفجر مع تصفيق اليدين في الهواء."),
    },
    "landmine_press": {
        "fr": ("Landmine press explosif", "Développé unilatéral explosif sur barre pivot."),
        "en": ("Explosive landmine press", "One-arm explosive press on a landmine."),
        "es": ("Press landmine explosivo", "Empuje unilateral explosivo con barra pivotante."),
        "ar": ("دفع لاندماين انفجاري", "دفع انفجاري بذراع واحدة على طرف البار المرتكز."),
    },
    "landmine_rotations": {
        "fr": ("Landmine rotations", "Rotations du tronc contre résistance."),
        "en": ("Landmine rotations", "Resisted torso rotations."),
        "es": ("Rotaciones landmine", "Rotaciones del torso contra resistencia con barra."),
        "ar": ("دوران لاندماين للجذع", "حركات دوران للجذع ضد مقاومة البار."),
    },
    "tractions_lestees": {
        "fr": ("Tractions lestées", "Tractions avec charge additionnelle."),
        "en": ("Weighted pull-ups", "Pull-ups with added load."),
        "es": ("Dominadas lastradas", "Dominadas con peso adicional."),
        "ar": ("عقلة بأوزان إضافية", "تمرين العقلة مع إضافة أوزان."),
    },
    "sparring_intensif": {
        "fr": ("Sparring haute intensité", "Rounds à intensité réelle, 5x3 min ou 3x5 min."),
        "en": ("High-intensity sparring", "Live rounds, 5x3 min or 3x5 min."),
        "es": ("Sparring de alta intensidad", "Asaltos a intensidad real, 5x3 min o 3x5 min."),
        "ar": ("نزال تدريبي عالي الكثافة", "جولات بكثافة قتالية حقيقية، 5×3 د أو 3×5 د."),
    },
    "sprawls_burpees": {
        "fr": ("Sprawls / burpees à épuisement", "Finisseur de combat jusqu'à fatigue."),
        "en": ("Sprawls / burpees to fatigue", "Fight finisher taken near exhaustion."),
        "es": ("Sprawls / burpees hasta el agotamiento", "Finalizador de combate hasta la fatiga."),
        "ar": ("سبرول وبيربي حتى الإنهاك", "تمرين ختامي قتالي عالي الإجهاد حتى التعب."),
    },
    "t_spine_mobility": {
        "fr": ("Mobilité thoracique (T-spine)", "Rotations et extensions de la cage thoracique."),
        "en": ("T-spine mobility", "Thoracic rotations and extensions."),
        "es": ("Movilidad torácica (T-spine)", "Rotaciones y extensiones de la columna torácica."),
        "ar": ("مرونة العمود الفقري الصدري", "حركات دوران وتمديد للقفص الصدري."),
    },
    "cervicales_bande": {
        "fr": ("Renforcement cervicales avec bande", "Résistance légère pour la nuque."),
        "en": ("Banded neck strengthening", "Light band resistance for the neck."),
        "es": ("Fortalecimiento cervical con banda", "Resistencia ligera con banda para el cuello."),
        "ar": ("تقوية عضلات الرقبة بالأشرطة", "مقاومة خفيفة بالشريط المطاطي لحماية وتقوية الرقبة."),
    },
    "coiffe_rotateurs": {
        "fr": ("Travail de la coiffe des rotateurs", "Rotations externes contrôlées, bande ou haltères légers."),
        "en": ("Rotator cuff work", "Controlled external rotations with a light band."),
        "es": ("Trabajo del manguito rotador", "Rotaciones externas controladas con banda o mancuernas."),
        "ar": ("تمارين الكفة المدورة للكتف", "دوران خارجي متحكم به بالشريط أو بأثقال خفيفة."),
    },
    "isometrie_grand_ecart": {
        "fr": ("Isométrie sur grand écart", "Maintiens longs pour ouvrir les hanches."),
        "en": ("Splits isometric holds", "Long holds to open the hips."),
        "es": ("Isometría en apertura de piernas (spagat)", "Mantenimiento estático prolongado para abrir caderas."),
        "ar": ("ثبات متساوي القياس في فتح الحوض", "ثبات طويل لفتح مفاصل الحوض والمرونة."),
    },

    # ------------------------------------------------------------
    # 2. MUSCULATION & FITNESS
    # ------------------------------------------------------------
    "developpe_militaire_halteres": {
        "fr": ("Développé militaire haltères", "Poussée verticale unilatérale plus naturelle pour les épaules."),
        "en": ("Dumbbell overhead press", "Vertical press with a more natural shoulder path."),
        "es": ("Press militar con mancuernas", "Empuje vertical con trayectoria natural para los hombros."),
        "ar": ("ضغط كتف عسكري بالدمبلز", "دفع عمودي علوي بمسار مريح للكتفين."),
    },
    "russian_twists": {
        "fr": ("Russian twists", "Rotations du buste assis, charge optionnelle."),
        "en": ("Russian twists", "Seated torso rotations, optional load."),
        "es": ("Giros rusos", "Rotaciones de tronco sentado con o sin peso."),
        "ar": ("التفاف روسي (روسيان تويست)", "دوران الجذع أثناء الجلوس مع وزن اختياري."),
    },
    "fentes_bulgares": {
        "fr": ("Fentes bulgares haltères", "Fente arrière pied surélevé, une jambe à la fois."),
        "en": ("Bulgarian split squats", "Rear-foot elevated split squat."),
        "es": ("Sentadilla búlgara con mancuernas", "Zancada con el pie trasero elevado."),
        "ar": ("سكوات بلغاري بالدمبلز", "سكوات برجل واحدة مع رفع القدم الخلفية."),
    },
    "tirage_vertical": {
        "fr": ("Tirage vertical poulie haute", "Grand dorsal en traction guidée."),
        "en": ("Lat pulldown", "Guided vertical pull for the lats."),
        "es": ("Jalón al pecho en polea alta", "Tracción vertical guiada para dorsales."),
        "ar": ("سحب علوي عريض بالكيبل", "سحب عمودي موجه لعضلات الظهر العريضة."),
    },
    "tractions_supination": {
        "fr": ("Tractions supination", "Prise inversée, dos et biceps."),
        "en": ("Chin-ups", "Supinated pull-ups for back and biceps."),
        "es": ("Dominadas supinas", "Agarre en supinación enfocado en dorsales y bíceps."),
        "ar": ("عقلة قبضة معكوسة (تشين أب)", "عقلة بقبضة متجهة للداخل للظهر والبايسبس."),
    },
    "souleve_terre_jambes_tendues": {
        "fr": ("Soulevé de terre jambes tendues", "Ischios en charnière, genoux souples."),
        "en": ("Stiff-leg deadlift", "Hamstring hinge with soft knees."),
        "es": ("Peso muerto piernas rígidas", "Bisagra enfocada en isquiotibiales con rodillas suaves."),
        "ar": ("ديدليفت بأرجل شبه مستقيمة", "تركيز على أوتار الركبة مع ثني خفيف جداً."),
    },
    "leg_extension": {
        "fr": ("Leg extension", "Isolation des quadriceps à la machine."),
        "en": ("Leg extension", "Quad isolation on the machine."),
        "es": ("Extensión de cuádriceps", "Aislamiento de cuádriceps en máquina."),
        "ar": ("مد الساقين بالجهاز (ليج إكستنشن)", "عزل عضلات الفخذ الأمامية على الجهاز."),
    },
    "mollets_debout": {
        "fr": ("Mollets debout", "Élévations sur la pointe des pieds."),
        "en": ("Standing calf raises", "Plantar flexion under load."),
        "es": ("Elevaciones de gemelos de pie", "Elevación sobre las puntas de los pies."),
        "ar": ("رفع السمانة واقفاً", "رفع الجسم على أطراف أصابع القدمين."),
    },
    "ecartes_poulie": {
        "fr": ("Écartés poulie vis-à-vis", "Étirement et contraction des pectoraux."),
        "en": ("Cable flyes", "Chest stretch and squeeze on cables."),
        "es": ("Cruces en polea", "Aperturas en polea para estiramiento y contracción pectoral."),
        "ar": ("تجميع الصدر بالكيبل (كيبل فلاي)", "تمديد وعصر عضلات الصدر بواسطة الكيبل."),
    },
    "elevations_laterales_cable": {
        "fr": ("Élévations latérales câble", "Deltoïde moyen sous tension continue."),
        "en": ("Cable lateral raises", "Side delts under constant tension."),
        "es": ("Elevaciones laterales en polea", "Deltoides laterales bajo tensión constante."),
        "ar": ("رفرفة جانبية بالكيبل", "عزل عضلة الكتف الجانبية تحت توتر مستمر."),
    },
    "extension_triceps_overhead": {
        "fr": ("Extensions triceps au-dessus de la tête", "Longue portion du triceps."),
        "en": ("Overhead triceps extension", "Long-head triceps emphasis."),
        "es": ("Extensión de tríceps sobre la cabeza", "Énfasis en la porción larga del tríceps."),
        "ar": ("تمديد الترايسبس فوق الرأس", "تركيز على الرأس الطويل لعضلة الترايسبس."),
    },
    "rowing_unilateral": {
        "fr": ("Rowing unilatéral haltère", "Tirage un bras, dos épais et stable."),
        "en": ("Single-arm dumbbell row", "Unilateral row for thickness and stability."),
        "es": ("Remo unilateral con mancuerna", "Remo a un brazo para densidad de espalda."),
        "ar": ("تجديف دمبل بذراع واحدة", "سحب أحادي لزيادة كثافة وقوة الظهر."),
    },
    "tirage_poitrine_prise_serree": {
        "fr": ("Tirage poitrine prise serrée", "Milieu du dos et biceps."),
        "en": ("Close-grip chest-supported row", "Mid-back and biceps focus."),
        "es": ("Remo con agarre cerrado apoyado en pecho", "Espalda media y bíceps."),
        "ar": ("تجديف قبضة ضيقة مسنود على الصدر", "تركيز على منتصف الظهر وعضلات البايسبس."),
    },
    "oiseau_halteres": {
        "fr": ("Oiseau haltères", "Arrière d'épaule, buste penché."),
        "en": ("Rear-delt flyes", "Bent-over rear deltoid raises."),
        "es": ("Pájaros con mancuernas", "Elevaciones posteriores para deltoides trasero."),
        "ar": ("رفرفة خلفية للكتف بالدمبلز", "عزل الكتف الخلفي مع انحناء الجذع للأمام."),
    },
    "curl_ez": {
        "fr": ("Curl barre EZ", "Biceps avec prise plus confortable pour les poignets."),
        "en": ("EZ-bar curl", "Biceps curl with a wrist-friendly grip."),
        "es": ("Curl con barra EZ", "Curl de bíceps con agarre ergonómico."),
        "ar": ("كيرل البايسبس بالبار الزكزاك (EZ)", "ثني البايسبس بقبضة مريحة ومحمية للمعصمين."),
    },
    "curl_marteau": {
        "fr": ("Curl marteau", "Brachial et avant-bras, haltères neutres."),
        "en": ("Hammer curl", "Neutral-grip curl for brachialis and forearms."),
        "es": ("Curl martillo", "Agarre neutro para braquial y antebrazos."),
        "ar": ("كيرل المطرقة (هامر كيرل)", "قبضة محايدة لاستهداف البراكياليس والساعدين."),
    },
    "squat_profond": {
        "fr": ("Squat profond", "Flexion complète, dos gainé."),
        "en": ("Deep squat", "Full-depth squat with a braced torso."),
        "es": ("Sentadilla profunda", "Flexión completa manteniendo el torso firme."),
        "ar": ("سكوات عميق", "نزول كامل مع ثبات واستقامة الظهر."),
    },
    "hip_thrust": {
        "fr": ("Hip thrust à la barre", "Extension de hanche lourde pour les fessiers."),
        "en": ("Barbell hip thrust", "Heavy hip extension for the glutes."),
        "es": ("Hip thrust con barra", "Extensión pesada de cadera para glúteos."),
        "ar": ("هيب ثرست بالبار", "تمديد الورك بالأوزان لبناء وتقوية الأرداف."),
    },
    "leg_curl_assis": {
        "fr": ("Leg curl assis", "Ischios en isolation, hanche fléchie."),
        "en": ("Seated leg curl", "Hamstring isolation with a flexed hip."),
        "es": ("Curl femoral sentado", "Aislamiento de isquiotibiales sentado en máquina."),
        "ar": ("ثني الساقين جالساً (ليج كيرل)", "عزل أوتار الركبة على الجهاز في وضعية الجلوس."),
    },
    "mollets_presse": {
        "fr": ("Mollets à la presse", "Mollets sous charge guidée."),
        "en": ("Leg-press calf raises", "Calves under a guided load."),
        "es": ("Elevación de gemelos en prensa", "Gemelos bajo carga guiada en prensa."),
        "ar": ("رفع السمانة على جهاز الضغط", "تمرين السمانة بأوزان موجهة على مكبس الأرجل."),
    },
    "releves_jambes_suspendu": {
        "fr": ("Relevés de jambes suspendu", "Abdominaux inférieurs en suspension."),
        "en": ("Hanging leg raises", "Lower abs from a dead hang."),
        "es": ("Elevaciones de piernas colgado", "Abdominales inferiores colgado en barra."),
        "ar": ("رفع الأرجل معلقاً في العقلة", "تقوية عضلات البطن السفلية أثناء التعلق."),
    },
    "fentes_marchees": {
        "fr": ("Fentes marchées", "Fentes dynamiques en déplacement alterné."),
        "en": ("Walking lunges", "Dynamic lunges stepping forward continuously."),
        "es": ("Zancadas caminando", "Zancadas dinámicas avanzando continuamente."),
        "ar": ("طعنات المشي (واركينغ لانجز)", "طعنات ديناميكية للأمام بخطوات متتالية."),
    },
    "pompes_lestees": {
        "fr": ("Pompes lestées", "Pompes au sol avec disque ou veste lestée sur le dos."),
        "en": ("Weighted push-ups", "Push-ups with a plate or weight vest on the back."),
        "es": ("Flexiones lastradas", "Flexiones con disco o chaleco de lastre en la espalda."),
        "ar": ("تمرين الضغط بأوزان إضافية", "ضغط على الأرض مع وضع وزن أو سترة مثقلة على الظهر."),
    },
    "dips_lestes": {
        "fr": ("Dips lestés", "Dips aux barres parallèles avec ceinture de lest."),
        "en": ("Weighted dips", "Parallel bar dips with an added weight belt."),
        "es": ("Fondos lastrados", "Fondos en paralelas con cinturón de lastre."),
        "ar": ("تمرين المتوازي بأوزان إضافية (ديبس)", "هبوط وصعود على المتوازي مع حزام أثقال."),
    },

    # ------------------------------------------------------------
    # 3. ENDURANCE
    # ------------------------------------------------------------
    "fentes_sautees": {
        "fr": ("Fentes sautées", "Fentes plyométriques, une jambe puis l'autre."),
        "en": ("Jumping lunges", "Alternating plyometric lunges."),
        "es": ("Zancadas con salto", "Zancadas pliométricas alternadas."),
        "ar": ("طعنات مع القفز (جمب لانجز)", "طعنات بليومترية بالتبادل بين الساقين مع القفز."),
    },
    "mollets_une_jambe": {
        "fr": ("Mollets sur une jambe", "Élévation unilatérale avec pause en haut."),
        "en": ("Single-leg calf raises", "Unilateral raise with a pause at the top."),
        "es": ("Gemelos a una pierna", "Elevación unilateral con pausa en contracción."),
        "ar": ("رفع السمانة برجل واحدة", "رفع أحادي للسمانة مع ثبات في أعلى الحركة."),
    },
    "step_ups_charges": {
        "fr": ("Step-ups chargés", "Montées sur banc avec haltères."),
        "en": ("Weighted step-ups", "Box step-ups holding dumbbells."),
        "es": ("Step-ups con peso", "Subidas al cajón o banco con mancuernas."),
        "ar": ("صعود الصندوق بأوزان (ستيب أب)", "صعود على الصندوق أو المقعد حاملاً دمبلز."),
    },
    "gainage_lateral": {
        "fr": ("Gainage latéral", "Planche sur le côté, hanche haute."),
        "en": ("Side plank", "Lateral plank with hips lifted."),
        "es": ("Plancha lateral", "Plancha de lado elevando las caderas."),
        "ar": ("لوح جانبي (سايد بلانك)", "بلانك على الجانب مع رفع الورك واستقامة الجسم."),
    },
    "bridge_une_jambe": {
        "fr": ("Bridge sur une jambe", "Pont fessier unilatéral."),
        "en": ("Single-leg glute bridge", "Unilateral hip bridge."),
        "es": ("Puente de glúteos a una pierna", "Puente de cadera unilateral."),
        "ar": ("جسر الأرداف برجل واحدة", "رفع الحوض برجل واحدة لعزل الأرداف."),
    },

    # ------------------------------------------------------------
    # 4. FOOTBALL & COLLECTIFS
    # ------------------------------------------------------------
    "sprints_en_v": {
        "fr": ("Sprints en V", "Accélérations avec changement de direction en V."),
        "en": ("V-cut sprints", "Accelerations with a V-shaped cut."),
        "es": ("Sprints en V", "Aceleraciones con cambio de dirección en ángulo V."),
        "ar": ("انطلاقات سريعة على شكل V", "تسارع سريع مع تغيير اتجاه حاد على شكل حرف V."),
    },
    "sauts_lateraux_haies": {
        "fr": ("Sauts latéraux haie basse", "Pliométrie latérale par-dessus une haie."),
        "en": ("Lateral hurdle hops", "Side-to-side hops over a low hurdle."),
        "es": ("Saltos laterales sobre vallas bajas", "Pliometría lateral sobre obstáculo bajo."),
        "ar": ("قفزات جانبية فوق حواجز منخفضة", "قفز بليومتري جانبي سريع لتطوير التوازن والرشاقة."),
    },
    "nordics_hamstring": {
        "fr": ("Nordic hamstring curls", "Curl ischio excentrique au sol, partenaire ou ancrage."),
        "en": ("Nordic hamstring curls", "Eccentric hamstring curl from the knees."),
        "es": ("Curl nórdico para isquiotibiales", "Curl excéntrico de isquiotibiales con anclaje."),
        "ar": ("تمرين نورديك لأوتار الركبة", "تمرين تركيز سلبي قوي لأوتار الركبة لمنع الإصابات."),
    },
    "copenhagen_plank": {
        "fr": ("Copenhagen plank / adducteurs", "Gainage latéral pour les adducteurs."),
        "en": ("Copenhagen plank", "Side-lying adductor plank."),
        "es": ("Plancha Copenhague / aductores", "Plancha lateral enfocada en aductores de la ingle."),
        "ar": ("لوح كوبنهاغن لتقوية الضامات", "بلانك جانبي مخصص لتقوية عضلات الفخذ الضامة."),
    },
    "proprio_bosu": {
        "fr": ("Proprioception BOSU / plateau instable", "Équilibre unipodal sur surface instable."),
        "en": ("BOSU proprioception", "Single-leg balance on an unstable surface."),
        "es": ("Propiocepción en BOSU / superficie inestable", "Equilibrio a una pierna sobre plataforma inestable."),
        "ar": ("توازن وإدراك حركي على البوسو (BOSU)", "توازن على قدم واحدة فوق سطح غير مستقر لتقوية المفاصل."),
    },
    "gainage_rotations_buste": {
        "fr": ("Gainage dynamique avec rotations", "Planche et rotations contrôlées du buste."),
        "en": ("Plank with torso rotations", "Dynamic plank adding controlled twists."),
        "es": ("Plancha dinámica con rotaciones", "Plancha con giros controlados del tronco."),
        "ar": ("بلانك مع دوران الجذع", "تمرين بلانك مع دوران جانبي متحكم به للجذع."),
    },
    "echelle_agilite_footwork": {
        "fr": ("Échelle d'agilité (pas chassés, in-out)", "Footwork rapide pieds joints et latéraux."),
        "en": ("Agility ladder footwork", "In-out, shuffles and two-foot hops."),
        "es": ("Escalera de agilidad (in-out, pasos rápidos)", "Juego de pies rápido y coordinación."),
        "ar": ("سلم الرشاقة (حركات قدم سريعة)", "تنقلات سريعة وتوافق عصبي عضلي للقدمين."),
    },

    # ------------------------------------------------------------
    # 5. SÉDENTAIRE
    # ------------------------------------------------------------
    "cat_cow": {
        "fr": ("Cat-cow", "Mobilisation douce de la colonne en flexion/extension."),
        "en": ("Cat-cow", "Gentle spinal flexion and extension."),
        "es": ("Gato-vaca (Cat-cow)", "Movilización suave de la columna en flexión y extensión."),
        "ar": ("وضعية القطة والبقرة (كات كاو)", "تحريك لطيف ومريح للعمود الفقري في الانحناء والانبساط."),
    },
    "squats_chaise": {
        "fr": ("Squats assis-debout sur chaise", "Assise et relevé contrôlés, amplitude limitée."),
        "en": ("Sit-to-stand from a chair", "Controlled stand-up with a limited range."),
        "es": ("Sentadilla sentarse y levantarse de silla", "Levantarse y sentarse de forma controlada."),
        "ar": ("الجلوس والوقوف من الكرسي", "سكوات ميسر بالجلوس والوقوف المنضبط على كرسي."),
    },
    "pompes_inclinees": {
        "fr": ("Pompes inclinées (table ou mur)", "Pompes facilitées, mains surélevées."),
        "en": ("Incline push-ups", "Hands elevated on a table or wall."),
        "es": ("Flexiones inclinadas (mesa o pared)", "Flexiones facilitadas con manos elevadas."),
        "ar": ("ضغط مائل (على طاولة أو جدار)", "تمرين ضغط ميسر برفع اليدين على طاولة أو حائط."),
    },
    "rowing_elastique": {
        "fr": ("Rowing avec bande élastique", "Tirage horizontal sans machine."),
        "en": ("Band row", "Horizontal pull with a resistance band."),
        "es": ("Remo con banda elástica", "Tirón horizontal sin máquinas."),
        "ar": ("تجديف بشريط المقاومة", "سحب أفقي لتقوية الظهر باستخدام شريط مطاطي."),
    },
    "developpe_epaules_leger": {
        "fr": ("Développé épaules léger", "Bouteilles d'eau ou petits haltères."),
        "en": ("Light shoulder press", "Water bottles or very light dumbbells."),
        "es": ("Press de hombros ligero", "Empuje con botellas de agua o mancuernas ligeras."),
        "ar": ("دفع كتف خفيف", "رفع أثقال خفيفة أو زجاجات مياه للأعلى."),
    },
    "gainage_genoux": {
        "fr": ("Gainage genoux au sol", "Planche adaptée, genoux posés."),
        "en": ("Kneeling plank", "Regressed plank with knees down."),
        "es": ("Plancha con rodillas en el suelo", "Plancha adaptada con apoyo de rodillas."),
        "ar": ("بلانك مع وضع الركبتين على الأرض", "لوح بلانك ميسر للمبتدئين بارتكاز الركبتين."),
    },
    "jumping_jacks": {
        "fr": ("Jumping jacks", "Écartés sautés, finisseur métabolique simple."),
        "en": ("Jumping jacks", "Simple metabolic finisher."),
        "es": ("Jumping jacks", "Saltos en tijera, finalizador metabólico sencillo."),
        "ar": ("القفز مع فتح الذراعين والساقين (جامبينج جاكس)", "تمرين حركي لحرق السعرات ورفع النبض."),
    },
    "respiration_diaphragmatique": {
        "fr": ("Respiration diaphragmatique", "Respiration ventrale lente pour récupérer."),
        "en": ("Diaphragmatic breathing", "Slow belly breathing for recovery."),
        "es": ("Respiración diafragmática", "Respiración abdominal lenta para calmar y recuperar."),
        "ar": ("تنفس بطني حجابي", "تنفس عميق من البطن لتهدئة الجهاز العصبي والاستشفاء."),
    },
    "travail_postural": {
        "fr": ("Travail postural", "Alignement tête-épaules-bassin, mobilité articulaire."),
        "en": ("Postural work", "Head-shoulder-hip alignment and joint mobility."),
        "es": ("Trabajo postural", "Alineación de cabeza, hombros y pelvis."),
        "ar": ("تمارين تصحيح القوام والمحاذاة", "محاذاة الرأس والكتفين والحوض مع مرونة المفاصل."),
    },
    "rotations_bras_epaules": {
        "fr": ("Rotations des bras et épaules", "Circonférences amples des bras pour mobiliser la ceinture scapulaire."),
        "en": ("Arm and shoulder circles", "Wide arm rotations to mobilize the shoulder girdle."),
        "es": ("Rotaciones de brazos y hombros", "Círculos amplios de brazos para movilizar los hombros."),
        "ar": ("دوران الذراعين والكتفين", "حركات دائرية واسعة للذراعين لتحريك مفصل الكتف."),
    },
    "marche_rapide": {
        "fr": ("Marche rapide", "Marche active à allure soutenue en plein air ou sur tapis."),
        "en": ("Brisk walking", "Active walking at a brisk pace outdoors or on a treadmill."),
        "es": ("Caminata rápida", "Paseo a ritmo rápido al aire libre o en cinta."),
        "ar": ("مشي سريع", "مشي بنشاط وسرعة معتدلة في الهواء الطلق أو على السير."),
    },
    "marche_active": {
        "fr": ("Marche active", "Marche continue pour relancer la circulation."),
        "en": ("Active walking", "Continuous active walking to boost circulation."),
        "es": ("Caminata activa", "Caminar continuo para activar la circulación sanguínea."),
        "ar": ("مشي نشط", "مشي مستمر لتنشيط الدورة الدموية والجسم."),
    },
    "etirements_doux_ischios_pecs": {
        "fr": ("Étirements doux des ischio-jambiers et pectoraux", "Étirements légers et progressifs sans forcer."),
        "en": ("Gentle hamstring and chest stretches", "Mild and progressive stretches without straining."),
        "es": ("Estiramientos suaves de isquiotibiales y pectorales", "Estiramientos progresivos y suaves sin forzar."),
        "ar": ("استطالة لطيفة لأوتار الركبة والصدر", "تمديد عضلات خلف الفخذ والصدر بلطف ودون إجهاد."),
    },
}

# Traductions multilingues (FR, EN, ES, AR) pour les exercices de base
BASE_EXERCISES_I18N = {
    "squat": {
        "fr": ("Squat", "Flexion des jambes avec charge sur les épaules."),
        "en": ("Squat", "Leg flexion with a barbell on the shoulders."),
        "es": ("Sentadilla", "Flexión de piernas con barra sobre los hombros."),
        "ar": ("تمرين القرفصاء (سكوات)", "ثني الساقين مع حمل البار على الكتفين."),
    },
    "developpe_couche": {
        "fr": ("Développé couché", "Poussée de la barre en position allongée."),
        "en": ("Bench press", "Barbell press performed lying down."),
        "es": ("Press de banca", "Empuje de barra tumbado en banco plano."),
        "ar": ("بنش برس بالبار", "دفع البار مستلقياً على مقعد مستوٍ."),
    },
    "developpe_incline_halteres": {
        "fr": ("Développé incliné haltères", "Cible le haut des pectoraux et l'avant des épaules."),
        "en": ("Incline dumbbell press", "Targets upper chest and front delts."),
        "es": ("Press inclinado con mancuernas", "Enfocado en la parte superior del pecho."),
        "ar": ("ضغط صدر مائل بالدمبلز", "استهداف الجزء العلوي من عضلات الصدر والكتف الأمامي."),
    },
    "souleve_de_terre": {
        "fr": ("Soulevé de terre", "Souleve la barre du sol jusqu'aux hanches."),
        "en": ("Deadlift", "Lifts the barbell from the floor to hip level."),
        "es": ("Peso muerto", "Levantamiento de la barra desde el suelo hasta la cadera."),
        "ar": ("الرفعة الميتة (ديدليفت)", "رفع البار من الأرض حتى مستوى الوركين بكامل الجسم."),
    },
    "traction": {
        "fr": ("Traction", "Tire le corps vers une barre fixe."),
        "en": ("Pull-up", "Pulls the body up to a fixed bar."),
        "es": ("Dominadas", "Tracción del cuerpo hacia una barra fija."),
        "ar": ("تمرين العقلة", "سحب الجسم للأعلى نحو عارضة ثابتة."),
    },
    "rowing_barre": {
        "fr": ("Rowing barre", "Tirage horizontal de la barre vers le nombril."),
        "en": ("Barbell bent-over row", "Horizontal barbell pull toward the navel."),
        "es": ("Remo con barra", "Tirón horizontal con barra hacia la cintura."),
        "ar": ("تجديف بالبار منحنياً", "سحب البار أفقياً نحو منطقة البطن مع انحناء الجذع."),
    },
    "developpe_militaire": {
        "fr": ("Développé militaire", "Développé au-dessus de la tête, barre debout."),
        "en": ("Overhead press", "Standing vertical barbell press overhead."),
        "es": ("Press militar", "Empuje vertical con barra por encima de la cabeza."),
        "ar": ("ضغط عسكري بالبار", "دفع البار عمودياً فوق الرأس من وضعية الوقوف."),
    },
    "dips": {
        "fr": ("Dips", "Flexion/extension des bras aux barres parallèles."),
        "en": ("Dips", "Arm dip performed on parallel bars."),
        "es": ("Fondos en paralelas", "Flexión y extensión de brazos en barras paralelas."),
        "ar": ("تمرين المتوازي (ديبس)", "ثني وتمديد الذراعين على عوارض متوازية."),
    },
    "presse_a_cuisses": {
        "fr": ("Presse à cuisses", "Poussée guidée des jambes, quadriceps et fessiers."),
        "en": ("Leg press", "Guided leg press for quads and glutes."),
        "es": ("Prensa de piernas", "Empuje de piernas guiado para cuádriceps y glúteos."),
        "ar": ("مكبس الأرجل (ليج برس)", "دفع الأوزان موجهة بالأرجل لاستهداف الفخذ والأرداف."),
    },
    "elevations_laterales": {
        "fr": ("Élévations latérales", "Isolation du faisceau latéral des épaules."),
        "en": ("Lateral raises", "Isolation of the side delts."),
        "es": ("Elevaciones laterales", "Aislamiento de la cabeza lateral del deltoides."),
        "ar": ("رفرفة جانبية بالدمبلز", "عزل وتقوية الجزء الجانبي من عضلات الكتف."),
    },
    "curl_biceps_barre": {
        "fr": ("Curl biceps à la barre", "Flexion des coudes, isolation des biceps."),
        "en": ("Barbell biceps curl", "Elbow flexion isolating the biceps."),
        "es": ("Curl de bíceps con barra", "Flexión de codos aislando los bíceps."),
        "ar": ("كيرل البايسبس بالبار", "ثني الكوعين لعزل وتضخيم عضلات البايسبس."),
    },
    "extension_triceps_poulie": {
        "fr": ("Extension triceps à la poulie", "Extension des coudes vers le bas."),
        "en": ("Triceps pushdown", "Cable pushdown isolating the triceps."),
        "es": ("Extensión de tríceps en polea", "Empuje hacia abajo aislando los tríceps."),
        "ar": ("سحب الترايسبس بالكيبل لأسفل", "دفع الكيبل لأسفل لعزل عضلات الترايسبس."),
    },
    "gainage": {
        "fr": ("Gainage planche", "Maintien statique horizontal, travail de la sangle abdominale."),
        "en": ("Plank", "Static horizontal hold for core strength."),
        "es": ("Plancha abdominal", "Mantenimiento estático horizontal para el núcleo."),
        "ar": ("لوح البلانك", "ثبات أفقي لتقوية عضلات البطن والجذع."),
    },
    "burpees_cardio": {
        "fr": ("Burpees explosifs", "Enchaînement squat, planche, pompe et saut."),
        "en": ("Explosive burpees", "Squat, plank, push-up and jump combination."),
        "es": ("Burpees explosivos", "Combinación de sentadilla, plancha, flexión y salto."),
        "ar": ("تمرين البيربي الانفجاري", "دمج السكوات والبلانك والضغط مع القفز."),
    },
    "kettlebell_swings": {
        "fr": ("Kettlebell swings", "Balancement balistique propulsé par les hanches."),
        "en": ("Kettlebell swings", "Ballistic hip-hinge swing."),
        "es": ("Kettlebell swings", "Balanceo balístico impulsado por la cadera."),
        "ar": ("أرجحة الكتلبل (سويغز)", "أرجحة انفجارية للكتلبل مدفوعة بحركة الوركين."),
    },
    "course_fractionnee": {
        "fr": ("Course fractionnée (HIIT)", "Intervalles sprint / footing lent."),
        "en": ("Interval running (HIIT)", "Sprint and slow jog intervals."),
        "es": ("Carrera fraccionada (HIIT)", "Intervalos de sprint y trote de recuperación."),
        "ar": ("الجري المتقطع عالي الكثافة", "فترات تبادلية بين الجري السريع والهرولة البطيئة."),
    },
    "velo_intervalles_puissance": {
        "fr": ("Vélo par intervalles de puissance", "Résistance maximale alternée avec pédalage fluide."),
        "en": ("Cycling power intervals", "Max resistance intervals alternated with easy pedaling."),
        "es": ("Intervalos de potencia en bicicleta", "Máxima resistencia alternada con pedaleo suave."),
        "ar": ("فترات القوة على الدراجة", "تبادل بين أقصى مقاومة والتدوير الخفيف."),
    },
    "intervalles_sprint_natation": {
        "fr": ("Natation fractionnée sprint", "Séries courtes en sprint crawl."),
        "en": ("Swim sprint intervals", "Short freestyle sprint repetitions."),
        "es": ("Series de natación en sprint", "Series cortas de sprint en estilo crol."),
        "ar": ("سباحة السرعة المتقطعة", "تكرارات سباحة حرة سريعة مع فترات راحة قصيرة."),
    },
    "course_endurance": {
        "fr": ("Course continue (Zone 2)", "Effort continu à allure conversationnelle."),
        "en": ("Continuous endurance run (Zone 2)", "Continuous run at conversational pace."),
        "es": ("Carrera continua (Zona 2)", "Ritmo cómodo y continuo de conversación."),
        "ar": ("الجري المستمر للتحمل (المنطقة 2)", "جري متواصل بوتيرة مريحة تسمح بالتحدث."),
    },
    "velo_route": {
        "fr": ("Sortie vélo continue", "Sortie route à cadence fluide Zone 2."),
        "en": ("Continuous road cycling", "Smooth cadence endurance road ride."),
        "es": ("Ciclismo de carretera continuo", "Pedaleo continuo a cadencia fluida en Zona 2."),
        "ar": ("ركوب الدراجة على الطريق", "تمرين مستمر بسرعة متوازنة في المنطقة 2."),
    },
    "natation_crawl": {
        "fr": ("Natation continue Crawl", "Nage continue en aisance respiratoire."),
        "en": ("Continuous freestyle swim", "Smooth continuous swim with comfortable breathing."),
        "es": ("Natación continua crol", "Nado continuo con respiración cómoda."),
        "ar": ("سباحة حرة مستمرة", "سباحة كراول متواصلة مع سهولة في التنفس."),
    },
    "match_football": {
        "fr": ("Match de football / opposition", "Match complet ou séquences à intensité réelle."),
        "en": ("Football match / scrimmage", "Full match or live-intensity sequences."),
        "es": ("Partido de fútbol / partidillo", "Partido completo o situaciones reales de juego."),
        "ar": ("مباراة كرة قدم / مناورة", "مباراة كاملة أو فترات لعب بكثافة واقعية."),
    },
    "passes_courtes_une_touche": {
        "fr": ("Passes courtes en une touche", "Exercice de conservation du ballon et réactivité."),
        "en": ("One-touch short passing", "Ball retention and quick-reaction drill."),
        "es": ("Pases cortos al primer toque", "Conservación de balón y velocidad de reacción."),
        "ar": ("تمريرات قصيرة من لمسة واحدة", "الاستحواذ على الكرة وسرعة رد الفعل."),
    },
    "frappes_et_tirs_au_but": {
        "fr": ("Frappes et tirs au but", "Travail de finition et précision face au gardien."),
        "en": ("Finishing and shooting drills", "Finishing and shooting accuracy drills."),
        "es": ("Tiros a puerta y finalización", "Trabajo de puntería y remate frente al portero."),
        "ar": ("التسديد وإنهاء الهجمات", "تطوير الدقة والتهديف أمام المرمى."),
    },
    "sprint": {
        "fr": ("Sprint", "Accélération maximale sur courte distance."),
        "en": ("Sprint", "Maximal linear sprint over a short distance."),
        "es": ("Sprint", "Aceleración máxima en corta distancia."),
        "ar": ("انطلاق سريع (سبرينت)", "تسارع بأقصى سرعة لمسافة قصيرة."),
    },
    "corde_a_sauter": {
        "fr": ("Corde à sauter", "Cardio et réactivité des chevilles."),
        "en": ("Jump rope", "Cardio conditioning and ankle stiffness."),
        "es": ("Salto a la comba", "Cardio y reactividad en los tobillos."),
        "ar": ("القفز بالحبل", "كارديو ورشاقة وسرعة ارتداد الكاحلين."),
    },
    "etirements": {
        "fr": ("Étirements & mobilité", "Retour au calme articulaire et musculaire."),
        "en": ("Stretching & mobility", "Cooldown joint and muscle release."),
        "es": ("Estiramientos y movilidad", "Vuelta a la calma muscular y articular."),
        "ar": ("استطالة ومرونة", "تهدئة العضلات والمفاصل بعد التمرين."),
    },
    "shadow_boxing": {
        "fr": ("Shadow boxing", "Boxe à vide travaillant technique et déplacements."),
        "en": ("Shadow boxing", "Mirror boxing focusing on footwork and technique."),
        "es": ("Shadow boxing", "Boxeo de sombra enfocado en técnica y desplazamientos."),
        "ar": ("ملاكمة الظل (شادو بوكسينغ)", "ملاكمة أمام المرآة لتطوير التكنيك وحركات القدم."),
    },
    "mountain_climbers": {
        "fr": ("Mountain climbers", "Montées de genoux dynamiques en position planche."),
        "en": ("Mountain climbers", "Dynamic knee drives from a plank position."),
        "es": ("Escaladores (mountain climbers)", "Elevaciones dinámicas de rodillas en posición de plancha."),
        "ar": ("تمرين متسلق الجبال (ماونتن كلايمبرز)", "سحب ديناميكي للركبتين من وضعية البلانك."),
    },
}

EXERCISE_I18N.update(BASE_EXERCISES_I18N)
