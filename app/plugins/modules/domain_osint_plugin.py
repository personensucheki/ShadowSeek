from app.plugins.base import BasePlugin
from app.services.domain_osint import analyze_domain_osint


class DomainOsintPlugin(BasePlugin):
    name = "domain_osint"
    description = "Extract domain and email OSINT hints."

    def run(self, data: dict) -> dict:
        website = data.get("website")
        email = data.get("email")
        if not website and not email:
            return {"success": True, "skipped": True, "domains": [], "emails": []}

        result = analyze_domain_osint(website=website, email=email)
        return {"success": True, **result}
