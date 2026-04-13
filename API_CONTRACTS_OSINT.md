# API_CONTRACTS_OSINT.md

## Global contract (new OSINT endpoints)
All new OSINT endpoints return:
```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

On failure:
```json
{
  "success": false,
  "data": {},
  "error": "human-readable error",
  "meta": {"endpoint": "..."}
}
```

## Endpoints

### POST `/api/identity/match`
Input:
- `username` (required)
- `realname`, `clanname`, `plz`, `bio`, `known_platform` (optional)

Output `data`:
- `profiles[]` with
  - `platform`, `username`, `display_name`, `bio`, `links`, `avatar_url`
  - `evidence[]`, `score`, `confidence`, `match_reasons[]`
- `meta`

### POST `/api/reverse-image`
Multipart input:
- `image` (required)
- `source_platform`, `source_profile` (optional persistence context)

Output `data`:
- `possible_matches[]`
- `hashes` (`phash`, `dhash`)

### POST `/api/analyze-profile`
Input:
- profile payload fields (username/display_name/bio/links/platform/posting_metadata...)

Output `data`:
- `fake_score`, `bot_score`, `scam_score`, `risk_level`, `indicators[]`, `explanation`, `llm_used`

### POST `/api/social-graph/build`
Input:
- `profiles[]`

Output `data`:
- `nodes[]`, `edges[]`, `clusters[]`, `confidence_summary`

### POST `/api/username/check`
Input:
- `username` (required)
- `platforms[]` (optional)

Output `data`:
- `results[]` with `platform`, `username`, `state`, `url`

### POST `/api/content-pattern/analyze`
Input:
- `posts[]`, `profiles[]`

Output `data`:
- repeated patterns and cluster flags

### POST `/api/watchlist/upsert`
Input:
- `normalized_username` (required)
- `platform`, `user_id`, `last_seen_bio`, `last_seen_avatar_hash`, `last_seen_links`

Output `data`:
- `watchlist` persisted record
