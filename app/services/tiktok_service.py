from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from .env_guards import feature_flag_enabled
from .provider_utils import ExternalProviderClient


_TIKTOK_SCRIPT_RE = re.compile(r'<script id="SIGI_STATE"[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)


class TikTokService:
    def __init__(self):
        self.client = ExternalProviderClient(provider_name="tiktok", timeout_seconds=5.5, retries=1, rate_limit_seconds=0.2)

    def get_profile_by_username(self, username: str) -> dict:
        handle = (username or "").strip().lstrip("@").lower()
        if not handle:
            return {"success": False, "error": "invalid_username", "profile": None}

        url = f"https://www.tiktok.com/@{handle}"
        response = self.client.get(url, headers={"Accept-Language": "en-US,en;q=0.9"})
        if not response.success:
            return {"success": False, "error": response.error, "profile": None}

        html = str(response.data.get("raw_text") or "")
        profile = self.extract_public_profile_signals(handle, html)
        if profile:
            return {"success": True, "error": None, "profile": profile}

        if feature_flag_enabled("ENABLE_TIKTOK_PLAYWRIGHT_FALLBACK", default=False):
            return {"success": False, "error": "playwright_fallback_not_implemented", "profile": None}

        return {"success": False, "error": "profile_not_parseable", "profile": None}

    def search_profile_candidates(self, username_variants: list[str]) -> list[dict]:
        candidates = []
        seen = set()
        for variant in username_variants[:8]:
            result = self.get_profile_by_username(variant)
            profile = result.get("profile")
            key = (profile or {}).get("username")
            if profile and key and key not in seen:
                seen.add(key)
                candidates.append(profile)
        return candidates

    def extract_public_profile_signals(self, username: str, html: str) -> dict | None:
        if not html:
            return None

        state = self._extract_state_json(html)
        if not state:
            return self._extract_from_meta(username, html)

        user_module = state.get("UserModule") if isinstance(state.get("UserModule"), dict) else {}
        users = user_module.get("users") if isinstance(user_module.get("users"), dict) else {}
        stats = user_module.get("stats") if isinstance(user_module.get("stats"), dict) else {}

        user_data = users.get(username) if username in users else (next(iter(users.values()), {}) if users else {})
        if not user_data:
            return self._extract_from_meta(username, html)

        unique_id = user_data.get("uniqueId") or username
        stat_data = stats.get(unique_id, {}) if isinstance(stats.get(unique_id), dict) else {}

        bio = user_data.get("signature") or ""
        links = extract_public_links_from_bio(bio)

        return {
            "platform": "tiktok",
            "username": unique_id,
            "display_name": user_data.get("nickname"),
            "bio": bio,
            "follower_count": stat_data.get("followerCount"),
            "following_count": stat_data.get("followingCount"),
            "like_count": stat_data.get("heartCount") or stat_data.get("heart"),
            "video_count": stat_data.get("videoCount"),
            "avatar_url": user_data.get("avatarLarger") or user_data.get("avatarMedium"),
            "links": links,
            "profile_url": f"https://www.tiktok.com/@{unique_id}",
            "evidence": ["public_profile", "sigi_state"],
        }

    def _extract_state_json(self, html: str) -> dict | None:
        match = _TIKTOK_SCRIPT_RE.search(html)
        if not match:
            return None
        raw = match.group(1)
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _extract_from_meta(self, username: str, html: str) -> dict | None:
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        if not title:
            return None
        return {
            "platform": "tiktok",
            "username": username,
            "display_name": title.replace("| TikTok", "").strip(),
            "bio": "",
            "follower_count": None,
            "following_count": None,
            "like_count": None,
            "video_count": None,
            "avatar_url": None,
            "links": [],
            "profile_url": f"https://www.tiktok.com/@{username}",
            "evidence": ["public_profile", "html_meta"],
        }


def extract_public_links_from_bio(bio: str) -> list[dict]:
    if not bio:
        return []
    pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    links = []
    for value in pattern.findall(bio):
        lowered = value.lower()
        if "instagram.com" in lowered:
            link_type = "instagram"
        elif "t.me" in lowered or "telegram.me" in lowered:
            link_type = "telegram"
        elif "discord.gg" in lowered or "discord.com" in lowered:
            link_type = "discord"
        elif "linktr.ee" in lowered:
            link_type = "linktree"
        elif "youtube.com" in lowered or "youtu.be" in lowered:
            link_type = "youtube"
        elif "twitch.tv" in lowered:
            link_type = "twitch"
        else:
            link_type = "public_link"
        links.append({"url": value, "type": link_type})
    return links
