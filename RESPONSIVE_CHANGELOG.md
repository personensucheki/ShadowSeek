# ShadowSeek Responsive & Layout-Überarbeitung (April 2026)

## Geänderte CSS-Dateien
- app/static/css/base.css
- app/static/css/pulse.css
- app/static/css/search.css
- app/static/css/home.css

## Geänderte Templates
- app/templates/base.html (Meta-Viewport)
- app/templates/components/navbar.html (Hamburger, Struktur)

## Eingeführte/optimierte Breakpoints
- 1280px, 1180px, 1024px, 900px, 880px, 768px, 700px, 600px, 480px, 390px

## Kritische Responsive-Probleme behoben
- Kein globaler horizontaler Overflow mehr
- Navbar mit Hamburger-Menü, Touch-Flächen
- Panels, Cards, KPI-Grids brechen sauber um
- Timeline/Charts mobil klar begrenzt
- Formulare, Inputs, Buttons überall touchfreundlich
- Typografie und Abstände skalieren über Viewports
- Tabellen und Listen umbrechen Inhalte, keine Scrollbar
- Keine festen Breiten/Höhen, alles fluid
- Cyberpunk-Look bleibt erhalten (Neon, Glow, Dark)

## Getestete Viewports
- 320 × 568, 360 × 800, 390 × 844, 412 × 915, 768 × 1024, 1280+ Desktop

## Hinweise
- Alle Kernseiten (Home, Search, Pulse, Dashboard, Auth) sind jetzt auf Mobile, Tablet und Desktop sauber nutzbar.
- Bei weiteren UI-Fehlern bitte Screenshot und Viewport melden – Nachbesserung jederzeit möglich.

---

**Letztes Update:** 12.04.2026

# Config & Security Refactor (Mai 2024)

## Config Structure
- Split config into `DevelopmentConfig`, `ProductionConfig`, `TestingConfig` (all inherit from `BaseConfig`)
- Hardened session and security settings (cookie flags, CSRF, session lifetime)
- Centralized upload directory and `MAX_CONTENT_LENGTH` enforcement
- All config values are environment-driven, with safe defaults

## Upload Security
- Only allows uploads to a dedicated directory (`UPLOAD_DIRECTORY`)
- Enforces `MAX_CONTENT_LENGTH` for all uploads
- Only allows image extensions: PNG, JPG, JPEG, WEBP, GIF
- Uses `secure_filename` for all uploaded files

## API Response Standardization
- All API endpoints now use `api_success` and `api_error` from `app/services/response_utils.py`
- Ensures consistent JSON structure for success/error

## Smoke Tests
- Added `tests/test_factory_smoke.py`, `tests/test_auth_smoke.py`, `tests/test_api_smoke.py`
- Validate app factory, blueprint registration, auth, and basic API routes

## Migration Notes
- Remove legacy `DevConfig`, `ProdConfig`, `TestConfig` usage; use new class names
- All config and upload security logic is now centralized and testable
- No breaking changes for existing deployments (env vars and instance folder respected)
