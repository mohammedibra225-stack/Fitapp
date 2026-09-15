"""
Client HTTP dédié pour l'API Kie AI (modèle GPT-6 Astra).

Ce module est strictement isolé du reste du code :
- Récupère la clé API depuis os.getenv("KIE_API_KEY")
- Ne logge JAMAIS la clé API ni les secrets
- Gère les timeouts et les erreurs HTTP spécifiques (401, 403, 429, 500, etc.)
- Permet une transition facile vers un autre fournisseur d'API IA si nécessaire.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# Exceptions spécifiques pour la gestion propre des erreurs
class KieAIError(Exception):
    """Exception de base pour les erreurs Kie AI."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class KieAIAuthError(KieAIError):
    """Erreur 401/403 : clé API invalide ou non autorisée."""

    def __init__(self, message: str = "Clé d'API Kie AI non valide ou manquante."):
        super().__init__(message, status_code=401)


class KieAIRateLimitError(KieAIError):
    """Erreur 429 : quota dépassé ou trop de requêtes."""

    def __init__(self, message: str = "Quota d'appels Kie AI dépassé. Veuillez réessayer ultérieurement."):
        super().__init__(message, status_code=429)


class KieAITimeoutError(KieAIError):
    """Timeout lors de l'appel à Kie AI."""

    def __init__(self, message: str = "Le service IA a mis trop de temps à répondre."):
        super().__init__(message, status_code=504)


class KieAIInvalidResponseError(KieAIError):
    """Réponse inattendue ou corrompue reçue de Kie AI."""

    def __init__(self, message: str = "Réponse invalide reçue du modèle IA."):
        super().__init__(message, status_code=502)


class KieAIService:
    """Service d'interaction avec l'API Kie AI pour GPT-6 Astra."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("KIE_API_KEY", "")
        self.api_url = (
            api_url
            if api_url is not None
            else os.getenv("KIE_API_URL", "https://api.kie.ai/codex/v1/responses")
        )
        self.model = (
            model
            if model is not None
            else os.getenv("KIE_MODEL", "gpt-6-astra")
        )
        try:
            self.timeout = (
                timeout
                if timeout is not None
                else float(os.getenv("KIE_TIMEOUT_SECONDS", "45"))
            )
        except ValueError:
            self.timeout = 45.0

    def is_configured(self) -> bool:
        """Vérifie si la clé API est renseignée."""
        return bool(self.api_key and self.api_key.strip())

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envoie les messages à Kie AI / GPT-6 Astra et renvoie le dictionnaire de réponse.

        Gère l'unification des formats :
        - Supporte le format input standardisé de Kie AI
        - Supporte l'injection de tools
        - Gère les codes d'erreur HTTP et les exceptions de transport
        """
        if not self.is_configured():
            logger.error("KIE_API_KEY manquante ou non configurée.")
            raise KieAIAuthError("Clé d'API Kie AI non configurée.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Fitapp-Backend/1.0",
        }

        # Formatage des messages d'entrée
        # Note : l'API /codex/v1/responses n'accepte pas role='system' dans input (retourne 500).
        # On préfixe les instructions système dans le premier message ou bloc approprié.
        formatted_input: List[Dict[str, Any]] = []

        first_user_injected = False
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            text_val = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

            if not first_user_injected and system_instruction:
                text_val = f"[INSTRUCTIONS SYSTEME]\n{system_instruction}\n\n[MESSAGE]\n{text_val}"
                first_user_injected = True

            # Si role est system, mapper en user car l'API Kie AI n'admet que user ou assistant
            api_role = "assistant" if role == "assistant" else "user"

            formatted_input.append({
                "role": api_role,
                "content": [{"type": "input_text", "text": text_val}],
            })

        if not formatted_input and system_instruction:
            formatted_input.append({
                "role": "user",
                "content": [{"type": "input_text", "text": system_instruction}],
            })

        payload: Dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "input": formatted_input,
        }

        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.api_url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning(f"Timeout lors de l'appel à Kie AI: {exc}")
            raise KieAITimeoutError() from exc
        except httpx.RequestError as exc:
            logger.error(f"Erreur de communication avec Kie AI: {exc}")
            raise KieAIError(f"Impossible de contacter le service IA: {exc}", status_code=503) from exc

        # Analyse du code statut HTTP
        if response.status_code in (401, 403):
            logger.error(f"Erreur d'authentification Kie AI (status {response.status_code}).")
            raise KieAIAuthError("Authentification refusée par le service Kie AI.")

        if response.status_code == 429:
            logger.warning("Limite de requêtes atteinte sur Kie AI (429).")
            raise KieAIRateLimitError()

        if response.status_code >= 500:
            logger.error(f"Erreur serveur interne Kie AI (status {response.status_code}).")
            raise KieAIError("Le service Kie AI a rencontré une erreur interne.", status_code=502)

        if not response.is_success:
            logger.error(f"Erreur Kie AI HTTP {response.status_code}: {response.text}")
            raise KieAIError(f"Erreur retournée par le service IA (code {response.status_code}).", status_code=response.status_code)

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            logger.error("Impossible de parser le JSON retourné par Kie AI.")
            raise KieAIInvalidResponseError("Le service IA a renvoyé un contenu non JSON.") from exc

        return self._extract_output(data)

    def _extract_output(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait le texte de réponse ou les tool calls demandés par le modèle.
        Compatible avec les formats de sortie de Kie AI / GPT-6 Astra :
        - standard `/codex/v1/responses` (champ `output` avec blocs text et call)
        - chat-completion classique (`choices[0].message`)
        - format texte direct / status standard
        """
        result: Dict[str, Any] = {
            "text": "",
            "tool_calls": [],
            "raw": raw_data,
        }

        # 1. Format /codex/v1/responses
        if "output" in raw_data and isinstance(raw_data["output"], list):
            for block in raw_data["output"]:
                block_type = block.get("type")
                if block_type == "message":
                    contents = block.get("content", [])
                    for c in contents:
                        c_type = c.get("type")
                        # GPT-6 Astra renvoie 'output_text' ou 'text'
                        if c_type in ("output_text", "text"):
                            result["text"] += c.get("text", "")
                elif block_type in ("function_call", "tool_call", "call"):
                    # Support des arguments en objet ou en JSON string
                    raw_args = block.get("arguments") or block.get("function", {}).get("arguments", {})
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            raw_args = {}
                    result["tool_calls"].append({
                        "name": block.get("name") or block.get("function", {}).get("name"),
                        "arguments": raw_args,
                    })
            if result["text"] or result["tool_calls"]:
                return result

        # 2. Format chat/completions alternatif
        if "choices" in raw_data and isinstance(raw_data["choices"], list) and raw_data["choices"]:
            first_choice = raw_data["choices"][0]
            msg = first_choice.get("message", {})
            result["text"] = msg.get("content") or ""
            calls = msg.get("tool_calls") or []
            for call in calls:
                func = call.get("function", {})
                args = func.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                result["tool_calls"].append({
                    "name": func.get("name") or call.get("name"),
                    "arguments": args,
                })
            return result

        # 3. Champ texte ou message de premier niveau
        if "text" in raw_data and isinstance(raw_data["text"], str) and raw_data["text"].strip():
            result["text"] = raw_data["text"].strip()
            return result

        if "message" in raw_data and isinstance(raw_data["message"], str) and raw_data["message"].strip():
            result["text"] = raw_data["message"].strip()
            return result

        # Si le résultat n'est dans aucun format reconnu
        logger.warning(f"Structure de réponse Kie AI inattendue: {list(raw_data.keys())}")
        raise KieAIInvalidResponseError("La réponse du modèle IA n'a pas pu être analysée.")
