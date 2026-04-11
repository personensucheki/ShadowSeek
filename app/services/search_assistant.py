from typing import Dict, Any, List

class RuleBasedSearchAssistant:
    def __init__(self, last_search_result: Dict[str, Any], last_summary: Dict[str, Any]):
        self.result = last_search_result
        self.summary = last_summary

    def get_response(self) -> str:
        if not self.result['results']:
            return self._no_results_response()
        if self.summary['confidence_distribution']['high'] > 0:
            return self._strong_result_response()
        if self.summary['confidence_distribution']['medium'] > 0:
            return self._medium_result_response()
        return self._weak_result_response()

    def _no_results_response(self) -> str:
        suggestions = [
            "Prüfe die Schreibweise des Usernames.",
            "Nutze DeepSearch für mehr Varianten und Quellen.",
            "Füge weitere Plattformen oder einen Clan-/Echtnamen hinzu.",
        ]
        return (
            "Keine Treffer gefunden.\n"
            "Tipps: " + " ".join(suggestions)
        )

    def _strong_result_response(self) -> str:
        best = self.result['results'][0]
        reasons = ", ".join(best.get('match_reasons', []))
        return (
            f"Der stärkste Treffer ist {best.get('username')} auf {best.get('platform')}.\n"
            f"Begründung: {reasons}.\n"
            f"Confidence: {best.get('confidence').upper()}\n"
        )

    def _medium_result_response(self) -> str:
        best = self.result['results'][0]
        return (
            f"Es gibt einen brauchbaren Treffer: {best.get('username')} auf {best.get('platform')}.\n"
            f"Confidence: {best.get('confidence').upper()}.\n"
            "Für noch bessere Ergebnisse aktiviere DeepSearch oder ergänze weitere Angaben."
        )

    def _weak_result_response(self) -> str:
        return (
            "Nur schwache Treffer gefunden.\n"
            "Die Ergebnisse sind unsicher. Prüfe weitere Varianten, Plattformen oder aktiviere DeepSearch."
        )

# Beispiel-Nutzung:
# assistant = RuleBasedSearchAssistant(result, summary)
# print(assistant.get_response())
