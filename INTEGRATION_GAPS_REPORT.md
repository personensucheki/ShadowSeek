# ShadowSeek Integration Gaps Report

Stand: 2026-04-12

## Geprueft

- `create_app()` Boot und reale `url_map`
- Kernseiten per `test_client()`
- zentrale JSON-Endpunkte per `test_client()`
- Frontend-Fetches in `app/static/js/*.js`
- Route-/Blueprint-Registrierung in `app/helpers/factory.py`

## Kritisch

- Keine aktuell.

## Hoch

- Keine aktuell.

## Mittel

- Zwei Health-Endpunkte parallel vorhanden
  - `/health` aus `app/routes/health.py`
  - `/healthz` direkt in `app/__init__.py`
  - Funktioniert aktuell, aber Infrastrukturvertrag sollte auf einen kanonischen Endpunkt vereinheitlicht werden

- Zwei Health-Endpunkte parallel vorhanden
  - `/health` aus `app/routes/health.py`
  - `/healthz` direkt in `app/__init__.py`
  - Funktioniert aktuell, aber Infrastrukturvertrag sollte auf einen kanonischen Endpunkt vereinheitlicht werden

- `DeepSearch`-Endpoint ist jetzt dekoriert, haengt aber weiterhin vom globalen Billing-Modus ab
  - Datei: `app/routes/analysis.py`
  - Bei deaktiviertem Billing bleibt der Endpoint absichtlich offen
  - Fuer Produktion ist das konsistent, solange Billing/Feature-Gating wirklich aktiv ist

## Niedrig

- `/live` ist absichtlich Login-protected und leitet sauber auf `/auth/login` um
- `/messages` und `/upload` leiten ebenfalls korrekt auf Login um
- `/pulse` und `/dashboard` antworten im aktuellen Stand mit `200`

## Sofort behoben

- `app/services/google_credentials.py`
  - `google_credentials_status()` repariert
  - Ergebnis: `/api/providers/status` hat keinen internen `NameError` mehr fuer Google-Status

- `app/routes/query_api.py`
  - doppelte `POST /api/pulse/search`-Route entfernt
  - neuer konfliktfreier Alias: `POST /api/pulse/query/search`

- `app/templates/base.html`
  - globales Legacy-Script `agent.js` entfernt
  - Ergebnis: kein totes Auth-/Profil-JS mehr im Standard-Bundle

- `app/routes/analysis.py`
  - `DeepSearch` mit serverseitigem `FEATURE_FULL_ACCESS`-Guard versehen

- `app/routes/provider_status.py`
  - optionale Provider ohne Konfiguration liefern kontrolliert `disabled`
  - weniger Exception-Rauschen fuer YouTube/Twitch im Normalbetrieb

## Noch offen

- Entscheiden, ob `/health` oder `/healthz` der einzige offizielle Deploy-/Monitoring-Endpunkt sein soll
- Optional: unbenutzte Datei `app/static/js/agent.js` aus dem Repo entfernen
- Optional: `DeepSearch` auch im Billing-off-Modus hart sperren, falls selbst im Dev/Staging kein offener Zugriff gewuenscht ist

## Stabilitaetseinschaetzung

- Basisstabilitaet: brauchbar
- App-Boot: ok
- Kernrouting: ok
- API-Verknuepfungen Frontend <-> Backend: ueberwiegend ok
- Produktionsreife: deutlich sauberer, Hauptrestpunkt ist jetzt vor allem die Health-/Deploy-Vereinheitlichung und generelle Feature-Policy
