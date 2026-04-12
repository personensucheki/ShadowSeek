# LIVE_ARCHITECTURE_PLAN

## Zielarchitektur
- Eigenes Flask-Backend (ShadowSeek) als zentrale Orchestrierungsschicht
- PostgreSQL für Stream-Metadaten
- Externe Provider (z.B. Google Live Stream API) für RTMP-Ingest und HLS-Ausgabe
- Cloud Storage Bucket als HLS-Ausgabeziel
- HLS-Playback im Frontend

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

---

*Stand: April 2026*
