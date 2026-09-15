"""
Routes API pour l'Assistant IA Fitapp.

Endpoint principal :
    POST /api/v1/assistant/chat

Permet à l'application mobile React Native / Expo de discuter naturellement
avec l'assistant conversationnel (Kie AI / GPT-6 Astra) couplé aux outils Fitapp.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_ai_service import AssistantAIService
from app.services.kie_ai_service import (
    KieAIAuthError,
    KieAIError,
    KieAIInvalidResponseError,
    KieAIRateLimitError,
    KieAITimeoutError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Envoyer un message à l'Assistant IA Fitapp",
    description="Discute avec l'Assistant IA (GPT-6 Astra) capable de répondre aux questions générales et d'exécuter des outils Fitapp.",
)
def chat_with_assistant(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
) -> AssistantChatResponse:
    """
    Point d'entrée du chat Assistant IA.
    Gère les erreurs proprement et ne renvoie jamais de traceback ou de clé secrète au client.
    """
    service = AssistantAIService(db=db)

    try:
        response = service.process_chat(
            message=payload.message,
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            language=payload.language,
        )
        return response

    except KieAIAuthError as exc:
        logger.error(f"Erreur d'authentification assistant IA : {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service Assistant IA est temporairement indisponible (erreur de configuration d'authentification).",
        )

    except KieAIRateLimitError as exc:
        logger.warning(f"Limite de requêtes atteinte pour l'assistant IA : {exc}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de requêtes vers l'assistant IA. Merci de patienter un instant avant de réessayer.",
        )

    except KieAITimeoutError as exc:
        logger.warning(f"Timeout du service assistant IA : {exc}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Le service Assistant IA a mis trop de temps à répondre. Veuillez réessayer.",
        )

    except KieAIInvalidResponseError as exc:
        logger.error(f"Réponse invalide de l'assistant IA : {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse invalide reçue de l'Assistant IA.",
        )

    except KieAIError as exc:
        logger.error(f"Erreur générale assistant IA : {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le service Assistant IA est temporairement indisponible.",
        )

    except Exception as exc:
        logger.exception(f"Erreur inattendue dans la route assistant chat : {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors de l'échange avec l'assistant.",
        )
