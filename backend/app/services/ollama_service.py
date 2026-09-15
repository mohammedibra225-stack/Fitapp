"""
Service d'analyse d'image de repas via Ollama (modele vision local, ex: qwen2.5vl:3b).

Regle fondamentale :
Ce service se charge EXCLUSIVEMENT de :
- Encoder l'image et l'envoyer a l'API HTTP locale d'Ollama
- Forcer une reponse JSON stricte
- Nettoyer, valider et normaliser cette reponse via Pydantic (MealVisionAnalysis)
- Remonter des exceptions explicites en cas d'erreur reseau, de modele absent
  ou de JSON invalide

Ce service NE FAIT AUCUN CALCUL NUTRITIONNEL.
Le matching Food et le calcul des macros restent la responsabilite de
food_matching_service + meal_calculator.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any, Optional

import httpx

from app.config_ai import (
    OLLAMA_BASE_URL,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_MAX_RETRIES,
    OLLAMA_MODEL,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT_SECONDS,
)
from app.schemas.meal_analysis import MealVisionAnalysis

logger = logging.getLogger("fitapp.ollama")


MEAL_VISION_PROMPT = """You are a professional nutrition vision assistant for a fitness application.
Analyze this meal photo carefully and identify the visible food items.

CRITICAL RULES:
1. Identify ONLY foods and ingredients that are actually visible. Do NOT invent items.
2. Look for: rice, pasta, bread, chicken, red meat, fish, eggs, vegetables, fruits,
   legumes, dairy products, sauces, oils, drinks, and any other visible food.
3. Estimate portions realistically. Prefer grams ("g") whenever possible.
4. For items naturally counted individually (egg, banana, apple, slice of bread),
   you may use "piece".
5. A photo never gives an exact weight. Give your best estimate and an honest
   confidence score between 0.0 and 1.0, for each item and overall.
6. Suggest alternatives in the "alternatives" list when unsure
   (e.g. "chicken" vs "turkey").
7. The nutritional database is handled entirely by the application.
   DO NOT estimate calories, protein, carbs or fat. Your job is visual food
   identification and portion estimation ONLY.
8. Deduce the probable meal_type: one of breakfast, lunch, dinner, snack.
9. If the photo contains no food at all, return an empty "foods" list.

Answer with a SINGLE valid JSON object. No markdown, no backticks, no comment
before or after. Exact shape:

{
  "meal_type": "lunch",
  "overall_confidence": 0.90,
  "foods": [
    {
      "name": "rice",
      "estimated_quantity": 150,
      "unit": "g",
      "preparation": "cooked",
      "confidence": 0.95,
      "alternatives": []
    }
  ],
  "notes": []
}
"""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class OllamaServiceError(Exception):
    """Erreur generique du service d'analyse de repas."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OllamaUnavailableError(OllamaServiceError):
    """Ollama n'est pas joignable (service eteint, mauvaise URL)."""

    def __init__(
        self,
        message: str = "Le service d'analyse des repas est temporairement indisponible.",
    ):
        super().__init__(message, status_code=503)


class OllamaModelMissingError(OllamaServiceError):
    """Le modele de vision n'est pas installe dans Ollama."""

    def __init__(
        self,
        message: str = "Le modèle d'analyse des repas n'est pas disponible.",
    ):
        super().__init__(message, status_code=503)


class OllamaTimeoutError(OllamaServiceError):
    """Le modele n'a pas repondu dans le delai imparti."""

    def __init__(
        self,
        message: str = "L'analyse du repas a pris trop de temps. Réessaie dans quelques instants.",
    ):
        super().__init__(message, status_code=504)


class OllamaInvalidResponseError(OllamaServiceError):
    """La reponse du modele n'est pas un JSON conforme."""

    def __init__(
        self,
        message: str = "La réponse du modèle d'analyse est inexploitable.",
    ):
        super().__init__(message, status_code=502)


# ---------------------------------------------------------------------------
# Nettoyage / normalisation de la sortie du modele
# ---------------------------------------------------------------------------

_ALLOWED_UNITS = ("g", "kg", "ml", "l", "piece", "unit", "pcs")
_ALLOWED_MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")

# Cles alternatives que les petits modeles utilisent souvent malgre le prompt.
_QUANTITY_KEYS = (
    "estimated_quantity",
    "estimated_quantity_g",
    "quantity",
    "amount",
    "portion",
    "estimated_weight_g",
)
_FOODS_KEYS = ("foods", "items", "food_items", "detected_foods")


def _extract_json_block(raw_text: str) -> str:
    """Isole l'objet JSON meme si le modele a ajoute du texte ou des backticks."""
    cleaned = (raw_text or "").strip()

    if cleaned.startswith("```"):
        # ```json ... ``` ou ``` ... ```
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[: -len("```")]
        cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise OllamaInvalidResponseError(
            "Le modèle d'analyse n'a pas renvoyé de JSON exploitable."
        )
    return cleaned[start : end + 1]


def _coerce_float(value: Any) -> Optional[float]:
    """Convertit '150', '150 g', 150.0 -> 150.0 ; sinon None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        buffer = ""
        for char in value.replace(",", "."):
            if char.isdigit() or (char == "." and "." not in buffer):
                buffer += char
            elif buffer:
                break
        if buffer:
            try:
                return float(buffer)
            except ValueError:
                return None
    return None


def _clamp_confidence(value: Any, default: float = 0.5) -> float:
    """Ramene la confiance dans [0, 1]. Gere aussi les modeles qui repondent 85 pour 85%."""
    number = _coerce_float(value)
    if number is None:
        return default
    if number > 1.0:
        number = number / 100.0 if number <= 100.0 else 1.0
    return max(0.0, min(1.0, number))


def _normalize_unit(value: Any, quantity_key_used: str) -> str:
    """Normalise l'unite, en tenant compte des cles du type 'estimated_quantity_g'."""
    if quantity_key_used.endswith("_g"):
        return "g"
    if not isinstance(value, str):
        return "g"
    unit = value.strip().lower()
    aliases = {
        "grams": "g",
        "gram": "g",
        "gr": "g",
        "grammes": "g",
        "gramme": "g",
        "kilograms": "kg",
        "milliliters": "ml",
        "millilitres": "ml",
        "liters": "l",
        "litres": "l",
        "pieces": "piece",
        "pc": "piece",
        "piece(s)": "piece",
        "units": "unit",
        "serving": "piece",
        "servings": "piece",
        "slice": "piece",
        "slices": "piece",
    }
    unit = aliases.get(unit, unit)
    return unit if unit in _ALLOWED_UNITS else "g"


def _sanitize_payload(data: Any) -> dict:
    """
    Transforme la sortie brute du modele en dict strictement conforme a
    MealVisionAnalysis. On ne fait JAMAIS confiance a la sortie telle quelle.
    """
    if not isinstance(data, dict):
        raise OllamaInvalidResponseError(
            "Le modèle d'analyse n'a pas renvoyé un objet JSON."
        )

    raw_foods: Any = []
    for key in _FOODS_KEYS:
        if isinstance(data.get(key), list):
            raw_foods = data[key]
            break

    foods: list[dict] = []
    for entry in raw_foods:
        if not isinstance(entry, dict):
            continue

        name = entry.get("name") or entry.get("food") or entry.get("label")
        if not isinstance(name, str) or not name.strip():
            continue

        quantity: Optional[float] = None
        quantity_key_used = ""
        for key in _QUANTITY_KEYS:
            if key in entry:
                quantity = _coerce_float(entry.get(key))
                if quantity is not None:
                    quantity_key_used = key
                    break

        # Une quantite absente ou nulle rend l'item inexploitable par le
        # Meal Calculator : on retient une valeur de repli plutot que de perdre
        # l'aliment, l'utilisateur pourra corriger dans l'ecran de confirmation.
        if quantity is None or quantity <= 0:
            quantity = 100.0
            quantity_key_used = ""

        # Garde-fou contre les valeurs aberrantes (modele qui hallucine 50000 g).
        quantity = min(quantity, 5000.0)

        alternatives_raw = entry.get("alternatives")
        alternatives = [
            alt.strip()
            for alt in alternatives_raw
            if isinstance(alt, str) and alt.strip()
        ][:5] if isinstance(alternatives_raw, list) else []

        preparation = entry.get("preparation")
        if not isinstance(preparation, str) or not preparation.strip():
            preparation = None

        foods.append(
            {
                "name": name.strip()[:120],
                "estimated_quantity": quantity,
                "unit": _normalize_unit(entry.get("unit"), quantity_key_used),
                "preparation": preparation,
                "confidence": _clamp_confidence(entry.get("confidence")),
                "alternatives": alternatives,
            }
        )

        # Un repas realiste depasse rarement 15 composants ; au-dela c'est du bruit.
        if len(foods) >= 15:
            break

    meal_type = data.get("meal_type")
    if not isinstance(meal_type, str) or meal_type.strip().lower() not in _ALLOWED_MEAL_TYPES:
        meal_type = "lunch"
    else:
        meal_type = meal_type.strip().lower()

    if "overall_confidence" in data:
        overall = _clamp_confidence(data.get("overall_confidence"))
    elif foods:
        overall = round(sum(f["confidence"] for f in foods) / len(foods), 2)
    else:
        overall = 0.0

    notes_raw = data.get("notes")
    notes = [
        note.strip()
        for note in notes_raw
        if isinstance(note, str) and note.strip()
    ][:5] if isinstance(notes_raw, list) else []

    return {
        "meal_type": meal_type,
        "foods": foods,
        "overall_confidence": overall,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Appel Ollama
# ---------------------------------------------------------------------------


def _is_model_missing_error(status_code: int, body: str) -> bool:
    """Ollama renvoie 404 + 'model ... not found' quand le pull n'a pas ete fait."""
    if status_code != 404:
        return False
    lowered = (body or "").lower()
    return "not found" in lowered or "try pulling" in lowered or "no such model" in lowered


def analyze_meal_image_with_ollama(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> MealVisionAnalysis:
    """
    Envoie l'image au modele de vision servi par Ollama et retourne un
    MealVisionAnalysis valide.

    Le parametre mime_type n'est pas transmis a Ollama (qui detecte le format
    lui-meme) ; il est conserve pour garder la meme signature qu'avant et pour
    le logging.
    """
    if not image_bytes:
        raise OllamaInvalidResponseError("Aucune image à analyser.")

    model = model_name or OLLAMA_MODEL
    url = f"{(base_url or OLLAMA_BASE_URL).rstrip('/')}/api/generate"

    payload = {
        "model": model,
        "prompt": MEAL_VISION_PROMPT,
        "images": [base64.b64encode(image_bytes).decode("utf-8")],
        "stream": False,
        "format": "json",
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
            "num_predict": OLLAMA_NUM_PREDICT,
        },
    }

    response_json: Optional[dict] = None
    attempts = OLLAMA_MAX_RETRIES + 1

    for attempt in range(1, attempts + 1):
        try:
            with httpx.Client(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload)

            if _is_model_missing_error(response.status_code, response.text):
                logger.error("Modele Ollama absent: %s", model)
                raise OllamaModelMissingError(
                    f"Le modèle d'analyse des repas n'est pas disponible ({model})."
                )

            if response.status_code >= 500:
                logger.warning(
                    "Ollama a renvoye %s (tentative %s/%s)",
                    response.status_code, attempt, attempts,
                )
                if attempt < attempts:
                    time.sleep(1.5 * attempt)
                    continue
                raise OllamaUnavailableError()

            if response.status_code >= 400:
                logger.error(
                    "Ollama a refuse la requete (%s): %s",
                    response.status_code, response.text[:300],
                )
                raise OllamaServiceError(
                    "Le service d'analyse des repas a refusé la requête.",
                    status_code=502,
                )

            response_json = response.json()
            break

        except (OllamaServiceError,):
            raise
        except httpx.TimeoutException as exc:
            logger.warning(
                "Timeout Ollama (tentative %s/%s): %s", attempt, attempts, exc
            )
            if attempt < attempts:
                time.sleep(1.5 * attempt)
                continue
            raise OllamaTimeoutError(
                "L'analyse du repas a dépassé le délai autorisé "
                f"({int(OLLAMA_TIMEOUT_SECONDS)}s). Réessaie dans quelques instants."
            ) from exc
        except httpx.RequestError as exc:
            # Connexion refusee / DNS / reseau : Ollama n'est pas lance.
            logger.warning(
                "Ollama injoignable (tentative %s/%s): %s", attempt, attempts, exc
            )
            if attempt < attempts:
                time.sleep(1.0 * attempt)
                continue
            raise OllamaUnavailableError() from exc
        except ValueError as exc:
            # response.json() sur un corps non-JSON
            logger.error("Reponse Ollama non-JSON: %s", exc)
            raise OllamaInvalidResponseError() from exc

    if not response_json:
        raise OllamaUnavailableError()

    raw_text = response_json.get("response")
    if not isinstance(raw_text, str) or not raw_text.strip():
        logger.error("Ollama a renvoye une reponse vide pour le modele %s", model)
        raise OllamaInvalidResponseError(
            "Le modèle d'analyse a renvoyé une réponse vide."
        )

    json_block = _extract_json_block(raw_text)

    try:
        data = json.loads(json_block)
    except json.JSONDecodeError as exc:
        logger.error("JSON invalide renvoye par Ollama: %s", raw_text[:500])
        raise OllamaInvalidResponseError(
            "Le modèle d'analyse a renvoyé un JSON invalide."
        ) from exc

    sanitized = _sanitize_payload(data)

    try:
        return MealVisionAnalysis.model_validate(sanitized)
    except Exception as exc:
        logger.error("Sortie du modele non conforme au schema: %s", exc)
        raise OllamaInvalidResponseError(
            "Le format de données renvoyé par le modèle d'analyse est incorrect."
        ) from exc


def check_ollama_health(base_url: Optional[str] = None, model_name: Optional[str] = None) -> dict:
    """
    Verifie qu'Ollama repond et que le modele de vision est installe.
    Utilise par l'endpoint de diagnostic, jamais par le flux d'analyse.
    """
    model = model_name or OLLAMA_MODEL
    url = f"{(base_url or OLLAMA_BASE_URL).rstrip('/')}/api/tags"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {
            "available": False,
            "model": model,
            "model_installed": False,
            "detail": "Ollama ne répond pas.",
        }

    models = data.get("models") or []
    installed_names = {
        m.get("name", "") for m in models if isinstance(m, dict)
    }
    # Ollama nomme les modeles "qwen2.5vl:3b" ; tolere l'absence de tag.
    model_installed = model in installed_names or any(
        name.split(":")[0] == model.split(":")[0] for name in installed_names
    )

    return {
        "available": True,
        "model": model,
        "model_installed": model_installed,
        "installed_models": sorted(installed_names),
        "detail": None if model_installed else f"Le modèle {model} n'est pas installé (ollama pull {model}).",
    }
