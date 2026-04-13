from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LOGGER = logging.getLogger("provider_utils")


@dataclass
class ProviderResult:
    success: bool
    data: dict
    error: str | None = None
    status_code: int | None = None
    transient: bool = False


class ExternalProviderClient:
    """
    Shared HTTP client for public provider integrations.
    Enforces timeout, retry, request headers and basic error mapping.
    """

    def __init__(
        self,
        *,
        provider_name: str,
        timeout_seconds: float = 6.0,
        retries: int = 2,
        backoff_factor: float = 0.35,
        rate_limit_seconds: float = 0.0,
        user_agent: str = "ShadowSeek-OSINT/1.0 (+public-signal-only)",
    ):
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.rate_limit_seconds = max(0.0, float(rate_limit_seconds))
        self.user_agent = user_agent
        self._last_request_at = 0.0

        self.session = requests.Session()
        retry_policy = Retry(
            total=max(0, int(retries)),
            connect=max(0, int(retries)),
            read=max(0, int(retries)),
            status=max(0, int(retries)),
            backoff_factor=max(0.0, float(backoff_factor)),
            status_forcelist=(408, 429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "HEAD"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _respect_rate_limit(self):
        if self.rate_limit_seconds <= 0:
            return
        now = time.time()
        delta = now - self._last_request_at
        if delta < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - delta)

    def _headers(self, extra_headers: dict | None = None):
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        }
        if isinstance(extra_headers, dict):
            headers.update(extra_headers)
        return headers

    def get(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> ProviderResult:
        self._respect_rate_limit()
        try:
            response = self.session.get(
                url,
                params=params or None,
                headers=self._headers(headers),
                timeout=self.timeout_seconds,
            )
            self._last_request_at = time.time()
            return map_http_response(self.provider_name, response)
        except requests.Timeout:
            return ProviderResult(False, {}, error="timeout", transient=True)
        except requests.RequestException as error:
            LOGGER.warning("[%s] request error: %s", self.provider_name, error)
            return ProviderResult(False, {}, error="network_error", transient=True)


def map_http_response(provider_name: str, response: requests.Response) -> ProviderResult:
    status = int(response.status_code)

    if 200 <= status < 300:
        content_type = (response.headers.get("Content-Type") or "").lower()
        data = {}
        if "application/json" in content_type:
            try:
                data = response.json()
            except ValueError:
                data = {"raw_text": response.text}
        else:
            data = {"raw_text": response.text}
        return ProviderResult(True, data, status_code=status)

    if status in (408, 429, 500, 502, 503, 504):
        LOGGER.warning("[%s] transient status %s", provider_name, status)
        return ProviderResult(False, {}, error=f"http_{status}", status_code=status, transient=True)

    LOGGER.info("[%s] non-success status %s", provider_name, status)
    return ProviderResult(False, {}, error=f"http_{status}", status_code=status, transient=False)
