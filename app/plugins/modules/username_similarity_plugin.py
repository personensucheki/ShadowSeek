from __future__ import annotations

from typing import Any

from app.plugins.base import BasePlugin
from app.services.username_similarity import find_similar_usernames


class UsernameSimilarityPlugin(BasePlugin):
    name = "username_similarity"
    description = "Compute similarity matches for username candidates."
    version = "1.0.0"
    produces = ["matches"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        username = str(context.get("username") or "").strip()
        if not username:
            return {"success": True, "data": {"matches": []}}

        candidates = [
            candidate
            for candidate in {
                username,
                f"{username}_",
                f"{username}.official",
                f"{username}tv",
                f"{username}live",
                f"real{username}",
                f"{username}01",
                f"{username}2024",
            }
            if candidate
        ]
        return {
            "success": True,
            "data": {"matches": find_similar_usernames(username, candidates)},
        }
