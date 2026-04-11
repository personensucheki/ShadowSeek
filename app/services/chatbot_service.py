
import re
from typing import Optional, Dict, Any
import os
import requests


class ChatbotService:
    """
    Rule-based Assistant for ShadowSeek Chatbot.
    Session-Lernen: Merkt sich pro Instanz die letzten Nutzerfragen, Suchanfragen, Treffer, DeepSearch-Status, Hilfen.
    Kein Self-Modifying-Code, kein unkontrolliertes Lernen.
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
        # Wenn OpenAI-API-Key gesetzt: GPT-4-Antwort

        import logging
        api_key = self.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                prompt = self._build_prompt(message, context)
                logging.info(f"[GPT-4] Prompt: {prompt}")
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "Du bist ShadowSeek Assistant. Antworte natürlich, hilfreich, freundlich und menschlich auf Deutsch. Sei kreativ, aber bleibe sachlich und hilfreich. Wenn es um Profilsuche, Social Media, OSINT oder Websuche geht, gib konkrete Tipps. Sonst antworte wie ein echter Mensch."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.8
                }
                resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=18)
                logging.info(f"[GPT-4] Status: {resp.status_code}, Antwort: {resp.text[:300]}")
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"].strip()
                self.session_memory["assistant_replies"].append(answer)
                if len(self.session_memory["assistant_replies"]) > self._max_history:
                    self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
                return answer
            except Exception as e:
                logging.error(f"[GPT-4] Fehler: {e}")
                self.session_memory["assistant_replies"].append(f"[GPT-Fehler: {e}] Ich antworte regelbasiert...")
                if len(self.session_memory["assistant_replies"]) > self._max_history:
                    self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
                # Weiter mit Regel-basiert

        # ...bestehende Regel-basierte Logik...
            def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
                # Kontext für GPT-4: Letzte Nutzerfragen, ggf. letzte Suche
                prompt = message.strip()
                if context:
                    if context.get("query"):
                        prompt += f"\nLetzte Suche: {context['query']}"
                    if context.get("results"):
                        prompt += f"\nLetzte Treffer: {context['results']}"
                    if context.get("deepsearch"):
                        prompt += f"\nDeepSearch: {context['deepsearch']}"
                return prompt
        msg = message.strip().lower()
        context = context or {}
        # Begrenze History
        self.session_memory["user_messages"].append(message)
        if len(self.session_memory["user_messages"]) > self._max_history:
            self.session_memory["user_messages"] = self.session_memory["user_messages"][-self._max_history:]

        # Session-Lernen: Kontext merken und begrenzen
        if context.get("query"):
            self.session_memory["last_query"] = context["query"]
        if context.get("results") is not None:
            # Begrenze gespeicherte Treffer
            results = context["results"]
            if isinstance(results, list) and len(results) > self._max_results:
                results = results[:self._max_results]
            self.session_memory["last_results"] = results
        if context.get("deepsearch") is not None:
            self.session_memory["last_deepsearch"] = context["deepsearch"]

        # 1. Greetings
        if re.search(r"\b(hi|hallo|hello|hey|servus|guten tag|moin)\b", msg):
            reply = "Hallo! Ich bin der ShadowSeek Assistant. Wie kann ich bei der Profilsuche helfen?"
            self.session_memory["assistant_replies"].append(reply)
            if len(self.session_memory["assistant_replies"]) > self._max_history:
                self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
            return reply

        # 2. Hilfe/Erklärung
        if "hilfe" in msg or "was kannst" in msg:
            reply = self._help_text(context)
            self.session_memory["assistant_replies"].append(reply)
            if len(self.session_memory["assistant_replies"]) > self._max_history:
                self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
            self.session_memory["given_hints"].add("hilfe")
            return reply

        # 3. DeepSearch Erklärung
        if "deepsearch" in msg:
            reply = (
                "DeepSearch nutzt mehr Varianten und Quellen, um noch gründlicher nach Profilen zu suchen. "
                "Du kannst DeepSearch aktivieren, wenn du besonders viele oder seltene Treffer brauchst."
            )
            self.session_memory["assistant_replies"].append(reply)
            if len(self.session_memory["assistant_replies"]) > self._max_history:
                self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
            self.session_memory["given_hints"].add("deepsearch")
            return reply

        # 4. Warum vorher Fallback?
        if "fallback" in msg or "nicht konfiguriert" in msg or "503" in msg:
            reply = (
                "Der Chatbot war bisher im Fallback-Modus, weil noch kein echter Assistant aktiviert war. "
                "Jetzt beantworte ich deine Fragen regelbasiert – und später auch mit KI, sobald ein API-Key hinterlegt ist."
            )
            self.session_memory["assistant_replies"].append(reply)
            if len(self.session_memory["assistant_replies"]) > self._max_history:
                self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
            return reply

        # 5. Suchkontext auswerten
        if context:
            reply = self._contextual_response(msg, context)
            self.session_memory["assistant_replies"].append(reply)
            if len(self.session_memory["assistant_replies"]) > self._max_history:
                self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
            return reply

        # 6. Standardantwort
        reply = self._help_text(context)
        self.session_memory["assistant_replies"].append(reply)
        if len(self.session_memory["assistant_replies"]) > self._max_history:
            self.session_memory["assistant_replies"] = self.session_memory["assistant_replies"][-self._max_history:]
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
