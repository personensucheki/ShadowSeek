# OSINT_ENGINE_TODO_MASTER.md

## Scope
Production-grade modular OSINT intelligence engine layered on existing ShadowSeek foundations.

## Completed in this iteration
1. Unified envelope helpers for new OSINT APIs (`success`, `data`, `error`, `meta`).
2. Shared provider utilities (timeouts, retries, rate-limiting, error mapping, normalization).
3. Shared score/confidence helpers.
4. Hardened upload image validation service.
5. New services:
- `identity_service`
- `youtube_service`
- `tiktok_service`
- `reverse_image_service`
- `profile_analysis_service`
- `social_graph_service`
- `availability_service`
- `geo_service`
- `content_pattern_service`
- `tracking_service`
6. New OSINT API blueprint with endpoints:
- `POST /api/identity/match`
- `POST /api/reverse-image`
- `POST /api/analyze-profile`
- `POST /api/social-graph/build`
- `POST /api/username/check`
- `POST /api/content-pattern/analyze`
- `POST /api/watchlist/upsert`
7. New DB models + migration for OSINT engine tables.
8. New API envelope tests for OSINT endpoints.

## Remaining high-priority TODO
1. Add persistent provider-level observability and latency metrics.
2. Add YouTube/TikTok integration tests with mocked network fixtures.
3. Add stricter per-endpoint rate buckets for new OSINT routes.
4. Extend identity engine with additional providers (Reddit, Instagram public metadata).
5. Implement optional Playwright fallback execution path for TikTok behind feature flag.
6. Add watchlist read/list/delete endpoints.
7. Build frontend result panels for identity/risk/graph/reverse-image.
8. Add background tracking jobs only after API/model stability gate.
