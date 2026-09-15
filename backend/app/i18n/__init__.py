"""
Module i18n — systeme de traduction centralise de Fitapp.

Expose :
- SUPPORTED_LANGUAGES / DEFAULT_LANGUAGE / get_language / is_supported (languages.py)
- translate / get_translations / Translator (translator.py)
"""

from .languages import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    LanguageInfo,
    get_language,
    is_supported,
    list_languages,
)
from .translator import translator, translate, get_translations

__all__ = [
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "LanguageInfo",
    "get_language",
    "is_supported",
    "list_languages",
    "translator",
    "translate",
    "get_translations",
]
