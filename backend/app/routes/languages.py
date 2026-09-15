"""
Routes API pour le systeme multilingue.

GET /languages                  -> liste des langues disponibles
GET /languages/{language}       -> infos d'une langue
GET /translations/{language}    -> traductions completes d'une langue
"""

from fastapi import APIRouter, HTTPException

from app.i18n import (
    get_language,
    get_translations,
    is_supported,
    list_languages,
)

router = APIRouter(tags=["i18n"])


@router.get("/languages")
def get_all_languages():
    """Retourne les 4 langues disponibles dans Fitapp."""
    return {"languages": list_languages()}


@router.get("/languages/{language}")
def get_one_language(language: str):
    """Retourne les informations d'une langue precise (code, nom, direction)."""
    if not is_supported(language):
        raise HTTPException(
            status_code=404,
            detail=f"Langue '{language}' non supportee.",
        )

    return get_language(language).to_dict()


@router.get("/translations/{language}")
def get_language_translations(language: str):
    """Retourne l'integralite des traductions d'une langue."""
    if not is_supported(language):
        raise HTTPException(
            status_code=404,
            detail=f"Langue '{language}' non supportee.",
        )

    return {
        "language": language,
        "translations": get_translations(language),
    }
