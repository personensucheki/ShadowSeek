from __future__ import annotations

from typing import Any

from app.plugins.base import BasePlugin
from app.services.username_patterns import analyze_username_patterns


class UsernamePatternsPlugin(BasePlugin):
    name = "username_patterns"
    description = "Analyze stylistic patterns of a username."
    version = "1.0.0"
    produces = ["style", "tags", "possible_year", "pattern_family"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        username = str(context.get("username") or "").strip()
        if not username:
            return {
                "success": True,
                "data": {
                    "style": "unknown",
                    "tags": [],
                    "possible_year": None,
                    "pattern_family": "unknown",
                },
            }

        return {"success": True, "data": analyze_username_patterns(username)}
