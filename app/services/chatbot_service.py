import logging
import re
from typing import Any, Dict, Optional

import requests


class ChatbotService:
    """
    Rule-based assistant with optional OpenAI enhancement.
    The fallback path must always keep working, even without API access.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self._max_history = 10
        self._max_results = 10
        self.session_memory = {
            "user_messages": [],
            "assistant_replies": [],
            "last_query": None,
            "last_results": None,
            "last_deepsearch": None,
            "given_hints": set(),
        }

    def handle_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        api_key = self.openai_api_key
        if api_key:
            try:
                prompt = self._build_prompt(message, context)
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Du bist ShadowSeek Assistant. Antworte natuerlich, "
                                    "hilfreich und sachlich auf Deutsch. Wenn es um "
                                    "Profilsuche, Social Media, OSINT oder Websuche geht, "
                                    "gib konkrete Tipps."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 400,
                        "temperature": 0.8,
                    },
                    timeout=18,
                )
                response.raise_for_status()
                answer = response.json()["choices"][0]["message"]["content"].strip()
                self._remember_reply(answer)
                return answer
            except Exception as error:
                logging.warning("OpenAI chatbot fallback activated: %s", error)

        return self._handle_rule_based(message, context or {})

    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        prompt = (message or "").strip()
        context = context or {}

        if context.get("query"):
            prompt += f"\nLetzte Suche: {context['query']}"
        if context.get("results"):
            prompt += f"\nLetzte Treffer: {context['results']}"
        if context.get("deepsearch") is not None:
            prompt += f"\nDeepSearch: {context['deepsearch']}"

        return prompt.strip()

    def _handle_rule_based(self, message: str, context: Dict[str, Any]) -> str:
        msg = (message or "").strip().lower()
        self.session_memory["user_messages"].append(message)
        self.session_memory["user_messages"] = self.session_memory["user_messages"][-self._max_history :]

        if context.get("query"):
            self.session_memory["last_query"] = context["query"]
        if context.get("results") is not None:
            results = context["results"]
            if isinstance(results, list):
                results = results[: self._max_results]
            self.session_memory["last_results"] = results
        if context.get("deepsearch") is not None:
            self.session_memory["last_deepsearch"] = context["deepsearch"]

        if re.search(r"\b(hi|hallo|hello|hey|servus|guten tag|moin)\b", msg):
            reply = "Hallo! Ich bin der ShadowSeek Assistant. Wie kann ich bei der Profilsuche helfen?"
            self._remember_reply(reply)
            return reply

        if "hilfe" in msg or "was kannst" in msg:
            reply = self._help_text(context)
            self.session_memory["given_hints"].add("hilfe")
            self._remember_reply(reply)
            return reply

        if "deepsearch" in msg:
            reply = (
                "DeepSearch nutzt mehr Varianten und Quellen, um noch gruendlicher nach "
                "Profilen zu suchen. Du kannst DeepSearch aktivieren, wenn du besonders "
                "viele oder seltene Treffer brauchst."
            )
            self.session_memory["given_hints"].add("deepsearch")
            self._remember_reply(reply)
            return reply

        if "fallback" in msg or "nicht konfiguriert" in msg or "503" in msg:
            reply = (
                "Der Chatbot war bisher im Fallback-Modus, weil noch kein echter Assistant "
                "aktiviert war. Jetzt beantworte ich deine Fragen regelbasiert und spaeter "
                "auch mit KI, sobald ein API-Key hinterlegt ist."
            )
            self._remember_reply(reply)
            return reply

        if context:
            reply = self._contextual_response(context)
            self._remember_reply(reply)
            return reply

        reply = self._help_text(context)
        self._remember_reply(reply)
        return reply

    def _help_text(self, context: Optional[Dict[str, Any]] = None) -> str:
        return (
            "ShadowSeek findet Profile auf vielen Plattformen. Stelle Fragen zur "
            "Profilsuche, zu Treffern oder wie du bessere Ergebnisse bekommst. "
            "Nutze DeepSearch fuer gruendlichere Suchen."
        )

    def _contextual_response(self, context: Dict[str, Any]) -> str:
        query = context.get("query")
        platforms = context.get("platforms")
        results = context.get("results")
        deepsearch = context.get("deepsearch")
        result_count = len(results) if isinstance(results, list) else 0

        if not query:
            return self._help_text(context)

        parts = [f"Letzte Suche: '{query}'."]
        if platforms:
            parts.append(f"Plattformen: {', '.join(platforms)}.")
        parts.append(f"Treffer: {result_count}.")
        parts.append(
            "DeepSearch war aktiviert." if deepsearch else "DeepSearch war nicht aktiviert."
        )

        if result_count == 0:
            parts.append("Tipp: Probiere andere Schreibweisen oder aktiviere DeepSearch.")
        else:
            parts.append("Du kannst nach weiteren Details fragen oder DeepSearch nutzen.")

        return " ".join(parts)

    def _remember_reply(self, reply: str) -> None:
        self.session_memory["assistant_replies"].append(reply)
        self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][
            -self._max_history :
        ]
