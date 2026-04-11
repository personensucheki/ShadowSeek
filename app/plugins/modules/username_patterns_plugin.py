from app.plugins.base import BasePlugin
from app.services.username_patterns import analyze_username_patterns


class UsernamePatternsPlugin(BasePlugin):
    name = "username_patterns"
    description = "Analyze stylistic patterns of a username."

    def run(self, data: dict) -> dict:
        username = (data.get("username") or data.get("base_username") or "").strip()
        if not username:
            return {
                "success": True,
                "style": "unknown",
                "tags": [],
                "possible_year": None,
                "pattern_family": "unknown",
            }

        result = analyze_username_patterns(username)
        return {"success": True, **result}
