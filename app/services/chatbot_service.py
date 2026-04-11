import re
from typing import Optional, Dict, Any


class ChatbotService:
    """
    Rule-based Assistant for ShadowSeek Chatbot.
    Session-Lernen: Merkt sich pro Instanz die letzten Nutzerfragen, Suchanfragen, Treffer, DeepSearch-Status, Hilfen.
    Kein Self-Modifying-Code, kein unkontrolliertes Lernen.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.session_memory = {
            "user_messages": [],
            "assistant_replies": [],
            "last_query": None,
            "last_results": None,
            "last_deepsearch": None,
            "given_hints": set(),
        }

    def handle_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        msg = message.strip().lower()
        context = context or {}
        self.session_memory["user_messages"].append(message)

        # Session-Lernen: Kontext merken
        if context.get("query"):
            self.session_memory["last_query"] = context["query"]
        if context.get("results") is not None:
            self.session_memory["last_results"] = context["results"]
        if context.get("deepsearch") is not None:
            self.session_memory["last_deepsearch"] = context["deepsearch"]

        # 1. Greetings
        if re.search(r"\b(hi|hallo|hello|hey|servus|guten tag|moin)\b", msg):
            reply = "Hallo! Ich bin der ShadowSeek Assistant. Wie kann ich bei der Profilsuche helfen?"
            self.session_memory["assistant_replies"].append(reply)
            return reply

        # 2. Hilfe/Erklärung
        if "hilfe" in msg or "was kannst" in msg:
            reply = self._help_text(context)
            self.session_memory["assistant_replies"].append(reply)
            self.session_memory["given_hints"].add("hilfe")
            return reply

        # 3. DeepSearch Erklärung
        if "deepsearch" in msg:
            reply = (
                "DeepSearch nutzt mehr Varianten und Quellen, um noch gründlicher nach Profilen zu suchen. "
                "Du kannst DeepSearch aktivieren, wenn du besonders viele oder seltene Treffer brauchst."
            )
            self.session_memory["assistant_replies"].append(reply)
            self.session_memory["given_hints"].add("deepsearch")
            return reply

        # 4. Warum vorher Fallback?
        if "fallback" in msg or "nicht konfiguriert" in msg or "503" in msg:
            reply = (
                "Der Chatbot war bisher im Fallback-Modus, weil noch kein echter Assistant aktiviert war. "
                "Jetzt beantworte ich deine Fragen regelbasiert – und später auch mit KI, sobald ein API-Key hinterlegt ist."
            )
            self.session_memory["assistant_replies"].append(reply)
            return reply

        # 5. Suchkontext auswerten
        if context:
            reply = self._contextual_response(msg, context)
            self.session_memory["assistant_replies"].append(reply)
            return reply

        # 6. Standardantwort
        reply = self._help_text(context)
        self.session_memory["assistant_replies"].append(reply)
        return reply

    def _help_text(self, context: Optional[Dict[str, Any]] = None) -> str:
        return (
            "ShadowSeek findet Profile auf vielen Plattformen. "
            "Stelle Fragen zur Profilsuche, zu Treffern oder wie du bessere Ergebnisse bekommst. "
            "Nutze DeepSearch für gründlichere Suchen."
        )

    def _contextual_response(self, msg: str, context: Dict[str, Any]) -> str:
        # Beispiel: Kontext enthält letzte Suchanfrage, Treffer, Plattformen, DeepSearch-Status
        query = context.get("query")
        platforms = context.get("platforms")
        results = context.get("results")
        deepsearch = context.get("deepsearch")
        n_results = len(results) if results else 0

        if query:
            resp = [f"Letzte Suche: '{query}'."]
            if platforms:
                resp.append(f"Plattformen: {', '.join(platforms)}.")
            resp.append(f"Treffer: {n_results}.")
            if deepsearch:
                resp.append("DeepSearch war aktiviert.")
            else:
                resp.append("DeepSearch war nicht aktiviert.")
            if n_results == 0:
                resp.append("Tipp: Probiere andere Schreibweisen oder aktiviere DeepSearch.")
            else:
                resp.append("Du kannst nach weiteren Details fragen oder DeepSearch nutzen.")
            return " ".join(resp)
        return self._help_text(context)
