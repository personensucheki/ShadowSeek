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
    resp = {"success": False, "message": message}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), status
