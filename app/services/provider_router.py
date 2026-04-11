import time
from typing import List, Dict, Any

class ProviderResult:
    def __init__(self, source: str, provider: str, platform: str, username: str, profile_url: str, title: str, snippet: str, response_status: str, evidence_signals: list, raw_confidence_hint: float):
        self.source = source
        self.provider = provider
        self.platform = platform
        self.username = username
        self.profile_url = profile_url
        self.title = title
        self.snippet = snippet
        self.response_status = response_status
        self.evidence_signals = evidence_signals
        self.raw_confidence_hint = raw_confidence_hint

    def as_dict(self):
        return self.__dict__

class BaseProvider:
    name = "base"
    platform = "generic"
    timeout = 5  # seconds

    def search(self, variant: str) -> List[ProviderResult]:
        raise NotImplementedError

    def safe_search(self, variant: str) -> List[ProviderResult]:
        start = time.time()
        try:
            results = self.search(variant)
            status = "ok"
        except Exception as e:
            results = []
            status = f"error: {e}"
        elapsed = time.time() - start
        # Logging (hier nur print, später Logging-Service)
        print(f"[Provider:{self.name}] variant='{variant}' status={status} time={elapsed:.2f}s results={len(results)}")
        return results

# Beispiel-Provider für Demo-Zwecke (z.B. GitHub)
class GithubProvider(BaseProvider):
    name = "github"
    platform = "GitHub"
    def search(self, variant: str) -> List[ProviderResult]:
        # Hier würde ein echter API-Call stehen
        # Demo: Simuliere Treffer, wenn variant wie ein GitHub-Username aussieht
        if len(variant) >= 3 and variant.isalnum():
            return [ProviderResult(
                source="web",
                provider=self.name,
                platform=self.platform,
                username=variant,
                profile_url=f"https://github.com/{variant}",
                title=f"GitHub: {variant}",
                snippet=f"Öffentliches GitHub-Profil für {variant}",
                response_status="ok",
                evidence_signals=["profile_exists"],
                raw_confidence_hint=0.8
            )]
        return []

class ProviderRouter:
    def __init__(self, providers: List[BaseProvider]):
        self.providers = providers

    def search_all(self, variant: str) -> List[Dict[str, Any]]:
        results = []
        for provider in self.providers:
            results.extend([r.as_dict() for r in provider.safe_search(variant)])
        return results

# Beispiel für die Nutzung:
# router = ProviderRouter([GithubProvider()])
# hits = router.search_all("shadowseek")
# print(hits)
