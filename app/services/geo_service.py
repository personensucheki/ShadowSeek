from __future__ import annotations

import re


def normalize_location(plz: str | None = None, location_text: str | None = None) -> dict:
    postal = (plz or "").strip()
    text = (location_text or "").strip()

    if postal and re.fullmatch(r"\d{5}", postal):
        return {
            "normalized_location": postal,
            "region": "DE",
            "country": "Germany",
            "confidence": "medium",
        }

    if text:
        normalized = re.sub(r"\s+", " ", text).strip()
        country = "Germany" if any(token in normalized.lower() for token in ["de", "deutsch", "berlin", "muenchen", "hamburg"]) else "unknown"
        confidence = "medium" if country != "unknown" else "low"
        return {
            "normalized_location": normalized,
            "region": "DE" if country == "Germany" else "unknown",
            "country": country,
            "confidence": confidence,
        }

    return {
        "normalized_location": None,
        "region": None,
        "country": None,
        "confidence": "low",
    }
