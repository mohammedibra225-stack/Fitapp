"""
Moteur de traduction de Fitapp.

Charge les fichiers JSON de locales/ une seule fois (cache en memoire),
puis resout des cles en notation pointee ("nutrition.calories") avec
gestion du fallback et des parametres dynamiques ("Bienvenue, {name}").
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from .languages import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, is_supported

logger = logging.getLogger("fitapp.i18n")

LOCALES_DIR = Path(__file__).parent / "locales"


class TranslationKeyError(KeyError):
    """Levee en interne quand une cle de traduction est introuvable."""


class Translator:
    """
    Gere le chargement et la resolution des traductions.

    Usage :
        translator.translate("nutrition.calories", "fr")
        translator.translate("welcome", "fr", name="Mohammed")
    """

    def __init__(self, locales_dir: Path = LOCALES_DIR) -> None:
        self._locales_dir = locales_dir
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load_language_file(self, language_code: str) -> Dict[str, Any]:
        """Charge (et met en cache) le fichier JSON d'une langue."""
        if language_code in self._cache:
            return self._cache[language_code]

        file_path = self._locales_dir / f"{language_code}.json"

        if not file_path.exists():
            logger.warning(
                "Fichier de traduction introuvable pour '%s' (%s)",
                language_code,
                file_path,
            )
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            logger.error(
                "Fichier de traduction invalide pour '%s': %s",
                language_code,
                exc,
            )
            data = {}

        self._cache[language_code] = data
        return data

    @staticmethod
    def _resolve_key(data: Dict[str, Any], dotted_key: str) -> str:
        """Parcourt un dict imbrique via une cle en notation pointee."""
        node: Any = data

        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                raise TranslationKeyError(dotted_key)
            node = node[part]

        if not isinstance(node, str):
            raise TranslationKeyError(dotted_key)

        return node

    def translate(self, key: str, language: str, **params: Any) -> str:
        """
        Traduit une cle pour une langue donnee.

        - Si la langue est inconnue -> utilise DEFAULT_LANGUAGE.
        - Si la cle est absente dans la langue demandee -> fallback sur
          DEFAULT_LANGUAGE, puis sur "en" si besoin.
        - Si la cle n'existe nulle part -> renvoie la cle elle-meme
          (jamais d'exception qui casse l'app, mais l'erreur est loguee).
        - Les `params` sont injectes dans le texte via `{param}`.
        """
        target_language = language if is_supported(language) else DEFAULT_LANGUAGE

        languages_to_try = [target_language]
        if DEFAULT_LANGUAGE not in languages_to_try:
            languages_to_try.append(DEFAULT_LANGUAGE)
        if "en" not in languages_to_try:
            languages_to_try.append("en")

        text = None
        for lang_code in languages_to_try:
            data = self._load_language_file(lang_code)
            try:
                text = self._resolve_key(data, key)
                break
            except TranslationKeyError:
                continue

        if text is None:
            logger.warning("Cle de traduction introuvable: '%s'", key)
            return key

        try:
            return text.format(**params) if params else text
        except (KeyError, IndexError) as exc:
            logger.warning(
                "Parametre manquant pour la cle '%s': %s", key, exc
            )
            return text

    def get_translations(self, language: str) -> Dict[str, Any]:
        """Retourne l'integralite des traductions d'une langue (avec fallback)."""
        target_language = language if is_supported(language) else DEFAULT_LANGUAGE
        data = self._load_language_file(target_language)

        if not data and target_language != DEFAULT_LANGUAGE:
            data = self._load_language_file(DEFAULT_LANGUAGE)

        return data

    def clear_cache(self) -> None:
        """Utile pour les tests ou un rechargement a chaud des fichiers JSON."""
        self._cache.clear()


# Instance partagee utilisee dans toute l'application
translator = Translator()


def translate(key: str, language: str, **params: Any) -> str:
    """Raccourci fonctionnel vers translator.translate()."""
    return translator.translate(key, language, **params)


def get_translations(language: str) -> Dict[str, Any]:
    """Raccourci fonctionnel vers translator.get_translations()."""
    return translator.get_translations(language)
