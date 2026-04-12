import time
from flask import request

# --- Minimal Rate Limiting (in-memory, per-process, IP+endpoint, fixed window) ---
# Limits (documented for report extraction):
#   /api/search: 10/minute/IP
#   /api/suggest: 20/minute/IP
#   /auth/login: 5/minute/IP
#   /auth/register: 3/minute/IP
#   /api/pulse/query, /api/pulse/query/search: 10/minute/IP
_RATE_LIMITS = {
    "/api/search": (10, 60),
    "/api/suggest": (20, 60),
    "/auth/login": (5, 60),
    "/auth/register": (3, 60),
    "/api/pulse/query": (10, 60),
    "/api/pulse/query/search": (10, 60),
}
_rate_limit_state = {}

def check_rate_limit(endpoint: str) -> tuple[bool, int]:
    """Returns (allowed, remaining)"""
    from flask import has_request_context
    if not has_request_context():
        return True, 9999
    ip = request.remote_addr or "?"
    key = (endpoint, ip)
    limit, window = _RATE_LIMITS.get(endpoint, (0, 0))
    if not limit:
        return True, 9999
    now = int(time.time())
    bucket = now // window
    state = _rate_limit_state.setdefault(key, {})
    if state.get("bucket") != bucket:
        state["bucket"] = bucket
        state["count"] = 0
    state["count"] = state.get("count", 0) + 1
    remaining = max(0, limit - state["count"])
    allowed = state["count"] <= limit
    if not allowed:
        import logging
        logging.warning(f"Rate limit exceeded: {endpoint} ip={ip} count={state['count']} limit={limit}/{window}s")
    return allowed, remaining
"""
API Response Utilities for ShadowSeek
- Standardize success/error responses
- Centralize error formatting
"""
from flask import jsonify

def api_success(data=None, message=None, status=200):
    resp = {"success": True}
    if data is not None:
        resp["data"] = data
    if message:
        resp["message"] = message
    return jsonify(resp), status

def api_error(message, status=400, errors=None):
    # Backwards-compatible: some callers/tests expect `error`, newer code used `message`.
    resp = {"success": False, "message": message, "error": message}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), status
