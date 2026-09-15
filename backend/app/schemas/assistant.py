"""
Schémas Pydantic pour la fonctionnalité Assistant IA (Kie AI / GPT-6 Astra).

Fournit les contrats d'entrée et de sortie pour :
- les requêtes utilisateur (POST /api/v1/assistant/chat)
- les réponses de l'assistant (avec métadonnées et tool_calls éventuels)
- l'historique des conversations
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    """Trace d'un outil métier Fitapp exécuté par l'assistant."""

    tool_name: str = Field(description="Nom de l'outil exécuté (ex: get_today_nutrition)")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Paramètres passés à l'outil")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Résultat retourné par l'outil")


class AssistantChatRequest(BaseModel):
    """Payload d'entrée pour la discussion avec l'Assistant IA."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message texte saisi par l'utilisateur",
        examples=["Combien de protéines me reste-t-il aujourd'hui ?"],
    )
    user_id: Optional[UUID] = Field(
        default=None,
        description="UUID de l'utilisateur Fitapp. Si omis ou non trouvé, l'assistant répond en mode invité.",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="UUID de la conversation existante. Si omis, une nouvelle conversation est créée.",
    )
    language: Optional[str] = Field(
        default=None,
        max_length=5,
        description="Code de langue forcée (ex: 'fr', 'en', 'es', 'ar'). Sinon, déduit du profil ou du message.",
    )


class AssistantChatResponse(BaseModel):
    """Réponse structurée retournée à l'application mobile React Native."""

    message: str = Field(
        ...,
        description="Réponse textuelle formulée par GPT-6 Astra pour l'utilisateur",
    )
    conversation_id: str = Field(
        ...,
        description="UUID de la conversation sous forme de chaîne pour les requêtes suivantes",
    )
    tool_calls: List[ToolCallRecord] = Field(
        default_factory=list,
        description="Liste des outils Fitapp déclenchés pour préparer cette réponse",
    )


class MessageOut(BaseModel):
    """Représentation d'un message archivé dans l'historique."""

    id: UUID
    role: str
    content: str
    language_code: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Représentation d'une conversation et de ses messages."""

    id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime
    messages: List[MessageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
