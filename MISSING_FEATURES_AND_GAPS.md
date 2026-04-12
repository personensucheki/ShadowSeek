# ShadowSeek – Missing Features & Gaps (Stand: 2026-04-12)

Diese Liste beschreibt **fehlende oder unvollständige** Teile (mit Fundstelle, Risiko, Priorität, Status).

Legende Priorität:
- P0 = Live-Blocker / Security critical
- P1 = sehr wichtig für Kernfluss
- P2 = wichtig, aber nicht blocker
- P3 = nice-to-have

---

## Auth / Security

### P0 – CSRF-Schutz auf Auth-Routen inkonsistent
- Bereich: Auth/Session Security
- Fundstelle: `D:\ShadowSeek\app\routes\auth.py`
- Was fehlt: CSRF-Policy für browserbasierte Login/Register Requests (aktuell `@csrf.exempt`)
- Auswirkung: CSRF-Angriffsfläche bei session-basierten Flows
- Risiko: Hoch
- Status: **Offen** (im Security-Report mit Fix-Vorschlag)

### P1 – Rate-Limiting / Abuse Protection fehlt global
- Bereich: API-Härtung
- Fundstellen: mehrere `/api/*` Endpunkte (Search, Live, Auth, Chatbot)
- Was fehlt: IP-/User-basiertes Rate-Limiting + einfache Abuse-Guards
- Auswirkung: DoS/Bruteforce/Spam möglich
- Risiko: Mittel/Hoch
- Status: Offen

---

## Search / DeepSearch

### P1 – “DeepSearch / AI Rerank” war teilweise Stub
- Bereich: Search Engine
- Fundstelle: `D:\ShadowSeek\app\services\search_service.py`
- Was fehlte: echte Provider-Integration + AI-Rerank
- Auswirkung: UI wirkt funktional, Ergebnis ist aber nur Kandidatenlinks
- Risiko: Produkt-/Trust-Risiko
- Status: **Teilweise behoben** (Public-Search + AI-Rerank minimal implementiert, ToS/Privacy-konform)

### P2 – Screenshot Engine deployt nicht out-of-the-box
- Bereich: DeepSearch Module
- Fundstelle: `D:\ShadowSeek\app\services\screenshot_engine.py`
- Was fehlt: Playwright Dependency + Browser Install Steps (nicht in `requirements.txt`)
- Auswirkung: `/search/screenshot` liefert in Produktion “Playwright ist nicht installiert.”
- Risiko: Mittel
- Status: Offen (Konzept vorhanden, Deploy fehlt)

---

## Live / Streaming

### P1 – Route-Prefix Bug (live_api_v2) führte zu /api/api
- Bereich: Routing
- Fundstelle: `D:\ShadowSeek\app\helpers\factory.py`
- Was fehlte: korrekte Blueprint-Registrierung ohne doppeltes Prefix
- Auswirkung: Clients treffen 404 / falsche URLs
- Risiko: Mittel
- Status: **Behoben** (Blueprint ohne `url_prefix="/api"` registriert)

### P2 – Auth/Guards an Live APIs teilweise unklar
- Bereich: Live APIs
- Fundstellen: `D:\ShadowSeek\app\routes\live_api_v2.py`, `D:\ShadowSeek\app\routes\live_api.py`
- Was fehlt: konsistente Auth-Checks, ggf. Feature-Gating, Rate-Limits
- Auswirkung: Missbrauch möglich
- Risiko: Mittel
- Status: Offen

---

## Billing / Subscription

### P2 – Stripe Default Price IDs hardcodiert (Produktiv-Risiko)
- Bereich: Billing
- Fundstelle: `D:\ShadowSeek\app\services\billing.py`
- Was fehlt: saubere Konfiguration/Mapping über ENV pro Umgebung, ohne feste IDs im Code
- Auswirkung: falsches Mapping bei Price-Änderungen
- Risiko: Mittel
- Status: Offen (funktional, aber wartungsriskant)

---

## Datenmodelle / Legacy

### P2 – Doppeltes User-Model (Legacy Datei)
- Bereich: Data Model Konsistenz
- Fundstelle: `D:\ShadowSeek\models.py` vs `D:\ShadowSeek\app\models\user.py`
- Was fehlt: eindeutige Source of Truth, Entfernen/Archivieren des Legacy-Modells
- Auswirkung: Verwirrung, falsche Imports möglich
- Risiko: Mittel
- Status: Offen

