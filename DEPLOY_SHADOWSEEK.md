#
# External Database & Credential Hygiene
#
- Render Connect liefert die vollständige External Database URL (inkl. User, Passwort, Host, DB).
- Diese URL muss exakt in `.env` als `DATABASE_URL` gesetzt werden (nur lokal/serverseitig, niemals ins Repo/Frontend/Chat).
- Nach jedem Leak (z.B. versehentliche Veröffentlichung, Chat, Screenshot) **muss** das DB-Passwort/Secret rotiert werden.
- Nach Rotation alte Zugangsdaten sofort deaktivieren.

# ShadowSeek Deploy Guide

## Render service

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app`
- Health path: `/health`

## Required environment variables

- `SECRET_KEY`
- `DATABASE_URL`
- `PUBLIC_BASE_URL`
- `APP_BASE_URL`
- `UPLOAD_DIRECTORY=/data/uploads`
- `BILLING_GATING_ENABLED=true`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_ABO_1`
- `STRIPE_PRICE_ID_ABO_2`
- `STRIPE_PRICE_ID_ABO_3`
- `STRIPE_PRICE_ID_ABO_4`

## Optional integrations

- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Stripe webhook

- Endpoint: `https://<your-domain>/api/stripe/webhook`
- Events:
  - `checkout.session.completed`
  - `invoice.paid`
  - `invoice.payment_failed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`

## Deploy order

1. Set all Render environment variables.
2. Attach a Render Persistent Disk mounted at `/data`.
3. Run database migrations with `flask db upgrade`.
4. Deploy the web service.
5. Configure the Stripe webhook endpoint.
6. Test checkout, portal return, webhook sync, and gated search access.

## Media persistence

- Profile avatars and banners are expected under `UPLOAD_DIRECTORY`, which should point to `/data/uploads` on Render.
- Without a mounted persistent disk, uploaded files will disappear after restart or redeploy.
- Existing legacy paths under `app/static/img/...` remain readable, but new uploads should go to the persistent disk.

## Security note

- Rotate any Stripe keys that were exposed in screenshots or chat.
- Never commit live secrets into the repository.
