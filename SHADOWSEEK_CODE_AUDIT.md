# ShadowSeek Code Audit – Stabilization Update (2026-04-11)

## Umgesetzte Fixes

1. **RevenueEvent-Schema vereinheitlicht**
   - Neues kanonisches API-Schema für Revenue-Responses:
     - `id, platform, username, display_name, estimated_revenue, currency, captured_at, source, confidence`
   - Eingeführt über `app/services/revenue_events.py` und in den Revenue-Endpunkten verdrahtet.

2. **Collector idempotent + Dedupe**
   - Collector (`scripts/scraper_job.py`) normalisiert eingehende Legacy-Daten.
   - Soft-Dedupe im Service vor `db.session.add(...)`.
   - Doppelte Datensätze werden übersprungen statt erneut gespeichert.

3. **DB-Constraint für harte Eindeutigkeit**
   - `UniqueConstraint(platform, username, captured_at, source)` im Modell.
   - Migration erstellt, inklusive Backfill von Legacy-Spalten.

4. **Input-Validation Layer**
   - Neue Utility `app/services/request_validation.py`.
   - Validation und Pagination in:
     - `/api/einnahmen/`
     - `/api/einnahmen/query`
     - `/api/pulse/query`
     - `/api/pulse/search` (neu alias)
     - `/api/live/<platform>` und `/api/pulse/live/<platform>`

5. **CORS Setup**
   - API-weite CORS-Header per `after_request` integriert.
   - CORS für `"/api/*"` aktiviert.

6. **Pagination vorbereitet**
   - Unterstützte Query-Parameter: `limit`, `offset`, `page`.
   - Einheitlich über `parse_pagination(...)`.

7. **Legacy-Hinweise markiert**
   - `# TODO remove legacy mapping` im Query-Filter (`kategorie -> typ`).

## Offene Punkte

1. **Legacy-Spaltenabbau**
   - `betrag/waehrung/typ/quelle/zeitpunkt` sind für Backward-Kompatibilität noch vorhanden.
   - Geordneter Remove nach Frontend/Export-Komplettumstellung empfohlen.

2. **/api/upload/* Endpunkte**
   - Aktuell keine dedizierten `/api/upload/*`-Routes vorhanden.
   - Falls Upload-APIs ergänzt werden, Validation Utility direkt wiederverwenden.

3. **Historische Datenqualität**
   - Falls bereits Dubletten mit identischen Unique-Schlüsseln existieren, braucht es ggf. einmaliges Cleanup-Script vor produktiver Migration.

## Empfohlene nächste Refactors

1. Revenue-Model komplett auf kanonische Felder umstellen und Legacy-Felder entfernen.
2. Frontend (`pulse.js`) um Datum/Confidence-Formatierung erweitern (ISO -> locale).
3. API-Response-Hülle vereinheitlichen (`{success, data, meta, errors}`).
4. Serverseitige Max-Limits zentral konfigurieren (Config statt magic numbers).
