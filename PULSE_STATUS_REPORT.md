# PULSE_STATUS_REPORT.md
Stand: 2026-04-13

## Realbestand
- Endpunkte: `/api/pulse/query`, `/api/pulse/query/search`, `/api/pulse/live/<platform>`, `/api/einnahmen/*`, `/api/einnahmen/summary`
- Schema: `EinnahmeInfo` mit Unique-Constraint fuer Event-Dedupe
- Collector: `RevenueLiveCollector` + Provider-Registry

## Funktioniert
- Query/Filter/Pagination fuer Revenue laufen.
- Profile-Scan Integration in Pulse-Query/Pulse-Live funktioniert.
- Summary liefert stabilen Fallback bei Datenbankproblemen.

## Teilweise funktioniert
- Legacy-Felder (`betrag`, `waehrung`, `typ`, `quelle`, `zeitpunkt`) laufen parallel zu neuem Event-Schema.
- Response-Envelopes historisch gemischt.

## Fehlend / riskant
- `ENABLE_DEMO_PROVIDER` standardmaessig `true` (produktionsriskant).
- Nicht alle Pulse-Endpunkte folgen bereits einem einheitlichen Contract.

## Sofort behoben
- Pulse Query/Life Responses auf kompatible Top-Level-Contracts mit `success` stabilisiert.
- Dashboard-Summary liefert jetzt kompatibel:
  - top-level Felder (legacy)
  - `data`-Envelope (neuer Standard)
- Fallback-Status auf `collector_status=unavailable` korrigiert.

## Verbleibende Blocker
- Operativer Blocker: Demo-Provider vor Produktion deaktivieren.
