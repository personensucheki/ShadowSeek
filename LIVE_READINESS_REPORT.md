# ShadowSeek – Live Readiness Report (Stand: 2026-04-12)

Bewertung: **Ready with warnings**

---

## Ready (funktioniert real)

- App Factory Boot (`D:\ShadowSeek\app\__init__.py`) startet lokal mit Default Dev Config.
- Healthchecks: `GET /healthz` (JSON), `GET /health` (route existiert).
- Search UI + `/api/search` Flow ist verbunden.
- Reverse-Image Upload Token + Asset Link Flow ist real.
- Billing/Stripe: Codepfad vorhanden (abhängig von Secrets/Stripe setup).
- Feature-Gating ist serverseitig implementiert und wird auf zentralen Flows genutzt.

---

## Warnings (Live-fähig, aber mit Risiken)

### W1: Auth CSRF exempt
- Login/Register ohne CSRF. Für production browser sessions kritisch.

### W2: Public Search Provider abhängig
- Serper Key nötig für konsistente Web-Suche.
- Bing RSS fallback ist best-effort und kann limitiert/unzuverlässig sein.

### W3: Rate Limiting fehlt
- DoS/Spam/Bruteforce möglich.

### W4: Legacy Files / Modell-Duplikate
- `D:\ShadowSeek\models.py` kann zu Import-Verwechslungen führen.

---

## Blocked (nicht live-ready ohne Zusatzarbeit)

### B1: Screenshot Engine
- Endpoint vorhanden, aber Playwright fehlt (Dependency + Browser install).
- Ohne Deploy-Schritte ist dieses Modul tot.

---

## Sofort empfohlene nächste Schritte (minimal-invasiv)

1) CSRF/Origin Policy für Auth entscheiden und implementieren.
2) Rate-Limits für `/auth/login`, `/auth/register`, `/api/search`, Live APIs.
3) Screenshot-Modul entweder:
   - sauber deploy-ready machen (Playwright + install), oder
   - im UI/Backend ehrlich deaktivieren.
4) `D:\ShadowSeek\models.py` entfernen/archivieren.
5) Production CORS streng konfigurieren (`API_CORS_ALLOWED_ORIGINS`).

## April 2026 – Finaler Produktionscheck

### Feed-API, Demo-Branch, Health-Check
- Erfolgreich stabilisiert, Schema-/Migrationsdrift bei media_posts behoben.
- Endpunkte liefern korrekte, konsistente Daten.

### Provider-Status-API
- /api/providers/status: Liefert aktuell 500 INTERNAL SERVER ERROR (kritischer Blocker, muss vor Launch behoben werden).

### Pulse-/Revenue-API
- /api/pulse, /api/revenue: 404 NOT FOUND (nicht implementiert oder Routing-Fehler, kein Blocker für Feed-Launch, aber für Pulse/Revenue-Features).

### Upload-API
- /api/upload: 405 METHOD NOT ALLOWED (POST-Only, GET nicht erlaubt, kein Fehler im Sinne der API-Spezifikation).

### Health-Check
- /health: {"status": "ok"}

### Deploy/Start
- flask db current: Migration auf head (20260412_9998)
- gunicorn: Start auf Windows nicht möglich (fcntl fehlt, Linux-only, kein echter Blocker für Codequalität)
- DATABASE_URL: korrekt gesetzt
- UPLOAD_DIRECTORY: nicht gesetzt/leer (prüfen, ob Default greift)

### Zusammenfassung
- Feed-API: ready
- API: nicht vollständig ready (Provider-Status-API kritisch)
- Launch: nicht ready, solange Provider-Status-API 500 liefert

