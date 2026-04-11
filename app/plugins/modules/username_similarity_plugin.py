from app.plugins.base import BasePlugin
from app.services.username_similarity import find_similar_usernames


class UsernameSimilarityPlugin(BasePlugin):
    name = "username_similarity"
    description = "Compute similarity matches for username candidates."

    def run(self, data: dict) -> dict:
        base_username = (data.get("username") or data.get("base_username") or "").strip()
        candidates = data.get("candidates")

        if not base_username or not isinstance(candidates, list):
            return {"success": True, "matches": []}

        return {
            "success": True,
            "matches": find_similar_usernames(base_username, candidates),
        }
