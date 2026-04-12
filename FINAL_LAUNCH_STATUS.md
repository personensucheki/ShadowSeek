# ShadowSeek – Final Launch Status (Stand: 2026-04-12)

## Zusammenfassung (ohne Beschönigung)

ShadowSeek ist **nicht** “fertig live” im Sinne eines sauberen, harten Produktionsbetriebs, aber der Kernflow (Search UI → `/api/search` → JSON → UI Rendering) ist real verbunden.

Status: **Ready with warnings**

---

## Was funktioniert echt?

- Flask App Factory, Blueprints, Templates, Static Assets
- Search-Form → `/api/search` inkl. optionalem Image Upload
- Reverse-Image Links (Lens/TinEye/Yandex) über tokenisiertes Asset
- Billing-Gating-Mechanik serverseitig (bei aktivem Stripe Setup)
- Permission Snapshot / Feature Guards

---

## Was war fake/unecht oder nur halb gebaut?

- Search Provider/AI Reranking war im Backend **Stub** (leere Funktionen) – wurde jetzt minimal realisiert.
- Screenshot-Modul wirkt vorhanden, ist ohne Playwright/Browsers nicht deploy-ready.
- Forgot-Password ist stub (501).
- Doppelte/Legacy Model Dateien (`models.py`) → wirkt wie Alt/Dummy.

---

## Was wurde repariert/ergänzt?

- Search: optionale Public-Search (Serper/Bing RSS) + optionales AI-Rerank (OpenAI) im Backend.
- Frontend: Modifier werden als Hidden Fields an `/api/search` gesendet.
- Routing: `live_api_v2` doppelt geprefixt (`/api/api/...`) gefixt.

---

## Was bleibt offen / blockiert “sauber live”?

Blocker/High-Risks:
- CSRF/Session-Security auf Auth (P0)
- Rate-Limiting/Abuse-Protection (P1)
- Screenshot Deploy (Playwright) oder ehrliches Deaktivieren (P1/P2)
- Legacy Cleanup (P2)

---

## April 2026 – Produktionsabnahme

### Getestete Bereiche
- Feed-API, Demo-Branch, UserPosts: erfolgreich, konsistente Daten, Mapping passt zum Frontend
- Provider-Status-API: 500 INTERNAL SERVER ERROR (kritischer Blocker)
- Pulse-/Revenue-API: 404 NOT FOUND (noch nicht implementiert)
- Upload-API: 405 METHOD NOT ALLOWED (nur POST erlaubt, korrekt)
- Health-Check: ok
- Migrationen: auf head
- gunicorn: Windows-Start nicht möglich (fcntl fehlt, Linux-only)
- ENV: DATABASE_URL korrekt, UPLOAD_DIRECTORY nicht gesetzt/leer

### Erfolgreiche Endpunkte
- /api/feed
- /api/feed?limit=1
- /api/feed?demo=1
- /api/u/ADMIN/posts
- /health

### Restprobleme
- Provider-Status-API liefert 500 (kritisch)
- Pulse-/Revenue-API nicht implementiert
- UPLOAD_DIRECTORY nicht gesetzt/leer
- gunicorn auf Windows nicht lauffähig (nur Linux)

### Fazit
- feed-ready: ja
- api-ready: nein (Provider-Status-API blockiert)
- launch-ready: nein (Blocker vorhanden)

