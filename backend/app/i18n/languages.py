"""
Definition centralisee des langues supportees par Fitapp.

Toute langue ajoutee plus tard (ex: allemand, italien...) doit uniquement
etre declaree ici + avoir son fichier JSON dans locales/. Aucun autre
fichier du backend ne doit contenir de langue codee en dur.
"""

from dataclasses import dataclass
from typing import Dict, Literal, Optional

Direction = Literal["ltr", "rtl"]


@dataclass(frozen=True)
class LanguageInfo:
    code: str
    name: str
    direction: Direction

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "name": self.name,
            "direction": self.direction,
        }


# Langue utilisee quand une traduction ou une langue demandee est introuvable
DEFAULT_LANGUAGE = "fr"

# Source de verite unique pour les langues disponibles dans l'application
SUPPORTED_LANGUAGES: Dict[str, LanguageInfo] = {
    "fr": LanguageInfo(code="fr", name="Français", direction="ltr"),
    "en": LanguageInfo(code="en", name="English", direction="ltr"),
    "es": LanguageInfo(code="es", name="Español", direction="ltr"),
    "ar": LanguageInfo(code="ar", name="العربية", direction="rtl"),
}


def is_supported(language_code: Optional[str]) -> bool:
    """Verifie si un code langue est supporte par l'application."""
    return bool(language_code) and language_code in SUPPORTED_LANGUAGES


def get_language(language_code: str) -> LanguageInfo:
    """
    Retourne les infos d'une langue, ou celles de la langue par defaut
    si le code demande n'existe pas.
    """
    return SUPPORTED_LANGUAGES.get(
        language_code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]
    )


def list_languages() -> list[Dict[str, str]]:
    """Retourne la liste des langues au format serialisable (pour l'API)."""
    return [lang.to_dict() for lang in SUPPORTED_LANGUAGES.values()]
