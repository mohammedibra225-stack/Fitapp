"""
Service d'analyse d'image de repas via Hugging Face ZeroGPU.

Le modèle Qwen2.5-VL fait uniquement :
- identification visuelle des aliments
- estimation des portions
- estimation de la confiance

Le matching Food et le calcul nutritionnel restent entièrement
gérés par Fitapp.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Optional

from gradio_client import Client, handle_file

from app.config_ai import HUGGINGFACE_TOKEN
from app.schemas.meal_analysis import MealVisionAnalysis


logger = logging.getLogger("fitapp.huggingface_vision")


SPACE_ID = "mohammedibra/fitapp-vision"
API_NAME = "/analyze_meal"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class HuggingFaceVisionError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class HuggingFaceUnavailableError(HuggingFaceVisionError):
    def __init__(
        self,
        message: str = "Le service d'analyse des repas est temporairement indisponible.",
    ):
        super().__init__(message, 503)


class HuggingFaceTimeoutError(HuggingFaceVisionError):
    def __init__(
        self,
        message: str = "L'analyse du repas a pris trop de temps. Réessaie dans quelques instants.",
    ):
        super().__init__(message, 504)


class HuggingFaceInvalidResponseError(HuggingFaceVisionError):
    def __init__(
        self,
        message: str = "La réponse du modèle d'analyse est inexploitable.",
    ):
        super().__init__(message, 502)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class HuggingFaceVisionService:
    def __init__(self):
        self.client: Optional[Client] = None

    def _get_client(self) -> Client:
        """
        Initialise le client uniquement au premier appel.
        """

        if self.client is None:
            logger.info(
                "Connexion au Space Hugging Face : %s (authentifie=%s)",
                SPACE_ID,
                bool(HUGGINGFACE_TOKEN),
            )

            try:
                # gradio_client >= 6.x (Gradio 6 migration guide) a
                # renomme le parametre hf_token en token.
                self.client = Client(
                    SPACE_ID,
                    token=HUGGINGFACE_TOKEN,
                )
            except TypeError:
                # Compatibilite avec les versions plus anciennes de
                # gradio_client (< 6.x) qui utilisent encore hf_token.
                self.client = Client(
                    SPACE_ID,
                    hf_token=HUGGINGFACE_TOKEN,
                )

        return self.client

    # -----------------------------------------------------------------------
    # Normalisation
    # -----------------------------------------------------------------------

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            value = value.replace(",", ".")

            buffer = ""

            for char in value:
                if char.isdigit() or (
                    char == "." and "." not in buffer
                ):
                    buffer += char
                elif buffer:
                    break

            if buffer:
                try:
                    return float(buffer)
                except ValueError:
                    return None

        return None

    @classmethod
    def _clamp_confidence(
        cls,
        value: Any,
        default: float = 0.5,
    ) -> float:

        number = cls._coerce_float(value)

        if number is None:
            return default

        if number > 1:
            number = number / 100 if number <= 100 else 1

        return max(0.0, min(1.0, number))

    @staticmethod
    def _normalize_unit(value: Any) -> str:

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
            "kilogram": "kg",

            "milliliters": "ml",
            "millilitres": "ml",

            "liters": "l",
            "litres": "l",

            "pieces": "piece",
            "pc": "piece",
            "pcs": "piece",

            "units": "unit",

            "slice": "piece",
            "slices": "piece",
        }

        unit = aliases.get(unit, unit)

        allowed = {
            "g",
            "kg",
            "ml",
            "l",
            "piece",
            "unit",
            "pcs",
        }

        return unit if unit in allowed else "g"

    # -----------------------------------------------------------------------
    # Transformation de la réponse Qwen
    # -----------------------------------------------------------------------

    @classmethod
    def _sanitize_payload(cls, data: Any) -> dict:

        if not isinstance(data, dict):
            raise HuggingFaceInvalidResponseError(
                "Le modèle n'a pas renvoyé un objet JSON."
            )

        raw_foods = data.get("foods")

        if not isinstance(raw_foods, list):
            raw_foods = data.get("items", [])

        if not isinstance(raw_foods, list):
            raw_foods = []

        foods = []

        for entry in raw_foods:

            if not isinstance(entry, dict):
                continue

            name = (
                entry.get("name")
                or entry.get("food")
                or entry.get("label")
                or entry.get("food_name")
            )

            if not isinstance(name, str) or not name.strip():
                continue

            quantity = (
                cls._coerce_float(
                    entry.get("estimated_quantity")
                )
                or cls._coerce_float(
                    entry.get("estimated_quantity_g")
                )
                or cls._coerce_float(
                    entry.get("quantity")
                )
            )

            if quantity is None or quantity <= 0:
                quantity = 100.0

            # Protection contre une valeur aberrante
            quantity = min(quantity, 5000.0)

            unit = cls._normalize_unit(
                entry.get("unit")
            )

            # Notre modèle actuel retourne généralement
            # estimated_quantity_g sans unit.
            if "estimated_quantity_g" in entry:
                unit = "g"

            preparation = entry.get("preparation")

            if not isinstance(preparation, str):
                preparation = None

            alternatives_raw = entry.get("alternatives")

            if isinstance(alternatives_raw, list):
                alternatives = [
                    str(x).strip()
                    for x in alternatives_raw
                    if str(x).strip()
                ][:5]
            else:
                alternatives = []

            confidence = cls._clamp_confidence(
                entry.get("confidence")
            )

            foods.append(
                {
                    "name": name.strip()[:120],
                    "estimated_quantity": quantity,
                    "unit": unit,
                    "preparation": preparation,
                    "confidence": confidence,
                    "alternatives": alternatives,
                }
            )

            if len(foods) >= 15:
                break

        meal_type = data.get("meal_type")

        if not isinstance(meal_type, str):
            meal_type = "lunch"

        meal_type = meal_type.strip().lower()

        allowed_meal_types = {
            "breakfast",
            "lunch",
            "dinner",
            "snack",
        }

        if meal_type not in allowed_meal_types:
            meal_type = "lunch"

        overall_confidence = cls._clamp_confidence(
            data.get("overall_confidence"),
            default=(
                sum(food["confidence"] for food in foods)
                / len(foods)
                if foods
                else 0.0
            ),
        )

        notes_raw = data.get("notes")

        if isinstance(notes_raw, list):
            notes = [
                str(note).strip()
                for note in notes_raw
                if str(note).strip()
            ][:5]
        else:
            notes = []

        return {
            "meal_type": meal_type,
            "foods": foods,
            "overall_confidence": overall_confidence,
            "notes": notes,
        }

    # -----------------------------------------------------------------------
    # Analyse
    # -----------------------------------------------------------------------

    def analyze_meal(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> MealVisionAnalysis:

        if not image_bytes:
            raise HuggingFaceInvalidResponseError(
                "Aucune image à analyser."
            )

        temp_path = None

        try:

            # Gradio Client attend un filepath ou une URL.
            suffix = ".jpg"

            if mime_type == "image/png":
                suffix = ".png"
            elif mime_type == "image/webp":
                suffix = ".webp"
            elif mime_type in {
                "image/heic",
                "image/heif",
            }:
                suffix = ".jpg"

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:

                temp_file.write(image_bytes)
                temp_path = temp_file.name

            client = self._get_client()

            logger.info(
                "Envoi de l'image au Space Hugging Face..."
            )

            result = client.predict(
                image=handle_file(temp_path),
                api_name=API_NAME,
            )

            if not isinstance(result, str):
                raise HuggingFaceInvalidResponseError(
                    "Le modèle a renvoyé une réponse inattendue."
                )

            raw_text = result.strip()

            if not raw_text:
                raise HuggingFaceInvalidResponseError(
                    "Le modèle a renvoyé une réponse vide."
                )

            # ---------------------------------------------------------------
            # Nettoyage JSON
            # ---------------------------------------------------------------

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]

            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]

            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            raw_text = raw_text.strip()

            # Si le modèle ajoute du texte avant/après le JSON
            start = raw_text.find("{")
            end = raw_text.rfind("}")

            if start == -1 or end == -1:
                raise HuggingFaceInvalidResponseError(
                    "Le modèle n'a pas renvoyé de JSON exploitable."
                )

            raw_text = raw_text[start:end + 1]

            try:
                data = json.loads(raw_text)

            except json.JSONDecodeError as exc:

                logger.error(
                    "JSON Hugging Face invalide : %s",
                    raw_text[:500],
                )

                raise HuggingFaceInvalidResponseError(
                    "Le modèle d'analyse a renvoyé un JSON invalide."
                ) from exc

            sanitized = self._sanitize_payload(data)

            try:

                return MealVisionAnalysis.model_validate(
                    sanitized
                )

            except Exception as exc:

                logger.error(
                    "Réponse Hugging Face incompatible avec "
                    "MealVisionAnalysis : %s",
                    exc,
                )

                raise HuggingFaceInvalidResponseError(
                    "Le format de données renvoyé par le modèle est incorrect."
                ) from exc

        except HuggingFaceVisionError:
            raise

        except Exception as exc:

            logger.exception(
                "Erreur Hugging Face Vision : %s",
                exc,
            )

            raise HuggingFaceUnavailableError() from exc

        finally:

            if temp_path:

                try:
                    Path(temp_path).unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass

    # -----------------------------------------------------------------------
    # Health
    # -----------------------------------------------------------------------

    def health(self) -> dict:

        return {
            "available": True,
            "provider": "huggingface",
            "space": SPACE_ID,
            "endpoint": API_NAME,
            "model": "Qwen2.5-VL-3B-Instruct",
        }


huggingface_vision_service = HuggingFaceVisionService()