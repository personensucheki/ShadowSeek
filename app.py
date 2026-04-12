"""
ShadowSeek backend entrypoint.

Hinweis:
- Die eigentliche App (Routen/Services/DB) liegt als Package unter `app/` und stellt `create_app()` bereit.
- Dieses File dient als schlanker Entrypoint für lokale Runs und WSGI-Server (Gunicorn/Render/etc.).

Wichtige Endpoints:
- `GET /healthz`       Healthcheck
- `POST /api/search`   Username + Plattform-Scan (multipart/form-data, optional `image`)
"""

import os

from app import create_app

app = create_app()


@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "ShadowSeek"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

