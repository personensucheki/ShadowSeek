from __future__ import annotations

from typing import Any

from app.plugins.base import BasePlugin
from app.services.domain_osint import analyze_domain_osint


class DomainOsintPlugin(BasePlugin):
    name = "domain_osint"
    description = "Extract domain and email OSINT hints."
    version = "1.0.0"
    produces = ["domains", "emails"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        username = str(context.get("username") or "").strip()
        real_name = str(context.get("real_name") or "").strip()
        candidate_email = username if "@" in username else None
        candidate_website = username if "." in username and "@" not in username else None

        if not candidate_email and not candidate_website and not real_name:
            return {
                "success": True,
                "data": {"skipped": True, "domains": [], "emails": []},
            }

        result = analyze_domain_osint(website=candidate_website, email=candidate_email)
        return {"success": True, "data": result}
