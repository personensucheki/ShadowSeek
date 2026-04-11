from __future__ import annotations

from typing import Any


class BasePlugin:
    name: str = "base"
    description: str = "Base plugin"
    version: str = "1.0.0"
    enabled: bool = True
    category: str = "analysis"
    timeout_ms: int = 3000
    requires: list[str] = []
    produces: list[str] = []

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
