from __future__ import annotations


def clamp_score(value: float | int, minimum: int = 0, maximum: int = 100) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = minimum
    return max(minimum, min(maximum, score))


def confidence_from_score(score: int) -> str:
    score = clamp_score(score)
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def score_from_evidence(evidence: list[dict], base: int = 0) -> int:
    score = int(base)
    for item in evidence or []:
        weight = item.get("weight", 0)
        try:
            score += int(weight)
        except (TypeError, ValueError):
            continue
    return clamp_score(score)
