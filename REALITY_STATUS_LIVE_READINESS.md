# ShadowSeek – Reality Status / Live Readiness (Stand: 2026-04-12)

## Realitätscheck

### Core Product Path (Search)
- **UI** vorhanden und technisch angebunden.
- **Backend** liefert echte JSON-Struktur.
- “DeepSearch/AI” war in Teilen **nur UI/Stub**, jetzt optional real (Public Search + AI Rerank) – abhängig von Keys.

### Auth
- Funktional: ja.
- Security: noch nicht production-hart (CSRF exempt + fehlende Rate-Limits).

### Billing
- Codepfad: real.
- Live-Funktion hängt an Stripe-Secrets, Webhook-Secret, Price IDs.
- Default-IDs im Code sind wartungsriskant.

### Live/Realtime
- Routen/Modelle existieren.
- Schutz/Abuse/Produktreife gemischt; Live APIs brauchen Audit-Härtung vor Public Launch.

---

## Einschätzung

**Ready with warnings**:
- Für private/closed beta: möglich, wenn Keys gesetzt und Logs/Monitoring aktiv.
- Für public launch: **noch nicht** ohne Security-Härtung (Auth + Rate-Limits) und klare Deaktivierung nicht deploybarer Module.

