# ShadowSeek – Routes/API/Auth Reality Check (Stand: 2026-04-12)

Diese Datei listet die wichtigsten Routen und bewertet:
- Existiert sie wirklich?
- Wird sie vom Frontend genutzt?
- Hat sie Guards/Gating?
- Live-tauglich?

Hinweis: Der Route-Snapshot wurde aus der tatsächlichen Flask `url_map` erzeugt (lokal importiert via `create_app()`).

---

## Tabelle (Kernrouten)

| Route | Method | Blueprint/Endpoint | Schutzstatus | Frontend-Verwendung | Zustand | Live-tauglich | Security-Risiko | Fix-Status |
|---|---|---|---|---|---|---|---|---|
| `/healthz` | GET | `healthz` | public | infra/monitoring | verbunden | ja | niedrig | ok |
| `/` | GET | `search.home` | public | Home UI | verbunden | ja | niedrig | ok |
| `/search` | GET | `search.search` | gated via `any_feature_required(...)` | Search UI | verbunden | ja | mittel (auth/session) | ok |
| `/platforms` | GET | `search.platforms` | gated | Search UI (dynamic tiles) | verbunden | ja | niedrig | ok |
| `/api/search` | POST | `search.api_search` | gated (bei billing_enabled()) | Search UI form submit | verbunden | ja (mit Keys optional) | mittel (abuse) | verbessert (Public/AI flags) |
| `/api/reverse-image/<token>` | GET | `search.reverse_image_asset` | signed token | Search UI reverse links | verbunden | ja | niedrig | ok |
| `/api/websearch` | GET | `websearch.websearch` | public | Landing/Home (engine) | verbunden | bedingt (Key/Fallback) | niedrig | ok |
| `/search/deepsearch` | POST | `analysis.deepsearch` | public | Search UI deepsearch | verbunden | bedingt (module deps) | mittel | offen (Module-Reife) |
| `/search/screenshot` | POST | `analysis.screenshot` | public | Search UI module | verbunden | nein (ohne Playwright) | mittel (SSRF mitigated) | offen |
| `/auth/login` | POST | `auth.login` | public | Login UI/JS | verbunden | ja | **hoch (CSRF exempt)** | offen |
| `/auth/register` | POST | `auth.register` | public | Register UI/JS | verbunden | ja | **hoch (CSRF exempt)** | offen |
| `/auth/logout` | GET/POST | `auth.logout` | session | UI | verbunden | ja | niedrig | ok |
| `/auth/forgot-password` | POST | `auth.forgot_password` | public | UI | **fake/stub** (501) | nein | niedrig | offen (Feature fehlt) |
| `/billing` | GET | `billing.billing_page` | public | UI | verbunden | ja | mittel | ok |
| `/api/stripe/webhook` | POST | `billing.stripe_webhook` | secret-based | Stripe | verbunden | ja | hoch (secret mgmt) | ok |
| `/api/pulse/query` | POST | `query_api.pulse_query` | feature_required | Pulse UI | verbunden | ja | mittel | ok |
| `/api/einnahmen/query` | POST | `query_api.einnahmen_query` | feature_required | Pulse UI | verbunden | ja | mittel | ok |
| `/live` | GET | `live.live_page` | gated? (prüfen) | Live UI | verbunden | bedingt | mittel | offen |
| `/api/live/*` | GET/POST | `live_api*` | uneinheitlich | Live UI | teils unklar | bedingt | mittel/hoch | offen |

---

## Harte Findings

1) **Live API v2 Prefixing war kaputt**
- Vor Fix: `/api/api/live/...`
- Fix: `D:\ShadowSeek\app\helpers\factory.py` registriert `live_api_v2_bp` ohne extra Prefix.

2) **Auth-Routen CSRF-exempt**
- `D:\ShadowSeek\app\routes\auth.py` exempts login/register/forgot-password.
- Für production browser sessions ist das ein Security-Problem → siehe Security Report.

