"""
Service d'orchestration de l'Assistant IA Fitapp.

Ce module gère :
- L'historique des conversations persisté en base (modèles Conversation et Message)
- La génération du system prompt multilingue et adapté aux règles Fitapp
- La communication avec Kie AI (GPT-6 Astra)
- La boucle d'exécution sécurisée des tools Fitapp (Function Calling)
- La persistance des messages et le renvoi de la réponse structurée.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import Conversation, Message
from app.models.enums import MessageRole
from app.models.user import User
from app.schemas.assistant import AssistantChatResponse, ToolCallRecord
from app.services.assistant_tools import FITAPP_TOOLS_DEFINITIONS, FitappToolsExecutor
from app.services.kie_ai_service import KieAIService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """Tu es l'assistant officiel de Fitapp, l'application complète de fitness, nutrition et sport.

Règles fondamentales :
1. Tu peux répondre aux questions générales de manière claire, concise, bienveillante et motivante.
2. Tu réponds aux questions spécifiques concernant Fitapp, ses fonctionnalités (nutrition, suivi des repas, inventaire frigo/placard, planification d'entraînement, récupération).
3. Pour les données personnelles et nutritionnelles de l'utilisateur :
   - UTILISE TOUJOURS LES OUTILS (tools) disponibles pour obtenir les vraies données.
   - Ne JAMAIS inventer de données nutritionnelles (calories, protéines, glucides, lipides) si la base Fitapp possède les informations ou permet de les calculer.
   - Privilégie TOUJOURS les calculs du backend de Fitapp (ex: calculate_meal, get_today_nutrition, search_food).
   - Ne prétends JAMAIS avoir effectué une action qui n'a pas été exécutée.
4. Pour les questions d'entraînement et de sport, réfère-toi aux sports et recommandations de l'utilisateur via get_training.
5. Langue : Réponds toujours dans la langue utilisée par l'utilisateur ou sa langue préférée ({language}). Fitapp supporte le français, l'anglais, l'arabe et l'espagnol.
6. Ne divulgue jamais d'informations techniques internes (clés d'API, requêtes SQL, architecture serveur).
"""


class AssistantAIService:
    """Service d'orchestration pour le chatbot IA conversationnel."""

    def __init__(
        self,
        db: Session,
        kie_service: Optional[KieAIService] = None,
    ):
        self.db = db
        self.kie_service = kie_service or KieAIService()

    def process_chat(
        self,
        message: str,
        user_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        language: Optional[str] = None,
    ) -> AssistantChatResponse:
        """
        Traite une requête utilisateur de chat de bout en bout.
        """
        # 1. Vérification / Récupération de l'utilisateur
        user: Optional[User] = None
        if user_id:
            user = self.db.get(User, user_id)

        user_lang = language or (user.preferred_language if user else "fr")

        # 2. Récupération ou création de la conversation
        conversation: Optional[Conversation] = None
        if conversation_id:
            conversation = self.db.get(Conversation, conversation_id)

        if not conversation:
            # Si pas d'utilisateur spécifié, on en cherche un ou on en crée une sans utilisateur
            # Notons que la table conversations a user_id NOT NULL dans le schema Postgres.
            if user:
                conversation = Conversation(
                    id=conversation_id or uuid4(),
                    user_id=user.id,
                    title=message[:50],
                )
                self.db.add(conversation)
                self.db.commit()
                self.db.refresh(conversation)

        # 3. Chargement de l'historique récent de la conversation
        history_messages: List[Dict[str, Any]] = []
        if conversation:
            # Récupérer les 10 derniers messages pour garder un contexte pertinent
            db_messages = (
                self.db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                .scalars()
                .all()
            )
            # Inverser pour ordre chronologique
            for msg in reversed(db_messages):
                role_str = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
                history_messages.append({
                    "role": role_str,
                    "content": msg.content,
                })

        # Ajouter le message utilisateur courant à la session
        history_messages.append({"role": "user", "content": message})

        # 4. Préparation du System Prompt
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(language=user_lang)

        # 5. Instanciation de l'exécuteur de tools Fitapp
        tools_executor = FitappToolsExecutor(
            db=self.db,
            user_id=user.id if user else None,
            language=user_lang,
        )

        executed_tool_records: List[ToolCallRecord] = []

        # 6. Appel Kie AI (GPT-6 Astra) avec boucle de tool calling (max 3 itérations)
        current_messages = list(history_messages)
        max_tool_iterations = 3
        final_answer = ""

        for iteration in range(max_tool_iterations):
            ai_output = self.kie_service.generate_response(
                messages=current_messages,
                tools=FITAPP_TOOLS_DEFINITIONS,
                system_instruction=system_instruction,
            )

            tool_calls = ai_output.get("tool_calls", [])

            # Si l'IA n'appelle aucun outil, on a notre réponse finale
            if not tool_calls:
                final_answer = ai_output.get("text", "")
                break

            # Sinon, exécuter chaque outil demandé
            for call in tool_calls:
                t_name = call.get("name")
                t_args = call.get("arguments", {})
                if isinstance(t_args, str):
                    try:
                        t_args = json.loads(t_args)
                    except json.JSONDecodeError:
                        t_args = {}

                t_result = tools_executor.execute(t_name, t_args)

                executed_tool_records.append(
                    ToolCallRecord(
                        tool_name=t_name,
                        arguments=t_args,
                        result=t_result,
                    )
                )

                # Injecter le résultat de l'outil dans les messages pour la boucle suivante
                current_messages.append({
                    "role": "system",
                    "content": (
                        f"[Résultat de l'outil Fitapp '{t_name}']:\n"
                        f"{json.dumps(t_result, ensure_ascii=False)}"
                    ),
                })

            # Si c'est la dernière itération, demander au modèle de formuler la synthèse
            if iteration == max_tool_iterations - 1:
                final_output = self.kie_service.generate_response(
                    messages=current_messages,
                    tools=None,
                    system_instruction=system_instruction,
                )
                final_answer = final_output.get("text", "")

        # Sécurité réponse vide
        if not final_answer:
            final_answer = "Je n'ai pas pu obtenir de réponse complète. Que souhaites-tu savoir d'autre ?"

        # 7. Persistance en base des messages (si la conversation existe)
        if conversation:
            user_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message,
                language_code=user_lang,
            )
            self.db.add(user_msg)

            assistant_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=final_answer,
                language_code=user_lang,
                context_metadata={
                    "tool_calls": [t.model_dump() for t in executed_tool_records]
                } if executed_tool_records else None,
            )
            self.db.add(assistant_msg)
            self.db.commit()

        conv_id_str = str(conversation.id) if conversation else str(conversation_id or uuid4())

        return AssistantChatResponse(
            message=final_answer,
            conversation_id=conv_id_str,
            tool_calls=executed_tool_records,
        )
