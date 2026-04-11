from __future__ import annotations

from typing import Any

from app.plugins.base import BasePlugin
from app.services.risk_score import calculate_osint_risk


class RiskScorePlugin(BasePlugin):
    name = "risk_score"
    description = "Calculate an OSINT risk score."
    version = "1.0.0"
    requires = [
        "username_similarity",
        "username_patterns",
        "domain_osint",
    ]
    produces = ["score", "level", "factors"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        plugin_results = context.get("plugin_results")
        plugin_results = plugin_results if isinstance(plugin_results, dict) else {}

        similarity_data = plugin_results.get("username_similarity", {}).get("data", {})
        patterns_data = plugin_results.get("username_patterns", {}).get("data", {})
        domain_data = plugin_results.get("domain_osint", {}).get("data", {})

        factors = []
        if patterns_data.get("possible_year"):
            factors.append("Username pattern exposes possible year")

        riskdata = {
            "has_real_name": bool(context.get("real_name")),
            "has_age": context.get("age") is not None,
            "has_location": bool(context.get("postal_code")),
            "has_email": bool(domain_data.get("emails")),
            "username_count": len(similarity_data.get("matches", [])),
            "platform_count": len(domain_data.get("domains", [])),
            "has_reverse_image": bool(context.get("image_path")),
            "image_reuse_score": 80 if similarity_data.get("matches") else 0,
        }

        result = calculate_osint_risk(riskdata)
        factors.extend(item for item in result.get("factors", []) if item not in factors)

        return {
            "success": True,
            "data": {
                "score": int(result.get("score", 0)),
                "level": result.get("level", "low"),
                "factors": factors,
            },
        }
