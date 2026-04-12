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

## 4) Routen- und Blueprint-Überblick (Real)

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

## 5) API-Struktur (Ist)

- Primäre JSON-APIs liegen unter:
  - `/api/...` (klassische APIs)
  - `/search/...` (Analysis APIs, JSON-only)
  - `/auth/...` (Login/Register, akzeptiert JSON oder Form)

Response-Shape:
- Search API liefert stabil:
  - `query`, `username_variations`, `profiles`, `reverse_image_search`, `meta`.

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

## 7) Search-/DeepSearch-Struktur (Ist)

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

## 8) Pulse-/Revenue-Struktur (Ist)

- Revenue Data: `EinnahmeInfo` Modelle/Endpoints vorhanden (`/api/einnahmen/*`, `/api/einnahmen/query`).
- `query_api.py` implementiert Filter/Pagination/Validation (solider Kern), aber:
  - uneinheitliche Feldnamen (z.B. `kategorie` mapped auf legacy `typ`).
  - Fehlerhandling/DB-Ausfall wird teils still “[]” (kann Monitoring erschweren).

---

## 9) Upload-/Media-Struktur (Ist)

- Reverse-Image Upload: in Search-Service gespeichert unter `UPLOAD_DIRECTORY` (default `instance/uploads` lokal, Render empfohlen `/data/uploads`).
- Tokenisierte Asset-Route: `/api/reverse-image/<token>` nutzt `itsdangerous` Signaturen + max_age.
- Pfad-Sicherheit: `secure_filename`, resolve-check (`upload_directory in image_path.parents`) vorhanden.

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

## 12) Responsive-/UI-Status

- CSS stark cyberpunk-orientiert, responsive Anpassungen sind vorhanden (z.B. `search.css` Media Queries).
- Keine visuellen Änderungen durch dieses Audit außer funktionalen Hidden Fields (keine UI-Zerstörung).

---

## 13) Deploy-/Runtime-/Env-Status (Ist)

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

