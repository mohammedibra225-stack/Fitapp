"""Configuration globale pour l'analyse IA de repas (vision locale via Ollama)."""

import os

# ---------------------------------------------------------------------------
# Ollama (analyse de photos de repas)
# ---------------------------------------------------------------------------
# Ollama tourne en local, il n'y a donc AUCUNE cle API a proteger ici.
# L'URL reste configurable pour pouvoir pointer vers une autre machine du
# reseau (ex: un PC plus puissant) sans toucher au code.
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

# Modele multimodal utilise pour la vision.
# qwen2.5vl:3b = bon compromis vitesse / qualite sur une machine de dev.
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")

# Timeout d'un appel Ollama (secondes).
# Un modele vision 3B sur CPU peut mettre 30-60s au premier appel (chargement
# du modele en memoire), puis beaucoup moins ensuite.
OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

# Nombre de tentatives supplementaires en cas de timeout / coupure reseau.
OLLAMA_MAX_RETRIES: int = int(os.getenv("OLLAMA_MAX_RETRIES", "1"))

# Temperature : basse = sortie plus deterministe, indispensable pour du JSON.
OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

# Duree pendant laquelle Ollama garde le modele charge en RAM/VRAM apres un
# appel. Sans ca, Ollama decharge le modele au bout de quelques minutes
# d'inactivite et le rechargement (20-40s pour un 3B) s'ajoute a CHAQUE
# analyse. "30m" = le modele reste chaud pendant 30 minutes d'utilisation
# normale de l'app. Utiliser "-1" pour ne jamais decharger (si assez de RAM).
OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# Nombre max de tokens generes par le modele. Notre JSON de sortie est court
# (quelques aliments) ; sans plafond, un petit modele peut partir dans du
# texte inutile et faire durer l'inference pour rien.
OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "400"))

# ---------------------------------------------------------------------------
# Hugging Face (analyse de photos de repas via ZeroGPU)
# ---------------------------------------------------------------------------
# Le Space Hugging Face de vision (Qwen2.5-VL) tourne sur du materiel
# ZeroGPU. Sans authentification, le quota de requetes ZeroGPU anonyme
# est tres bas et s'epuise vite ("You have exceeded your ZeroGPU runs
# limit"). En fournissant un token Hugging Face (lecture seule suffit),
# le quota devient nettement plus eleve.
#
# Cree un token sur https://huggingface.co/settings/tokens (role "read")
# et renseigne HUGGINGFACE_TOKEN dans le .env. Reste facultatif : si
# absent, le client Gradio se connecte en anonyme comme avant.
HUGGINGFACE_TOKEN: str | None = (
    os.getenv("HUGGINGFACE_TOKEN")
    or os.getenv("HF_TOKEN")
    or None
)

# ---------------------------------------------------------------------------
# Seuils de confiance pour l'analyse d'aliments
# ---------------------------------------------------------------------------
# confidence >= HIGH_CONFIDENCE_THRESHOLD -> fiable
# MEDIUM_CONFIDENCE_THRESHOLD <= confidence < HIGH_CONFIDENCE_THRESHOLD -> demande confirmation
# confidence < MEDIUM_CONFIDENCE_THRESHOLD -> demande correction utilisateur
HIGH_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_HIGH_CONFIDENCE_THRESHOLD", "0.80"))
MEDIUM_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_MEDIUM_CONFIDENCE_THRESHOLD", "0.50"))

# ---------------------------------------------------------------------------
# Limites pour l'upload d'image
# ---------------------------------------------------------------------------
MAX_IMAGE_SIZE_BYTES: int = int(os.getenv("AI_MAX_IMAGE_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10 Mo
ALLOWED_IMAGE_MIME_TYPES: tuple[str, ...] = (
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
)

# Cote le plus long de l'image envoyee au modele, en pixels.
# Une photo d'iPhone fait ~4000px. Sur un 3B CPU, le temps d'inference vision
# croit fortement avec la resolution : 768px est le meilleur compromis
# vitesse/qualite pour de la reconnaissance d'aliments (1024 est ~2x plus lent
# pour un gain de precision marginal).
AI_IMAGE_MAX_DIMENSION: int = int(os.getenv("AI_IMAGE_MAX_DIMENSION", "768"))

# Qualite JPEG apres normalisation de l'image.
AI_IMAGE_JPEG_QUALITY: int = int(os.getenv("AI_IMAGE_JPEG_QUALITY", "85"))

# ---------------------------------------------------------------------------
# Quota quotidien
# ---------------------------------------------------------------------------
# Historiquement a 4/jour pour proteger le quota payant de Gemini.
# Ollama tourne en local : le cout marginal d'une analyse est nul, la seule
# limite reelle est le temps CPU. Le quota est conserve comme garde-fou
# (evite qu'un bug de l'app sature le serveur) mais nettement releve.
MAX_MEAL_ANALYSES_PER_DAY: int = int(os.getenv("AI_MAX_MEAL_ANALYSES_PER_DAY", "30"))
