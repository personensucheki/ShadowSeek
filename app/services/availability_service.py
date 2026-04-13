from __future__ import annotations

from .provider_utils import ExternalProviderClient


PLATFORM_PATTERNS = {
    "instagram": "https://www.instagram.com/{username}/",
    "tiktok": "https://www.tiktok.com/@{username}",
    "youtube": "https://www.youtube.com/@{username}",
    "twitch": "https://www.twitch.tv/{username}",
    "reddit": "https://www.reddit.com/user/{username}",
    "telegram": "https://t.me/{username}",
    "x": "https://x.com/{username}",
    "discord": "https://discord.com/users/{username}",
}


def check_username_availability(username: str, platforms: list[str] | None = None) -> list[dict]:
    normalized = (username or "").strip().lstrip("@").lower()
    if not normalized:
        return []

    client = ExternalProviderClient(provider_name="availability", timeout_seconds=4.0, retries=1, rate_limit_seconds=0.15)
    selected = platforms or list(PLATFORM_PATTERNS.keys())

    results = []
    for platform in selected:
        pattern = PLATFORM_PATTERNS.get(platform)
        if not pattern:
            continue

        url = pattern.format(username=normalized)
        response = client.get(url)
        if not response.success:
            state = "unclear_or_rate_limited" if response.transient else "not_found"
        else:
            raw = str(response.data.get("raw_text") or "").lower()
            if response.status_code == 200 and normalized in raw:
                state = "claimed"
            elif response.status_code == 404:
                state = "not_found"
            else:
                state = "likely_claimed"

        results.append({
            "platform": platform,
            "username": normalized,
            "state": state,
            "url": url,
        })

    return results
