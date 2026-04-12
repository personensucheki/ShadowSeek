"""ShadowSeek Flask entrypoint.

The application uses the factory in ``app.create_app()``. This module keeps the
top-level WSGI entrypoint importable for local runs, Gunicorn, and ad-hoc
development commands without duplicating route registration.
"""

from __future__ import annotations

import os

from flask import Flask, request

from app import create_app


def add_api_cors(app: Flask) -> None:
    """
    Minimal-CORS fuer API-Calls vom Frontend.

    Falls dein Frontend und Backend auf unterschiedlichen Origins laufen (z.B. Vercel + Render),
    muss der Browser Cross-Origin Requests erlauben.

    Konfiguration:
    - `CORS_ALLOW_ORIGIN` (Default: "*") -> z.B. "https://shadowseek.example"
    """

    allow_origin = os.environ.get("CORS_ALLOW_ORIGIN", "*")

    @app.after_request
    def _cors_after_request(response):
        if request.path.startswith("/api/"):
            response.headers.setdefault("Access-Control-Allow-Origin", allow_origin)
            response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            response.headers.setdefault(
                "Access-Control-Allow-Headers", "Content-Type, X-CSRFToken, Authorization"
            )
        return response

    @app.route("/api/<path:_subpath>", methods=["OPTIONS"])
    def _cors_preflight(_subpath: str):
        # Leere Response fuer Preflight; Header werden im after_request gesetzt.
        return ("", 204)


app = create_app()
add_api_cors(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
