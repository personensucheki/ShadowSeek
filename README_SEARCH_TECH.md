# ShadowSeek – Technische Zusammenfassung (maximal tiefer, legaler Search-Agent)

## 1. Wie tief sucht der Standardmodus?
- Nutzt 3–4 starke, normalisierte Varianten des Usernamens (QueryNormalizer)
- Fragt nur Kern-Provider (z. B. GitHub) ab
- Evidence Fusion & Deduplication: Doppelte/ähnliche Treffer werden zusammengeführt
- RankingService bewertet nach exaktem Match, Plattform, Evidenz, Confidence
- Ergebnisobjekte enthalten Score, Confidence, Match-Reasons, Quality-Flags
- Latenz und Ressourcenverbrauch sind niedrig

## 2. Was macht DeepSearch zusätzlich?
- Nutzt alle generierten Varianten (bis zu 10, inkl. Kontext/Weak Expansions)
- Fragt mehr Provider/Quellen parallel ab (später: weitere APIs, Foren, eigene DB)
- Evidence Fusion & Deduplication mit mehr Signalschichten
- Optional: KI-Reranking, ausführlichere Analyse
- Meta-Infos: Anzahl Varianten, Provider, Rohtreffer, Dedup-Statistik, DeepSearch-Status
- Gründlicher, aber kontrolliert (Timeouts, Caps, Logging)

## 3. Wie wird der Score berechnet?
- Exakter Username-Match: +2.0
- Variant/Normalized-Match: +1.0
- Gewählte Plattform: +0.7
- Mehrere Evidenzquellen: +0.1 pro zusätzlicher Quelle (max. +0.5)
- Confidence-Hint des Providers: bis +1.0
- Profile-URL vorhanden: +0.3
- Snippet/Titel plausibel: +0.2
- Quality-Flags: z. B. strong evidence, weak confidence
- Confidence-Level: high (>=2.5), medium (>=1.5), low (<1.5)
- Match-Reasons und Quality-Flags werden ausgegeben

## 4. Wie nutzt der Chatbot den Suchkontext?
- Greift auf die letzte Suche und die Summary zu (Persistenzmodul)
- Erklärt, warum Treffer oben stehen (Match-Reasons)
- Gibt Tipps bei leeren oder schwachen Ergebnissen
- Macht Vorschläge für DeepSearch, Plattformen, Varianten
- Keine Halluzination, sondern regelbasierte, nachvollziehbare Antworten

## 5. Offene Restpunkte
- Weitere Provider (z. B. Foren, eigene DB, Reverse-Image, Meta-APIs) ergänzen
- KI-Reranking (OpenAI, nur mit Key, mit Timeout/Fallback) produktiv machen
- Frontend-Integration für neue Meta-Infos und Chatbot-Antworten
- Performance-Optimierung bei vielen parallelen Provider-Requests
- Security-Review für neue Provider/Quellen
- Erweiterte Tests für Edge Cases und Fehlerfälle

---

**Status:** Alle Kernmodule sind modular, testbar und dokumentiert. Die Suche ist maximal tief, robust und rechtlich sauber – bereit für weitere Provider und Features.


# Revenue Collector & Demo-Seed

**Revenue Collector starten:**

	python scripts/run_revenue_collector.py

**Historische Testdaten erzeugen:**

	python scripts/seed_revenue_history.py

**Konfigurierbare Umgebungsvariablen:**

	REVENUE_COLLECTOR_INTERVAL=60
	ENABLE_DEMO_PROVIDER=true
	ENABLE_TIKTOK_PROVIDER=false
	REVENUE_DEFAULT_CURRENCY=EUR
	REVENUE_MAX_ROWS_PER_RUN=100
	REVENUE_WRITE_BATCH_SIZE=25
