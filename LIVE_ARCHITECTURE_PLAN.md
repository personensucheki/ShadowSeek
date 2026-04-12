# Security-Policy: DATABASE_URL und Credential-Leaks

- Jede offengelegte `DATABASE_URL` mit Passwort/Secret gilt als kompromittiert.
- Nach Leak (z.B. Chat, Screenshot, Upload) **muss** das DB-Passwort/Secret rotiert werden.
- Neue Zugangsdaten **niemals** ins Repo, Frontend, Chat oder Uploads einbringen.
- Die `.env` mit echter `DATABASE_URL` darf **nur** lokal/serverseitig verwendet werden.
- Nach Rotation alte Secrets sofort deaktivieren.

# Lokale .env und Konfigurationspflichten

### Minimal erforderliche .env-Variablen (lokal und Produktion)

**Pflichtfelder:**
- SECRET_KEY
- DATABASE_URL
- PUBLIC_BASE_URL
- APP_BASE_URL
- UPLOAD_DIRECTORY
- BILLING_GATING_ENABLED
- GOOGLE_APPLICATION_CREDENTIALS
- GOOGLE_CLOUD_PROJECT_ID
- GOOGLE_CLOUD_OUTPUT_BUCKET
- GOOGLE_CLOUD_LOCATION
- GOOGLE_SERVICE_ACCOUNT_EMAIL

**Stripe-Variablen** können lokal leer bleiben, wenn Billing nicht getestet wird.

**Wichtig:**
- Die Datei `.env` im Projekt-Root wird beim lokalen Start und Testen geladen (z.B. via python-dotenv oder Flask).
- Die Variable `DATABASE_URL` **muss** gesetzt sein, sonst schlägt der App-Start und jede Migration fehl.
- Google-Credentials und -Konfiguration **müssen** serverseitig gesetzt sein, sonst liefert der Provider-Adapter einen klaren Fehlerstatus.

### Config-Loading und Priorität
- `.env` im Projekt-Root wird zuerst geladen (lokal).
- In Produktion werden Environment-Variablen (z.B. Render, Docker, CI) priorisiert.
- Falls mehrere Config-Pfade existieren, gilt: **Environment > .env > Default**.

### Fehlerfall-Handling
- Fehlt `DATABASE_URL`, gibt das Backend einen klaren Fehler beim Start/Migration aus (kein späterer DB-Crash).
- Fehlt Google-Config, liefert der Provider-Adapter einen klaren Fehlercode (`provider_not_configured`, `credentials_missing` etc.), aber kein globaler Import- oder App-Crash.

### Sicherheit
- Niemals Secrets ins Repo oder ins Frontend.
- Service-Account-JSON **nur** serverseitig, niemals im Repo oder Frontend.

---
# Programmatische Google-Integration

### Warum erfolgt die Google-Integration programmatisch?
- Die Google Cloud Console bietet keinen stabilen, produktiven Klickpfad für Input/Channel-Erstellung.
- ShadowSeek orchestriert Input Endpoint, Channel und Status **vollständig serverseitig** via Google Live Stream API.
- Die gesamte Provisionierung (Input, Channel, Output, Status) erfolgt über das Backend – keine manuelle UI-Interaktion nötig.
- Nur so ist eine sichere, nachvollziehbare und automatisierbare Bereitstellung von Livestreams möglich.

### Warum ist der UI-Klickpfad nicht der Produktionsweg?
- Die Google UI ist für Einzel-Setups und Testzwecke gedacht, nicht für skalierbare, automatisierte Livestream-Orchestrierung.
- ShadowSeek benötigt eine API-gesteuerte, reproduzierbare Steuerung (z.B. für mehrere parallele Streams, Status-Checks, Fehlerbehandlung).

### Orchestrierung durch ShadowSeek
- ShadowSeek steuert Input Endpoint, Channel und Status **immer** serverseitig.
- Die API liefert alle relevanten Provider- und Playback-Informationen strukturiert aus.
- Status- und Fehlercodes werden klar und nachvollziehbar an das Frontend/API zurückgegeben.

### OBS/RTMP bleibt Phase-1-Produktivpfad
- Für die erste Produktivphase bleibt OBS/RTMP der empfohlene Weg für Broadcaster.
- Die Google-Integration dient als orchestrierter, sicherer Backend-Provider.

### Direct-PC bleibt vorerst nicht produktiv
- Direkte PC-Streams ohne Provider/OBS werden **nicht** als produktiver Pfad unterstützt.
# LIVE_ARCHITECTURE_PLAN

## Zielarchitektur
- Eigenes Flask-Backend (ShadowSeek) als zentrale Orchestrierungsschicht
- PostgreSQL für Stream-Metadaten
- Externe Provider (z.B. Google Live Stream API) für RTMP-Ingest und HLS-Ausgabe
- Cloud Storage Bucket als HLS-Ausgabeziel
- HLS-Playback im Frontend

## Region / Location (Google Provider)
- Empfohlene Default-Region für dieses Setup: **`europe-west3` (Frankfurt)**.
- Warum:
  - europäische/deutsche Nähe (Latenz),
  - konsistente Provider-Ressourcen (Inputs/Channels/Endpoints in einer Region),
  - besser planbar für Betrieb/Observability.
- ShadowSeek speichert und nutzt diese Location **serverseitig** via `GOOGLE_CLOUD_LOCATION`.

## Provider-Output-Referenzierung
- Das LiveStream-Modell speichert:
  - provider
  - provider_input_id
  - provider_channel_id
  - playback_url
  - ingest_url
  - stream_key
  - status (draft, provisioning, ready, live, ended, error)
- Keine Fake-Werte im Produktivsystem
- Backend liefert diese Felder in API-Responses aus

## Service-Schicht
- ProviderAdapter-Konzept für externe Provider
- Trennung: Metadaten im Backend, Ingest/Playback beim Provider
- Dummy/Stub für Google-Live-Provider implementiert

## API-Design
- Einheitliche JSON-Struktur für Live-Endpunkte
- Stream-Objekte enthalten alle relevanten Provider-/Playback-Felder

## Cloud Storage
- Cloud Storage dient als HLS-Ausgabeziel für Provider
- ShadowSeek speichert nur Referenzen auf Provider/HLS-Ressourcen
- Kein direkter Upload/Playback im Backend

### Output-Bucket Konvention
- `GOOGLE_CLOUD_OUTPUT_BUCKET` ist **nur der Bucket-Name** (z.B. `shadowseek-hls-output`).
  - kein `gs://` Prefix
  - keine URL
  - kein Unterpfad/Objektpfad
- Hintergrund: Die Google Live Stream API schreibt die HLS-Ausgabe in **Google Cloud Storage**.
  - ShadowSeek speichert/liest nur die **Bucket-Referenz** (Konfiguration) und später Playback-Referenzen (URLs).
  - Der Output-Bucket ist Teil der Provider-Konfiguration und wird serverseitig validiert.

## Sicherheit & Orchestrierung
- Backend bleibt zentrale Steuerung
- Kein "fertig live"-Flow ohne echten Provider
- Status robust und nachvollziehbar

## Credential-Handling (serverseitig, secret-frei im Repo)
- **Service-Account JSON** ist ein **serverseitiges Credential**.
  - Wird **nur** auf dem Server/Container bereitgestellt (z.B. Secret Mount / `/etc/secrets/...`).
  - Wird **niemals** ins Repo committed.
  - Wird **niemals** ins Frontend/JS/Template eingebaut.
- ShadowSeek Backend nutzt `GOOGLE_APPLICATION_CREDENTIALS` (Dateipfad) zur **Runtime-Ladung**.
- Konfiguration erfolgt ausschließlich über Environment-Variablen:
  - `GOOGLE_CLOUD_PROJECT_ID`
  - `GOOGLE_CLOUD_LOCATION`
  - `GOOGLE_CLOUD_OUTPUT_BUCKET`
  - `GOOGLE_APPLICATION_CREDENTIALS`
  - `GOOGLE_SERVICE_ACCOUNT_EMAIL` (optional, Validierung/Logging)
- Das Backend liefert nur **Status/Error-Codes** für die UI, keine Secrets.

## Security-Policy: kompromittierte Credentials
- **Offengelegte Service-Account JSONs / private keys gelten als kompromittiert** (z.B. via unsicherem Chat/Upload/Leak).
- Konsequenz:
  - **Betroffene Keys müssen gelöscht/rotiert werden** (neuer Service-Account-Key erstellen, alten deaktivieren/löschen).
  - **Der Service Account selbst darf bestehen bleiben** (Identität/Rollen/Bindings bleiben).
  - **Nicht-geheime Metadaten** wie `project_id`, Bucket-Name, Region/Location können weiterverwendet werden.
  - `project_id` ersetzt **kein** Credential: ohne gültigen privaten Key gibt es keine Auth.
- ShadowSeek Zielzustand:
  - kompromittierte Secrets konsequent ersetzen/rotieren,
  - niemals Secrets ins Frontend,
  - niemals Credentials ins Repo.

---

*Stand: April 2026*
