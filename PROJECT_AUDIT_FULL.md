# ShadowSeek – Full Project Audit (Stand: 2026-04-12)

Diese Audit-Datei beschreibt den **tatsächlichen** Zustand des Repos `D:\ShadowSeek` (kein Marketing).
Fokus: Entry-Points, Bootpfad, Routen/Blueprints, echte Backend-Logik, Frontend↔Backend-Verbindungen, Security und Live-Readiness.

---

## 1) Gesamtarchitektur (Ist-Zustand)

- **Framework**: Flask + Jinja Templates + Vanilla JS (kein SPA).
- **App Factory**: `D:\ShadowSeek\app\__init__.py` (`create_app()`).
- **DB**: SQLAlchemy + Flask-Migrate, Default SQLite lokal (`sqlite:///shadowseek.db`), Production via `DATABASE_URL` (Render).
- **Billing/Gating**: Stripe integriert, Feature-Gating serverseitig vorhanden (Plan→Features).
- **Realtime**: Flask-SocketIO vorhanden; weitere Live-Teile existieren (Streams/Chat/Gifts), aber Reifegrad gemischt.
- **OSINT/Search**: Kernpfad `/api/search` existiert. Vor Audit war “DeepSearch/AI” teilweise **Stub/Dummy**; wurde in diesem Audit für Public-Search und AI-Rerank minimal realisiert (ToS-/Privacy-konform; keine Plattform-Scraper).

---

## 2) Tatsächliche Projektstruktur (High-Level)

- `D:\ShadowSeek\app\__init__.py`: App Factory, DB-URI Normalisierung, Blueprint-Registrierung, Health.
- `D:\ShadowSeek\app\helpers\factory.py`: Blueprint-Registration + Hooks + Error-Handling + CORS.
- `D:\ShadowSeek\app\routes\*`: Pages + APIs (Search, Pulse, Billing, Community, Live, etc.).
- `D:\ShadowSeek\app\services\*`: Business-Logik (Search, Billing, Deepsearch, Risk Score, etc.).
- `D:\ShadowSeek\app\static\css|js|images`: Frontend Assets.
- `D:\ShadowSeek\app\templates\*`: Jinja Templates.
- `D:\ShadowSeek\migrations\`: Alembic Migrations.
- `D:\ShadowSeek\instance\`: Uploads/Instance-Data (lokal).
- `D:\ShadowSeek\reports\`: vorhandene Reports/Artefakte.
- **Auffälligkeit**: `D:\ShadowSeek\models.py` existiert parallel zu `D:\ShadowSeek\app\models\...` → wirkt wie Legacy/Altbestand (siehe “Fake/Dummy”).

---

## 3) Entry-Points und Bootpfad

- **WSGI**: `D:\ShadowSeek\run.py` importiert `create_app()` (normaler Einstieg).
- **Alternative**: `D:\ShadowSeek\app.py` importiert `create_app()` und addiert CORS (aber CORS passiert bereits in `factory.py` → Duplikat-Risiko).
- `create_app()`:
  - lädt Config aus `app\config.py` (Development/Production/Testing),
  - normalisiert `DATABASE_URL` (inkl. `postgres://`→`postgresql+psycopg://`),
  - initialisiert `db`, `migrate`, `csrf`, `socketio`,
  - registriert Blueprints über `app\helpers\factory.py`,
  - optional Owner-Bootstrap via `app\services\owner_bootstrap.py` (env-gesteuert),
  - Health: `GET /healthz` (JSON).

---




### PHASE 5.5: Auth CSRF Hardening & Verification (April 2026)

+- **CSRF Model:** All browser-submitted auth routes (`/auth/login`, `/auth/register`, `/auth/forgot-password`, `/auth/logout`) now enforce CSRF protection. No `@csrf.exempt` remains on these routes. All browser forms render CSRF tokens and require them for POSTs. API-style POSTs without CSRF are rejected. If API endpoints are needed in the future, they must be split and documented.
+- **Affected Routes:** `/auth/login`, `/auth/register`, `/auth/forgot-password`, `/auth/logout`
+- **Exact Changes:** Removed `@csrf.exempt` from all browser auth routes. No ambiguity remains; all POSTs require CSRF tokens. Forms unchanged (tokens already present).
+- **Runtime Verification:**
+    - POST without CSRF: 302 redirect, no explicit CSRF error (safe, but not explicit)
+    - POST with CSRF: 302 redirect, normal validation path
+    - No raw exceptions, no UX regression
+    - CSRF failures are safe but not clearly surfaced to the user
+- **Classification:** READY WITH WARNINGS (CSRF enforced, but failure feedback is not explicit)


- **Global Envelope:** Alle Search-Endpunkte liefern jetzt strikt:
  `{ "success": boolean, "data": object|null, "error": string|null }`
  - `/api/search` (POST)
  - `/api/suggest` (GET)
  - `/api/reverse-image/<token>` (GET, Fehlerfälle)
- **Frontend:** `search.js`, `landing.js` entpacken und verarbeiten das Envelope, inkl. Fehler/Leere.
- **Runtime-Tests:**
  - Normale Suche, DeepSearch, leere/Low-Signal-Suche, Validation Error, Timeout/Partial Failure
  - Suggest: normal, leer, malformed
  - Reverse-Image: invalid/missing token
  - Alle Responses: immer Envelope, keine Legacy-Root-Payloads, keine rohen Exceptions
- **Files changed:**
  - `app/routes/search.py`, `app/routes/suggest.py`, `app/services/response_utils.py`
  - `app/static/js/search.js`, `app/static/js/landing.js`
- **Frontend:** Keine Mapping- oder Render-Fehler, alle States (leer, Fehler, partial) werden sicher verarbeitet.
- **Warnings:** Rate-Limiting, Security/Performance-Review, Legacy-Modelle, Upload/Media-Checks offen
- **Status:** READY WITH WARNINGS

**Siehe Code: `app/services/search_service.py`, `app/routes/search.py`, `app/routes/suggest.py`, `app/static/js/search.js`, `app/static/js/landing.js` (Stand: April 2026)**

Blueprint-Registrierung: `D:\ShadowSeek\app\helpers\factory.py`.

Wichtigste Flows:
- **Home/Search UI**: `GET /` (`search.home`), `GET /search` (`search.search`), `GET /platforms` (`search.platforms`).
- **Search API**: `POST /api/search` (`search.api_search`) – nimmt FormData + optional Image.
- **Reverse-Image Asset**: `GET /api/reverse-image/<token>` – serve für Lens/TinEye/Yandex Links.
- **Analysis APIs**: `POST /search/deepsearch`, `/search/screenshot`, `/search/similarity`, `/search/image-similarity`, `/search/risk-score`.
- **Websearch API**: `GET /api/websearch` – Serper (falls Key) oder Bing-RSS fallback.
- **Auth**: `POST /auth/login`, `POST /auth/register`, `GET/POST /auth/logout`, `POST /auth/forgot-password` (aktuell “nicht aktiviert”).
- **Billing**: `/billing`, `/api/billing/*`, `/api/stripe/webhook`.
- **Pulse/Revenue**: `/pulse`, `/api/pulse/*`, `/api/einnahmen/*`.
- **Community**: `/members`, `/messages`, etc.
- **Live**: `/live`, diverse `/api/live/*` und “v2” APIs.

### Harte Befundstelle (Bug Fix im Audit)
- Vor Fix war `live_api_v2` **doppelt** unter `/api/api/live/...` registriert (Blueprint hatte `/api/live/...` Routen, wurde aber zusätzlich mit `url_prefix="/api"` registriert).
- Fix: `D:\ShadowSeek\app\helpers\factory.py` registriert `live_api_v2_bp` jetzt ohne extra Prefix.

---


## 5) API-Struktur (Status: PARTIALLY VERIFIED)

- **Status:** PARTIALLY VERIFIED
- **Reason:** Mixed `success/data/error` patterns still exist; standardization not complete.
- **Evidence:** Some endpoints return envelope, others raw lists or dicts; see code and test results.
- **Risks:** Inconsistent client handling, harder error tracking, possible integration bugs.

---

## 6) Auth-/Session-/Security-Struktur (Ist)

- Sessions: Flask Cookie Session (`session["user_id"]`, `role`, etc.).
- Passwort-Hashing: Werkzeug (`generate_password_hash`, `check_password_hash`).
- CSRF: Flask-WTF installiert und global in Factory init.
- **Problem**: `D:\ShadowSeek\app\routes\auth.py` setzt `@csrf.exempt` auf **login/register/forgot-password**.
  - Das ist für JSON-Clients nachvollziehbar, aber für Browser-Sessions riskant (CSRF).
  - Siehe `SECURITY_AND_FAKE_CLEANUP_REPORT.md`.
- CORS:
  - In `factory.py` werden für `/api/*` permissive Header gesetzt (`API_CORS_ALLOWED_ORIGINS` default `"*"`).
  - Zusätzlich existiert CORS-Logik in `D:\ShadowSeek\app.py` → Duplikat/Inkonsistenz-Risiko.

---


## 7) Search-/DeepSearch-Struktur (Status: READY WITH WARNINGS)

- **Status:** READY WITH WARNINGS
- **Reason:** Providers not fully implemented; AI reranking not fully production-ready; performance and security still open.
- **Evidence:** Minimal implementation for Serper/Bing/OpenAI; some functions are stubs or best-effort; see FINAL_LAUNCH_STATUS.md.
- **Risks:** Incomplete results, possible ToS/privacy issues, unpredictable latency, security surface.

### Search (Kernpfad)
- Frontend: `D:\ShadowSeek\app\templates\search.html` + `D:\ShadowSeek\app\static\js\search.js`.
- Backend: `D:\ShadowSeek\app\routes\search.py` → `execute_search()` in `app\services\search_service.py`.
- Inputs: username + optionale Felder + Plattform-Auswahl + optional Image + DeepSearch Toggle.

### Echte vs. unechte Teile (Stand vor Audit)
- `app\services\search_service.py` enthielt mehrere **Stub-Funktionen**:
  - `collect_serper_profiles`, `collect_bing_profiles`, `discover_profiles`, `scan_platform`, `should_ai_rerank`, `rerank_profiles_with_openai` → waren leer / always-false.
- Effekt: UI suggerierte DeepSearch/AI/“Plattformen werden geprüft”, aber Backend lieferte nur “lokale Kandidatenlinks”.

### Fixes in diesem Audit (minimal & ToS-/Privacy-konform)
- `app\services\search_service.py`:
  - optionaler **Public-Search** via Serper (falls API-Key) oder Bing RSS fallback,
  - optionales **AI-Reranking** via OpenAI (falls `OPENAI_API_KEY`),
  - neue Flags aus dem Frontend: `public_sources`, `ai_rerank`, `secure_mode`, `precision_mode`.
- `app\static\js\search.js`:
  - sendet Modifier als Hidden Fields an `/api/search`.

Wichtig: Keine Scraper/Headless-“Account Existence” Checks auf Plattform-Endpoints (ToS/Privacy).

---


## 8) Pulse-/Revenue-Struktur (Status: READY WITH WARNINGS)

- **Status:** READY WITH WARNINGS
- **Reason:** Legacy fields still present; config completeness not guaranteed.
- **Evidence:** Endpoints exist but 404 for /api/pulse, /api/revenue; legacy field mapping; see FINAL_LAUNCH_STATUS.md.
- **Risks:** Data drift, missing features, possible integration errors.

- Revenue Data: `EinnahmeInfo` Modelle/Endpoints vorhanden (`/api/einnahmen/*`, `/api/einnahmen/query`).
- `query_api.py` implementiert Filter/Pagination/Validation (solider Kern), aber:
  - uneinheitliche Feldnamen (z.B. `kategorie` mapped auf legacy `typ`).
  - Fehlerhandling/DB-Ausfall wird teils still “[]” (kann Monitoring erschweren).

---


## 9) Upload-/Media-Struktur (Status: READY WITH WARNINGS)

- **Status:** READY WITH WARNINGS
- **Reason:** Upload validation not fully hardened; persistence depends on `/data/uploads`; deployment risk documented.
- **Evidence:** Uploads work locally with default, but `UPLOAD_DIRECTORY` unset/empty in prod; see FINAL_LAUNCH_STATUS.md.
- **Risks:** Data loss if directory missing; incomplete validation could allow unsafe files; see LIVE_READINESS_REPORT.md.
- **Tokenisierte Asset-Route:** `/api/reverse-image/<token>` nutzt `itsdangerous` Signaturen + max_age.
- **Pfad-Sicherheit:** `secure_filename`, resolve-check (`upload_directory in image_path.parents`) vorhanden.

---

## 10) Feed-/Live-/Profil-/Mitglieder-Struktur (Ist)

- Members: `/members`, `/members/<username>`.
- Profile: `/profile` + `/profile/update` + `/uploads/<filename>` (Upload handling prüfen).
- Live: mehrere APIs + SocketIO; Reifegrad heterogen, teils ohne Guards.

---

## 11) Frontend-/JS-/Template-Verknüpfung (Ist)

- Search-Form `action="/api/search"` passt zu Backend.
- DeepSearch-Analysis: `search.js` ruft `/search/deepsearch` auf (JSON), Backend existiert.
- UI-Module (“screenshots”, “risk score”, “image similarity”) haben Endpoints, aber:
  - Screenshot-Funktion benötigt Playwright (nicht in `requirements.txt`) → in Produktion aktuell **nicht lauffähig** ohne Zusatzsetup.
  - Andere Module (Risk/Similarity) sind lokal implementiert und lauffähig, aber teils “heuristisch”.

---


## 12) Responsive-/UI-Status (Status: PARTIALLY VERIFIED)

- **Status:** PARTIALLY VERIFIED
- **Reason:** Only core pages confirmed; no full viewport validation proof.
- **Evidence:** Media queries present, but not all pages tested on all devices.
- **Risks:** Possible layout issues on edge devices, incomplete mobile UX.

---


## 13) Integrations (Stripe, OpenAI, etc.) (Status: PARTIALLY VERIFIED)

- **Status:** PARTIALLY VERIFIED (unless ENV keys present and tested)
- **Reason:** Not all ENV keys validated in prod; some integrations untested.
- **Evidence:** Stripe/OpenAI/Serper code paths present, but require ENV and live test.
- **Risks:** Integration failures, missing features, runtime errors.

- `.env.example` vorhanden.
- Render Config existiert (`render.yaml`), Gunicorn ist in requirements.
- Risiken:
  - Default Dev Secret (`shadowseek-dev-secret`) in DevelopmentConfig (ok lokal, nicht in Prod).
  - Doppelte CORS Logik (app.py + factory.py).
  - Playwright fehlt (Screenshot-Modul).

---

## 14) Datenbank-/Modellstatus (Ist)

- “Real” Modelle liegen unter `D:\ShadowSeek\app\models\...` (z.B. `user.py`).
- `D:\ShadowSeek\models.py` enthält ein **zweites** `User` Modell mit hardcodierten Defaults und Encoding-Artefakten → wirkt wie Legacy/Dummy, nicht konsistent mit `app\models\user.py`.

---

## 15) Offene Risiken (Kurz)

- CSRF-Exempt auf Auth-Routen.
- CORS `"*"` für `/api/*` im Default (kann Credential-Leaks vermeiden, aber trotzdem streng prüfen).
- Screenshot Engine abhängig von Playwright (nicht installiert).
- Live APIs: teils ohne Auth/Rate-Limits (mögliche Abuse-Fläche).
- Mehrere “Demo”-Signale in UI (“DeepSearch scannt Plattformen...”) ohne garantiert echte Prüflogik (besser ehrlich labeln).

---

## 16) Offene technische Schulden

- Legacy-Dateien (`models.py`) und doppelte Patterns.
- Uneinheitliche API-Envelopes (`{success:...}` vs. rohe Listen).
- Fehlende systemweite Rate-Limits/Abuse-Protection.

---

## 17) Live-Readiness-Einschätzung (Aktuell)

Status: **Ready with warnings**

Blocker:
- Screenshot-Modul (Playwright) nicht deploy-ready ohne zusätzliche Schritte.
- CSRF/Session-Härtung auf Auth.

Warnings:
- Public Search abhängig von Serper Key (Fallback “Bing RSS” ist best-effort).
- Mehrere Features wirken “größer” als die reale Backend-Wirkung (muss im UI klarer werden).

