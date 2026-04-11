from app.plugins.base import BasePlugin
from app.services.risk_score import calculate_osint_risk


class RiskScorePlugin(BasePlugin):
    name = "risk_score"
    description = "Calculate an OSINT risk score."

    def run(self, data: dict) -> dict:
        riskdata = data.get("riskdata")
        if not isinstance(riskdata, dict):
            return {"success": True, "score": 0, "level": "low", "factors": []}

        result = calculate_osint_risk(riskdata)
        return {
            "success": True,
            "score": int(result.get("score", 0)),
            "level": result.get("level", "low"),
            "factors": result.get("factors", []),
        }
