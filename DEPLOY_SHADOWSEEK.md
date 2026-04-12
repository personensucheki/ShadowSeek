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
2. Run database migrations with `flask db upgrade`.
3. Deploy the web service.
4. Configure the Stripe webhook endpoint.
5. Test checkout, portal return, webhook sync, and gated search access.

## Security note

- Rotate any Stripe keys that were exposed in screenshots or chat.
- Never commit live secrets into the repository.
