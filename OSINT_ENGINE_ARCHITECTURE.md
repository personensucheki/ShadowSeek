# OSINT_ENGINE_ARCHITECTURE.md

## Principles
- Routes orchestrate only.
- Provider/network logic lives in `app/services`.
- All new OSINT endpoints return `{success,data,error,meta}`.
- Public/legal signals only.

## Layering
1. API Layer
- `app/routes/osint_engine.py`
- Validates request shape.
- Calls service layer only.

2. Service Layer
- `provider_utils.py`: HTTP client, retry, timeout, error mapping, rate limit pacing.
- `identity_service.py`: orchestration and explainable matching.
- `youtube_service.py`: YouTube Data API normalization.
- `tiktok_service.py`: public HTML/SIGI extraction with feature-flag fallback path.
- `reverse_image_service.py`: pHash/dHash generation + similarity matching.
- `profile_analysis_service.py`: heuristics-first risk model, optional OpenAI augmentation.
- `social_graph_service.py`: node/edge/clustering builder.
- `availability_service.py`: platform presence scanner.
- `geo_service.py`: auxiliary location normalization.
- `content_pattern_service.py`: repeated pattern detection.
- `tracking_service.py`: watchlist persistence/upsert.

3. Persistence Layer
- `app/models/osint_engine.py`
- Tables: `external_profiles`, `identity_matches`, `image_hashes`, `profile_analysis`, `graph_nodes`, `graph_edges`, `watchlist`.

4. Migration Layer
- `migrations/versions/20260413_0200_add_osint_engine_tables.py`

## Safety/Resilience
- Timeouts and retries centralized in `ExternalProviderClient`.
- Transient vs non-transient errors mapped consistently.
- Optional integrations fail gracefully when env keys are missing.
- OSINT engine can be globally disabled with `OSINT_ENGINE_ENABLED`.
