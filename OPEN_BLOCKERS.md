# OPEN_BLOCKERS.md
Stand: 2026-04-13

## Offene Blocker (Priorisiert)
1. Produktions-ENV in Render final pruefen und setzen:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `PUBLIC_BASE_URL`
   - `APP_BASE_URL`
   - `UPLOAD_DIRECTORY=/data/uploads`
   - `BILLING_GATING_ENABLED`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `STRIPE_PRICE_ID_ABO_1..4`

2. Persistent Disk in Render sicherstellen:
   - Mount auf `/data`
   - Schreibrechte und Persistenz fuer `/data/uploads`

3. Demo-Pfade fuer Produktion absichern:
   - `ENABLE_DEMO_PROVIDER=false`
   - `FEED_DEMO_ENABLED=false` in Production behalten

## Offene Risiken (kein harter Blocker, aber relevant)
- TikTok/OSINT-Provider koennen anti-bot/challenge Seiten liefern.
- API-Consistency ist im Kern gefixt, aber nicht in allen Alt-Endpunkten vollstaendig vereinheitlicht.
- `.env` enthaelt doppelte Schluessel (Konfigurationsdrift-Risiko).

## Bereits sofort behoben
- TikTok-Scraper Integrationsfehler und Fetcher-Crash
- Search-Meta-Contract (`ai_reranking_applied`) und DeepSearch-Fallbacks
- Pulse/Live/Dashboard Contract-Brueche
- Summary-Fehlerfallback mit klarer Collector-Status-Angabe

## Finale Aussage
`live-ready-with-warnings`
