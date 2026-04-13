from __future__ import annotations

import json
import logging
from typing import Any

from .score_utils import clamp_score


LOGGER = logging.getLogger("profile_analysis")
SUSPICIOUS_KEYWORDS = {
    "crypto": 12,
    "guaranteed": 10,
    "forex": 12,
    "airdrop": 12,
    "free money": 15,
    "dm me": 6,
    "investment": 8,
    "support": 5,
    "verify": 6,
}


def analyze_profile(payload: dict[str, Any], *, openai_api_key: str | None = None) -> dict:
    text = " ".join(
        str(payload.get(key) or "")
        for key in ["username", "display_name", "bio", "platform"]
    ).lower()
    links = payload.get("links") or []

    indicators = []
    fake_score = 8
    bot_score = 5
    scam_score = 5

    for keyword, weight in SUSPICIOUS_KEYWORDS.items():
        if keyword in text:
            indicators.append(f"keyword:{keyword}")
            scam_score += weight
            bot_score += weight // 2

    if isinstance(links, list) and len(links) > 6:
        indicators.append("link_overload")
        bot_score += 10

    posting_meta = payload.get("posting_metadata") or {}
    if isinstance(posting_meta, dict):
        burstiness = posting_meta.get("burstiness")
        if isinstance(burstiness, (int, float)) and burstiness > 0.8:
            indicators.append("posting_burstiness_high")
            bot_score += 12

    fake_score = clamp_score(fake_score + (bot_score // 3) + (scam_score // 4))
    bot_score = clamp_score(bot_score)
    scam_score = clamp_score(scam_score)

    risk_level = "low"
    max_score = max(fake_score, bot_score, scam_score)
    if max_score >= 80:
        risk_level = "high"
    elif max_score >= 50:
        risk_level = "medium"

    explanation = "Heuristic risk analysis based on public profile signals."
    llm_used = False

    if openai_api_key:
        llm_result = _optional_openai_classifier(payload, openai_api_key)
        if llm_result:
            llm_used = True
            explanation = llm_result.get("explanation") or explanation
            fake_score = clamp_score((fake_score + int(llm_result.get("fake_score", fake_score))) / 2)
            bot_score = clamp_score((bot_score + int(llm_result.get("bot_score", bot_score))) / 2)
            scam_score = clamp_score((scam_score + int(llm_result.get("scam_score", scam_score))) / 2)
            risk_level = llm_result.get("risk_level") or risk_level
            indicators.extend(llm_result.get("indicators") or [])

    return {
        "fake_score": fake_score,
        "bot_score": bot_score,
        "scam_score": scam_score,
        "risk_level": risk_level,
        "indicators": sorted(set(indicators)),
        "explanation": explanation,
        "llm_used": llm_used,
    }


def _optional_openai_classifier(payload: dict, api_key: str) -> dict | None:
    try:
        from openai import OpenAI
    except Exception:
        return None

    try:
        client = OpenAI(api_key=api_key, timeout=8)
        prompt = {
            "task": "score_profile_risk",
            "input": payload,
            "output_schema": {
                "fake_score": "0-100",
                "bot_score": "0-100",
                "scam_score": "0-100",
                "risk_level": "low|medium|high",
                "indicators": ["..."],
                "explanation": "string",
            },
        }
        response = client.responses.create(
            model="gpt-5-mini",
            input=[{"role": "user", "content": [{"type": "input_text", "text": json.dumps(prompt)}]}],
        )
        text = (response.output_text or "").strip()
        if not text.startswith("{"):
            return None
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return None
        return parsed
    except Exception as error:
        LOGGER.warning("OpenAI profile analysis failed: %s", error)
        return None
