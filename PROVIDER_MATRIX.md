# PROVIDER_MATRIX.md

## Current Providers

### Identity Engine Sources
- YouTube (`youtube_service.py`)
  - Requires: `YOUTUBE_API_KEY`
  - Capabilities: channel search, channel stats, handle/username lookup, recent videos.
  - Mode when missing key: disabled with explicit error in normalized response.

- TikTok Public (`tiktok_service.py`)
  - Requires: none for public HTML fetch.
  - Capabilities: public profile extraction by username, candidate search, public bio links.
  - Fallback: `ENABLE_TIKTOK_PLAYWRIGHT_FALLBACK` (reserved path).

- Username Presence (`availability_service.py`)
  - Requires: none.
  - Capabilities: claim state probing (`claimed`, `likely_claimed`, `not_found`, `unclear_or_rate_limited`).

### Analysis Sources
- Reverse Image (`reverse_image_service.py`)
  - Requires: valid image upload.
  - Capabilities: pHash/dHash compute + similarity against stored hashes.

- Profile Risk (`profile_analysis_service.py`)
  - Local heuristics: always available.
  - Optional LLM: uses `OPENAI_API_KEY` with timeout/fallback.

## Shared Controls
- Timeout / retry / request headers: `provider_utils.ExternalProviderClient`.
- Score/confidence normalization: `score_utils.py`.
- Optional integration guards: `env_guards.py`.
