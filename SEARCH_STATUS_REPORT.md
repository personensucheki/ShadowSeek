# SEARCH_STATUS_REPORT.md
Stand: 2026-04-13

## Realbestand
- Endpoint: `POST /api/search`
- Komponenten: Payload-Validierung, Username-Variationen, Provider-Fanout, Ranking, Dedup, Reverse-Image-Links, optional AI-Rerank
- TikTok-Provider via `app/providers/tiktok_provider.py` + Modul `app/modules/tiktok_scraper`

## Funktioniert
- Rankingfelder (`match_score`, `confidence`, `match_reason`) werden durchgereicht.
- Dedup + per-platform-Limits laufen.
- Reverse-Image-Links (Lens/TinEye/Yandex) werden generiert.
- DeepSearch-Flow und Meta-Ausgabe stabil.

## Teilweise funktioniert
- Externe Plattformen (insb. TikTok) koennen Challenge/Blockseiten liefern.
- AI-Reranking nur bei verfuegbarem OpenAI-Key.

## Fehlend / riskant
- Historische Meta-Feldnamenabweichungen verursachten Contract-Brueche.
- Public-Source Verhalten war zu konservativ fuer erwartete Defaults.

## Sofort behoben
- TikTok-Scraper Fixes:
  - Runner-Importe korrigiert
  - Profil-URLs unterstuetzt
  - Fetcher-Fehler mit `BrowserContext.user_agent` behoben
- Search-Fixes:
  - `meta.ai_reranking_applied` hinzugefuegt
  - `public_sources` default auf aktiv gesetzt
  - DeepSearch aktiviert AI-Rerank default
  - Rerank-Pfad auf `rerank_profiles_with_openai()` vereinheitlicht

## Verbleibende Blocker
- Keine internen Code-Blocker.
- Externe Provider-Limits/Anti-Bot bleiben ein betriebliches Risiko.
