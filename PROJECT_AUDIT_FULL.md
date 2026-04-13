# PROJECT_AUDIT_FULL.md
Stand: 2026-04-13
Projekt: ShadowSeek

## Gesamturteil
`live-ready-with-warnings`

## Prioritaet 1 - Produktionshaerte
### Was existiert real
- Deploy-Doku vorhanden: `DEPLOY_SHADOWSEEK.md` mit Render Build/Start/Health und ENV-Liste.
- App-Factory + WSGI vorhanden (`run.py`, `app.py`, `app/__init__.py`).
- Health-Endpunkte vorhanden: `/health` und `/healthz`.
- Migrationen lauffaehig (`flask db upgrade` lokal erfolgreich auf SQLite).
- Upload-Verzeichnisse werden beim Start erzeugt.

### Was funktioniert
- `flask db upgrade` lief erfolgreich.
- `/health` und `/healthz` liefern 200.
- ENV-Validation in `create_app()` blockiert bei fehlenden Pflicht-ENV in Render-Runtime.

### Was teilweise funktioniert
- `gunicorn run:app` ist fuer Linux korrekt, aber lokaler Check auf Windows scheitert erwartbar an `fcntl` (kein Linux-Runtime-Test lokal moeglich).
- Persistent-Storage ist vorbereitet, aber lokal auf `instance/uploads` konfiguriert statt `/data/uploads`.

### Was fehlt / riskant
- `.env` hat doppelte Keys (u. a. `PUBLIC_BASE_URL`, `APP_BASE_URL`, `UPLOAD_DIRECTORY`, `BILLING_GATING_ENABLED`).
- Lokale `.env` nutzt `UPLOAD_DIRECTORY=instance/uploads`; fuer Render muss `/data/uploads` gesetzt bleiben.
- `required_env`-Liste in `create_app()` prueft nicht explizit `PUBLIC_BASE_URL`/`APP_BASE_URL`/`UPLOAD_DIRECTORY`.

### Sofort behoben
- Keine Breaking-Aenderung an Deploy-Flow; Audit-Validierung live ausgefuehrt und dokumentiert.

### Blocker
- Kein harter Blocker fuer Deploy-Architektur.
- Operativer Blocker bleibt: Produktions-ENV muss in Render konsistent gesetzt/validiert werden.

## Prioritaet 2 - Search / DeepSearch
### Was existiert real
- Search-Endpoint: `POST /api/search`.
- Payload-Builder, Username-Variationen, Ranking, Dedup, Reverse-Image-Links (Google Lens/TinEye/Yandex).
- DeepSearch-/Public-Source-/AI-Rerank-Pfade vorhanden.
- Provider-Fanout vorhanden inkl. TikTok-Provider.

### Was funktioniert
- Score/Confidence/Match-Reasons/Meta werden durchgereicht.
- Dedup + Plattform-Limits greifen.
- Reverse-Image-Link-Generierung funktioniert.

### Was teilweise funktioniert
- TikTok liefert je nach Schutzseite Challenge/Shell statt Profil-Daten.
- AI-Reranking ist optional und fallback-faehig.

### Was fehlt / riskant
- Contract-Streuung in Meta-Feldern war vorhanden (`ai_reranked` vs erwartetes `ai_reranking_applied`).
- Public-Source-Default war zu restriktiv fuer erwartetes Verhalten.

### Sofort behoben
- TikTok-Scraper-Integration stabilisiert:
  - relative Imports in `runner.py` korrigiert
  - Profil-URLs zusaetzlich zu Video-URLs unterstuetzt
  - Fetcher-Crash (`context.user_agent`) behoben
- Search-Meta stabilisiert:
  - Alias `meta.ai_reranking_applied` hinzugefuegt
  - `public_sources` standardmaessig aktiviert
  - AI-Rerank in DeepSearch ohne expliziten Flag aktiviert
  - interne Rerank-Route auf `rerank_profiles_with_openai()` vereinheitlicht

### Blocker
- Kein harter Blocker, aber TikTok ist extern challenge-anfaellig (plattformbedingt).

## Prioritaet 3 - Pulse / Revenue
### Was existiert real
- Revenue-/Pulse-Routen: `/api/einnahmen/*`, `/api/pulse/query`, `/api/pulse/live/*`, Analytics-Endpunkte.
- Revenue-Schema (`EinnahmeInfo`) + Collector + Dedupe vorhanden.

### Was funktioniert
- Query, Filter, Pagination und Serialisierung funktionieren.
- Fallback bei DB-Fehlern in Summary nun robust.

### Was teilweise funktioniert
- Legacy-Felder in `EinnahmeInfo` (alt + neu parallel) sind noch vorhanden.
- API-Responses waren gemischt (teils `api_success(data=...)`, teils flache Payload).

### Was fehlt / riskant
- Demo-Provider default `true` in `revenue_provider_registry.py` ist produktionsriskant.

### Sofort behoben
- API-Contract-Fixes:
  - `query_api.py` liefert fuer Pulse-Mode wieder top-level Felder (`mode`, `rows`, ...) + `success`
  - `live_api.py` dito fuer `/api/pulse/live/<platform>`
  - `dashboard.py` Summary liefert kompatibel sowohl top-level Felder als auch `data`-Envelope
  - Fallback-Status bei Summary-Exceptions auf `collector_status=unavailable`

### Blocker
- Demo-Provider Default-Einstellung bleibt als operatives Risiko offen.

## Prioritaet 4 - Upload / Media
### Was existiert real
- Gemeinsame Upload-Validierung (`services/media.py`) fuer Typ, MIME, Groesse.
- Profil- und Feed-Uploads nutzen persistente Basis `UPLOAD_DIRECTORY`.

### Was funktioniert
- Uploads werden unter `UPLOAD_DIRECTORY` abgelegt.
- Legacy-Static-Pfade werden lesend unterstuetzt.

### Was teilweise funktioniert
- Persistenz ist nur so robust wie ENV-Mount (`/data/uploads` in Produktion).

### Was fehlt / riskant
- Lokale `.env` aktuell nicht auf Render-Persistent-Pfad.

### Sofort behoben
- Keine code-seitige Breaking-Aenderung; Fokus auf Audit + klare Deploy-Hinweise.

### Blocker
- Produktionsmount und ENV-Abgleich bleibt Pflicht vor Livegang.

## Prioritaet 5 - Feed / Profile / Live
### Was existiert real
- Feed API + Interaktions-API (Kommentare/Likes/Views).
- Profilseite + Profil-Update + Upload-Routen.
- Live API v1/v2 mit Stream/Like/Chat/Gift/Leaderboard.
- Modelle fuer Posts/Interactions/Live-Events vorhanden.

### Was funktioniert
- Grundfunktionen sind implementiert und erreichbar.

### Was teilweise funktioniert
- Live/Feed nutzen unterschiedliche Response-Stile (historisch gemischt).
- Demo-Feed kann in Dev aktiv sein.

### Was fehlt / riskant
- Kein vollstaendig einheitlicher Contract ueber alle historischen Live-/Pulse-Endpunkte.

### Sofort behoben
- Pulse-Live-Contract wieder auf erwartete Form gebracht (kompatibel mit Tests/Frontend).

### Blocker
- Kein harter Blocker, aber weitere API-Normalisierung empfohlen.

## Prioritaet 6 - API-Konsistenz
### Was existiert real
- `api_success`/`api_error` Utilities vorhanden.

### Was funktioniert
- Einheitliche Error-Shape meist vorhanden (`success`, `error`, optional `errors`).

### Was teilweise funktioniert
- Einige Endpunkte erwarten historisch top-level Felder ohne `data`-Kapselung.

### Was fehlt / riskant
- Vollstaendig konsistentes Envelope-Muster ist noch nicht ueberall durchgezogen.

### Sofort behoben
- Kritische Contract-Breaks fuer Search/Pulse/Live/Dashboard beseitigt.

## Test- und Laufnachweise
- `flask db upgrade`: erfolgreich.
- Healthcheck per Test-Client: `/health` 200, `/healthz` 200.
- Relevante Regression-Suite: `30 passed`:
  - `tests/test_search_core.py`
  - `tests/test_search_api.py`
  - `tests/test_deepsearch_plugins.py`
  - `tests/test_einnahmen_summary.py`
  - `tests/test_api_smoke.py`
