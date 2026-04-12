# ShadowSeek – Missing & Fake Features Report (Stand: 2026-04-12)

Ziel: Alles auflisten, was im UI/Code “funktional wirkt”, aber technisch **stub/dummy/halb** ist oder im Livebetrieb gefährlich wäre.

---

## 1) Search: Provider/AI waren Stub (vor Fix)

- Bereich: Search Engine
- Fundstelle: `D:\ShadowSeek\app\services\search_service.py` (Funktionen: `collect_serper_profiles`, `collect_bing_profiles`, `discover_profiles`, `scan_platform`, `should_ai_rerank`, `rerank_profiles_with_openai`)
- Beschreibung: Funktionen waren vorhanden, haben aber **immer** leere Ergebnisse geliefert bzw. `False`.
- Warum unecht/gefährlich:
  - UI zeigt “Plattformen werden geprüft / KI Bewertung”, Backend hat real nur Kandidatenlinks generiert.
  - Nutzer glauben an “Verifikation”, aber es gibt keine echte Prüfung.
- Auswirkung Livebetrieb:
  - Produktversprechen/Trust bricht; falsche Erwartung an “gefunden”.
- Sicherheitsrisiko: indirekt (kein Exploit), aber hohes Produkt-/Compliance-Risiko.
- Status: **Bereinigt/Teilfix** – Public Search + AI Rerank wurden minimal implementiert (öffentliches Web, kein Scraping).

---

## 2) DeepSearch: Screenshot-Feature wirkt vorhanden, ist deploy-seitig nicht real

- Bereich: DeepSearch Module
- Fundstelle: `D:\ShadowSeek\app\services\screenshot_engine.py`
- Beschreibung: Screenshot-Endpoint existiert und UI nutzt ihn, aber Playwright ist nicht in `requirements.txt`.
- Warum unecht/gefährlich:
  - In Produktion kommt “Playwright ist nicht installiert.” → Feature ist praktisch tot.
- Auswirkung Livebetrieb:
  - UI Module bleiben leer oder zeigen Fehler.
- Sicherheitsrisiko: gering/mittel (SSRF-Protection ist implementiert), aber Betriebsausfall.
- Status: Offen (Deploy-Pfad fehlt)

---

## 3) Legacy/Dummy: Zusätzliches `models.py` mit anderem User-Modell

- Bereich: Data Models
- Fundstelle: `D:\ShadowSeek\models.py`
- Beschreibung:
  - Enthält eigenes `User` Modell mit hardcodierten Defaults (Support-Mail/PayPal-Link etc.) und Encoding-Artefakten.
  - Parallel existiert das echte Modell `D:\ShadowSeek\app\models\user.py`.
- Warum unecht/gefährlich:
  - Gefahr von falschen Imports/Verwechslung.
  - Hinweise auf “Demo/Seed”-Artikulation im Produktivpfad.
- Auswirkung Livebetrieb:
  - Wartbarkeit/Debugging schwierig, potenziell Dateninkonsistenzen.
- Sicherheitsrisiko: mittel (falsche Defaults, ungeprüfte Imports).
- Status: Offen (Empfehlung: entfernen oder klar archivieren)

---

## 4) Live API v2: Route-Prefixing war kaputt (falsche URLs)

- Bereich: Routing/API
- Fundstelle: `D:\ShadowSeek\app\helpers\factory.py`
- Beschreibung: Blueprint mit `/api/live/...` Routen wurde zusätzlich mit `url_prefix="/api"` registriert → `/api/api/live/...`.
- Warum unecht/gefährlich:
  - Clients treffen die beabsichtigten URLs nicht.
- Auswirkung Livebetrieb:
  - Feature wirkt vorhanden, ist aber faktisch unbenutzbar.
- Sicherheitsrisiko: nein
- Status: **Bereinigt** (Prefix-Duplikat entfernt)

