import requests
import json

BASE = "http://127.0.0.1:5000"

def check(method, path, data=None):
    url = BASE + path
    try:
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url, json=data or {})
        try:
            js = r.json()
            normalized = isinstance(js, dict) and "success" in js and ("data" in js or "error" in js)
        except Exception:
            js = None
            normalized = False
        print(f"{method} {path} -> {r.status_code} | normalized: {normalized} | body: {json.dumps(js) if js else r.text[:200]}")
        return r.status_code, normalized, js
    except Exception as e:
        print(f"{method} {path} -> EXCEPTION: {e}")
        return None, False, None

endpoints = [
    ("GET", "/api/providers/status"),
    ("GET", "/api/einnahmen/"),
    ("GET", "/api/einnahmen/summary"),
    ("POST", "/api/einnahmen/query"),
    ("POST", "/api/pulse/query"),
    ("POST", "/api/pulse/query/search"),
    ("POST", "/api/pulse/search"),
]

for method, path in endpoints:
    check(method, path)
