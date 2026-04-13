from __future__ import annotations

from .env_guards import require_optional_integration
from .provider_utils import ExternalProviderClient


class YouTubeService:
    def __init__(self, api_key: str | None):
        self.api_key = (api_key or "").strip()
        self.client = ExternalProviderClient(provider_name="youtube", timeout_seconds=5.5, retries=2, rate_limit_seconds=0.1)

    def _guard(self):
        ok, error = require_optional_integration("YOUTUBE_API_KEY", "YouTube integration")
        if self.api_key:
            ok = True
            error = None
        if not ok:
            return {"enabled": False, "error": error}
        return None

    def _call(self, endpoint: str, params: dict):
        guard = self._guard()
        if guard:
            return guard
        merged = {**params, "key": self.api_key}
        result = self.client.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=merged)
        if not result.success:
            return {"enabled": True, "error": result.error, "items": []}
        return {"enabled": True, "items": result.data.get("items", [])}

    def get_channel_by_username(self, username: str):
        return self._call("channels", {"part": "snippet,statistics", "forUsername": username})

    def get_channel_by_handle(self, handle: str):
        query = (handle or "").lstrip("@")
        return self.search_channels(query)

    def get_channel_stats(self, channel_id: str):
        response = self._call("channels", {"part": "statistics,snippet", "id": channel_id})
        items = response.get("items", [])
        if items:
            stats = items[0].get("statistics", {})
            return {
                "enabled": True,
                "channel_id": channel_id,
                "subscriber_count": stats.get("subscriberCount"),
                "video_count": stats.get("videoCount"),
                "view_count": stats.get("viewCount"),
            }
        return {"enabled": response.get("enabled", False), "error": response.get("error"), "channel_id": channel_id}

    def get_videos(self, channel_id: str, limit: int = 10):
        response = self._call(
            "search",
            {"part": "snippet", "channelId": channel_id, "maxResults": max(1, min(int(limit), 25)), "order": "date", "type": "video"},
        )
        items = []
        for item in response.get("items", []):
            identifier = item.get("id", {})
            snippet = item.get("snippet", {})
            items.append({
                "video_id": identifier.get("videoId"),
                "title": snippet.get("title"),
                "published_at": snippet.get("publishedAt"),
                "url": f"https://www.youtube.com/watch?v={identifier.get('videoId')}" if identifier.get("videoId") else None,
            })
        return {"enabled": response.get("enabled", False), "error": response.get("error"), "items": items}

    def search_channels(self, query: str, limit: int = 8):
        response = self._call(
            "search",
            {"part": "snippet", "q": query, "maxResults": max(1, min(int(limit), 25)), "type": "channel"},
        )
        normalized = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            channel_id = (item.get("id", {}) or {}).get("channelId")
            custom_url = snippet.get("customUrl") or ""
            normalized.append(
                {
                    "platform": "youtube",
                    "channel_id": channel_id,
                    "username": (custom_url or "").lstrip("@"),
                    "display_name": snippet.get("channelTitle"),
                    "bio": snippet.get("description"),
                    "avatar_url": ((snippet.get("thumbnails") or {}).get("default") or {}).get("url"),
                    "profile_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                    "evidence": ["youtube_search"],
                }
            )
        return {"enabled": response.get("enabled", False), "error": response.get("error"), "items": normalized}
