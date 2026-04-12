# ShadowSeek – Security & Fake Cleanup Report (Stand: 2026-04-12)

Diese Datei benennt konkrete Security-Risiken, Fake-/Demo-Schutzmechanismen, Dev-Reste und Fix-Status.

---

## 1) CSRF / Session Security (P0)

### Finding: `@csrf.exempt` auf Login/Register
- Fundstelle: `D:\ShadowSeek\app\routes\auth.py`
- Risiko: Hoch (CSRF bei browserbasierten Session-Flows möglich)
- Kontext: App nutzt Cookie Session + setzt `session["user_id"]` etc.
- Empfehlung (minimal, ohne großen Umbau):
  - CSRF für Form-basierte Browser Requests aktiv lassen.
  - Für JSON-Clients: Token-Header verpflichtend oder separate tokenbasierte Auth (z.B. API-Key/JWT) einführen.
  - Alternativ: Login/Register nur per JSON + SameSite/Origin Checks erzwingen.
- Status: **Offen** (noch nicht in Code gehärtet; Entscheidung nötig, weil UI/Clients betroffen).

---

## 2) CORS Defaults (P1)

### Finding: Default `Access-Control-Allow-Origin: *` auf `/api/*`
- Fundstelle: `D:\ShadowSeek\app\helpers\factory.py` (`add_api_cors_headers`)
- Risiko: Mittel
- Details:
  - In Kombination mit `credentials: "same-origin"` im Frontend aktuell meist ok,
    aber sobald Cookies cross-site oder Frontend/Backend getrennte Origins sind, muss CORS präzise sein.
- Empfehlung:
  - `API_CORS_ALLOWED_ORIGINS` in Prod auf konkrete Origin(s) setzen.
  - Keine `*` in Prod, wenn Credentials genutzt werden sollen.
- Status: Offen (Config-Thema)

---

## 3) Abuse/Rate Limiting (P1)

### Finding: Keine Rate-Limits auf Auth/Search/Live
- Risiko: Mittel/Hoch
- Empfehlung:
  - `flask-limiter` oder Reverse-Proxy (Nginx/Cloudflare) Rate-Limits.
  - Minimal: Login + Search endpoint limitieren (z.B. 10/min/IP + 3/min/user).
- Status: Offen

---

## 4) Screenshot Engine SSRF (P2)

### Positive: SSRF-Mitigation ist vorhanden
- Fundstelle: `D:\ShadowSeek\app\services\screenshot_engine.py`
- Schutz:
  - Blocked private/loopback/link-local/reserved IP ranges
  - Hostname regex + DNS resolve check
- Restrisiko:
  - DNS Rebinding/IPv6 edge cases, Proxy-Umgebungen, etc.
- Status: OK (aber Feature ist deploy-seitig nicht aktiv ohne Playwright)

---

## 5) Fake-/Stub Features (Zusammenfassung)

- Search Provider/AI waren vor Audit stubbed → wurde teilweise repariert.
- `/auth/forgot-password` ist explizit stub (501) → UI muss ehrlich damit umgehen.
- `D:\ShadowSeek\models.py` wirkt wie Legacy/Dummy → cleanup empfohlen.

