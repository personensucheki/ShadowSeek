import requests
import re

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# Utility to extract CSRF token from HTML
CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
def get_csrf_token(html):
    m = CSRF_RE.search(html)
    return m.group(1) if m else None

def test_route(name, form_url, post_url, post_data, expect_success_text=None):
    print(f"\n=== {name.upper()} ===")
    # 1. GET form to fetch CSRF token
    r = s.get(BASE + form_url)
    html = r.text
    csrf_token = get_csrf_token(html)
    print(f"Fetched CSRF token: {csrf_token}")
    # 2. POST without CSRF token
    data_no_csrf = post_data.copy()
    if 'csrf_token' in data_no_csrf:
        del data_no_csrf['csrf_token']
    r_no_csrf = s.post(BASE + post_url, data=data_no_csrf, allow_redirects=False)
    print(f"POST without CSRF: status={r_no_csrf.status_code}, body={r_no_csrf.text[:200]}")
    # 3. POST with valid CSRF token
    data_with_csrf = post_data.copy()
    data_with_csrf['csrf_token'] = csrf_token
    r_with_csrf = s.post(BASE + post_url, data=data_with_csrf, allow_redirects=False)
    print(f"POST with CSRF: status={r_with_csrf.status_code}, body={r_with_csrf.text[:200]}")
    if expect_success_text:
        print(f"Success text present: {expect_success_text in r_with_csrf.text}")

test_route(
    "login",
    "/",  # Home page renders login modal
    "/auth/login",
    {"username": "idontexist", "password": "wrong"},
    expect_success_text="Login fehlgeschlagen"
)

test_route(
    "register",
    "/",  # Home page renders register modal
    "/auth/register",
    {"username": "idontexist", "email": "idontexist@example.com", "password": "wrongpass", "password2": "wrongpass"},
    expect_success_text="existiert"
)

test_route(
    "forgot-password",
    "/",  # Home page renders forgot modal
    "/auth/forgot-password",
    {"email": "idontexist@example.com"},
    expect_success_text="Passwort-Reset"
)

# LOGOUT: must be POST, check both with and without CSRF
def test_logout():
    print("\n=== LOGOUT ===")
    # Get CSRF token from home page
    r = s.get(BASE + "/")
    html = r.text
    csrf_token = get_csrf_token(html)
    # POST without CSRF
    r_no_csrf = s.post(BASE + "/auth/logout", data={}, allow_redirects=False)
    print(f"POST /auth/logout without CSRF: status={r_no_csrf.status_code}, body={r_no_csrf.text[:200]}")
    # POST with CSRF
    r_with_csrf = s.post(BASE + "/auth/logout", data={"csrf_token": csrf_token}, allow_redirects=False)
    print(f"POST /auth/logout with CSRF: status={r_with_csrf.status_code}, body={r_with_csrf.text[:200]}")

test_logout()
