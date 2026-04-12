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

