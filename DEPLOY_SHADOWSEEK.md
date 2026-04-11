# ShadowSeek – Start & Deploy Anleitung (Stand: 2026-04-12)

## 1. Voraussetzungen
- Python 3.10+
- pip, venv
- Stripe-Account (API Keys)
- SQLite (oder kompatible DB)

## 2. Setup

```bash
# Repository klonen
# cd ShadowSeek
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# .env anlegen (siehe .env.example)
# STRIPE_SECRET_KEY=...
# STRIPE_WEBHOOK_SECRET=...
# APP_BASE_URL=...
# DATABASE_PATH=shadowseek.db

# Datenbank initialisieren
flask db upgrade  # oder: python scripts/show_tables.py

# (Optional) Admin-User anlegen
python scripts/bootstrap_admin.py
```

## 3. Starten (lokal)

```bash
.venv\Scripts\activate
flask run
```

## 4. Stripe Webhook einrichten

- Stripe Dashboard → Developers → Webhooks
- Endpoint: `https://<deine-domain>/api/stripe/webhook`
- Events: checkout.session.completed, invoice.paid, invoice.payment_failed, customer.subscription.updated, customer.subscription.deleted
- STRIPE_WEBHOOK_SECRET in .env eintragen

## 5. Wichtige Pfade
- /admin/subscription – Abo/Upgrade-UI
- /api/billing/* – Billing-API
- /api/search – Feature-Gating aktiv

## 6. Hinweise
- Feature-Gating: UI und API prüfen Entitlements
- Bei Problemen: Logs und SHADOWSEEK_CODE_AUDIT.md konsultieren
- Für Produktion: HTTPS, sichere .env, Stripe-Live-Keys nutzen

---

Siehe auch: SHADOWSEEK_CODE_AUDIT.md, README_SEARCH_TECH.md
