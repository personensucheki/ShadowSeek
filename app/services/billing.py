from __future__ import annotations

from datetime import datetime, timezone

from flask import current_app

try:
    import stripe
except ModuleNotFoundError:  # pragma: no cover - depends on optional local dependency
    stripe = None

from app.extensions.main import db
from app.models import ProcessedWebhookEvent, User
from app.services.search_service import PLATFORM_INDEX
from app.services.permissions import (
    FEATURE_FULL_ACCESS,
    FEATURE_PLATFORM_DATING_CHAT_ALL,
    FEATURE_PLATFORM_INSTAGRAM,
    FEATURE_PLATFORM_SOCIAL_ALL,
    FEATURE_PLATFORM_TIKTOK,
    get_permission_snapshot,
)


SUBSCRIPTION_ACTIVE_STATUSES = {"active", "trialing"}
ALL_SEARCH_PLATFORMS = tuple(sorted(PLATFORM_INDEX.keys()))
SOCIAL_ALL_CATEGORIES = {"social", "gaming", "forums"}
DATING_CHAT_CATEGORIES = {"dating", "adult", "porn", "cam"}

PLAN_DEFINITIONS = {
    "abo_1": {
        "code": "abo_1",
        "name": "ShadowSeek Abo 1",
        "amount_eur": 1.99,
        "price_id_env": "STRIPE_PRICE_ID_ABO_1",
        "buy_link_env": "STRIPE_BUY_LINK_ABO_1",
        "ui_modules": ("search",),
        "enabled_platforms": ("instagram", "tiktok"),
        "deepsearch_allowed": False,
    },
    "abo_2": {
        "code": "abo_2",
        "name": "ShadowSeek Abo 2",
        "amount_eur": 3.99,
        "price_id_env": "STRIPE_PRICE_ID_ABO_2",
        "buy_link_env": "STRIPE_BUY_LINK_ABO_2",
        "ui_modules": ("search", "pulse"),
        "enabled_platforms": ALL_SEARCH_PLATFORMS,
        "deepsearch_allowed": False,
    },
    "abo_3": {
        "code": "abo_3",
        "name": "ShadowSeek Abo 3",
        "amount_eur": 6.50,
        "price_id_env": "STRIPE_PRICE_ID_ABO_3",
        "buy_link_env": "STRIPE_BUY_LINK_ABO_3",
        "ui_modules": ("search", "pulse"),
        "enabled_platforms": ALL_SEARCH_PLATFORMS,
        "deepsearch_allowed": False,
    },
    "abo_4": {
        "code": "abo_4",
        "name": "ShadowSeek Abo 4",
        "amount_eur": 9.99,
        "price_id_env": "STRIPE_PRICE_ID_ABO_4",
        "buy_link_env": "STRIPE_BUY_LINK_ABO_4",
        "ui_modules": ("search", "pulse", "deepsearch"),
        "enabled_platforms": ALL_SEARCH_PLATFORMS,
        "deepsearch_allowed": True,
    },
}

DEFAULT_BUY_LINKS = {
    "abo_1": "https://buy.stripe.com/8x26oJbgkeTNeFA00p3cc00",
    "abo_2": "https://buy.stripe.com/6oUeVffwAh1V694bJ73cc01",
    "abo_3": "https://buy.stripe.com/dRmfZj3NS5jd2WS7sR3cc02",
    "abo_4": "https://buy.stripe.com/aFa9AVbgkdPJgNI28x3cc03",
}

# Feste Price-IDs (wie im Projekt angelegt). Werden zusätzlich zu .env/config gemappt,
# damit Webhooks auch dann sauber auf Plan-Codes auflösen, wenn Config noch leer ist.
DEFAULT_PRICE_ID_TO_PLAN = {
    "price_1TLIGpQOOkzbRZU4sLvRJF6t": "abo_1",
    "price_1TLILBQOOkzbRZU4RwLyMT05": "abo_2",
    "price_1TLILMQOOkzbRZU4722usbdC": "abo_3",
    "price_1TLILbQOOkzbRZU4i4ZZkaEv": "abo_4",
}


def build_configured_plans(config):
    plans = {}
    for code, plan in PLAN_DEFINITIONS.items():
        buy_link = (config.get(plan["buy_link_env"]) or DEFAULT_BUY_LINKS.get(code) or "").strip()
        plans[code] = {
            **plan,
            "price_id": config.get(plan["price_id_env"]) or "",
            "buy_link": buy_link,
        }
    return plans


def get_configured_plans():
    return build_configured_plans(current_app.config)


def billing_enabled() -> bool:
    configured = current_app.config.get("BILLING_GATING_ENABLED")
    if configured is not None:
        return bool(configured)
    return bool(current_app.config.get("STRIPE_SECRET_KEY"))


def stripe_configured() -> bool:
    return bool(stripe) and bool(current_app.config.get("STRIPE_SECRET_KEY"))


def require_stripe():
    if stripe is None:
        raise RuntimeError(
            "Stripe SDK ist nicht installiert. Installiere die Abhaengigkeit 'stripe' oder deaktiviere Billing-Gating."
        )


def init_stripe():
    require_stripe()
    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY") or ""
    stripe.api_version = current_app.config.get("STRIPE_API_VERSION") or stripe.api_version


def utc_now():
    return datetime.now(timezone.utc)


def is_subscription_active(user: User | None) -> bool:
    return bool(user and user.subscription_status in SUBSCRIPTION_ACTIVE_STATUSES and user.plan_code)


def get_plan_entitlements(plan_code: str | None):
    plan = get_configured_plans().get(plan_code or "")
    return {
        "plan_code": plan["code"] if plan else None,
        "plan_name": plan["name"] if plan else None,
    }


def _enabled_platforms_for_snapshot(snapshot):
    if snapshot.has(FEATURE_FULL_ACCESS):
        return list(ALL_SEARCH_PLATFORMS)

    enabled = set()
    if snapshot.has(FEATURE_PLATFORM_INSTAGRAM):
        enabled.add("instagram")
    if snapshot.has(FEATURE_PLATFORM_TIKTOK):
        enabled.add("tiktok")

    if snapshot.has(FEATURE_PLATFORM_SOCIAL_ALL):
        for slug, platform in PLATFORM_INDEX.items():
            if platform.category in SOCIAL_ALL_CATEGORIES:
                enabled.add(slug)

    if snapshot.has(FEATURE_PLATFORM_DATING_CHAT_ALL):
        for slug, platform in PLATFORM_INDEX.items():
            if platform.category in DATING_CHAT_CATEGORIES:
                enabled.add(slug)

    return sorted(enabled)


def get_user_entitlements(user: User | None):
    if not billing_enabled():
        return {
            "plan_code": "local-open",
            "plan_name": "Local Open Access",
            "enabled_platforms": list(ALL_SEARCH_PLATFORMS),
            "features": ["full_access"],
            "billing_enabled": False,
            "access_enabled": True,
        }

    snapshot = get_permission_snapshot(user)
    entitlements = {
        **get_plan_entitlements(user.plan_code if user else None),
        "plan_code_effective": snapshot.plan_code,
        "subscription_active": snapshot.subscription_active,
        "features": list(snapshot.features),
        "enabled_platforms": _enabled_platforms_for_snapshot(snapshot),
        "billing_enabled": True,
        "access_enabled": True,
    }
    return entitlements


def serialize_user_subscription(user: User | None):
    if not user:
        return {
            "logged_in": False,
            "plan_code": None,
            "subscription_status": None,
            "subscription_period_end": None,
        }

    return {
        "logged_in": True,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "plan_code": user.plan_code,
        "subscription_status": user.subscription_status,
        "subscription_period_end": user.subscription_period_end.isoformat()
        if user.subscription_period_end
        else None,
        "stripe_customer_id": user.stripe_customer_id,
    }


def get_or_create_customer(user: User):
    init_stripe()
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id), "username": user.username},
    )
    user.stripe_customer_id = customer["id"]
    db.session.commit()
    return user.stripe_customer_id


def create_checkout_session(user: User, plan_code: str):
    plans = get_configured_plans()
    plan = plans.get(plan_code)
    if not plan:
        raise ValueError("Invalid plan selected.")
    if not plan["price_id"]:
        raise ValueError(f"Missing Stripe price for {plan_code}.")

    init_stripe()
    customer_id = get_or_create_customer(user)
    app_base_url = current_app.config["APP_BASE_URL"].rstrip("/")
    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        client_reference_id=str(user.id),
        line_items=[{"price": plan["price_id"], "quantity": 1}],
        success_url=f"{app_base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app_base_url}/billing/cancel",
        metadata={"user_id": str(user.id), "plan_code": plan_code},
        subscription_data={
            "metadata": {
                "user_id": str(user.id),
                "plan_code": plan_code,
            }
        },
        allow_promotion_codes=True,
    )
    return checkout_session


def create_portal_session(user: User):
    if not user.stripe_customer_id:
        raise ValueError("No Stripe customer found for this account.")

    init_stripe()
    app_base_url = current_app.config["APP_BASE_URL"].rstrip("/")
    return stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{app_base_url}/billing/account",
    )


def mark_event_processed(event_id: str, event_type: str) -> bool:
    existing = ProcessedWebhookEvent.query.filter_by(event_id=event_id).first()
    if existing:
        return False

    db.session.add(ProcessedWebhookEvent(event_id=event_id, event_type=event_type))
    db.session.commit()
    return True


def _sync_user_subscription(
    user: User,
    *,
    stripe_customer_id: str | None,
    stripe_subscription_id: str | None,
    plan_code: str | None,
    status: str | None,
    current_period_end: datetime | None,
):
    user.stripe_customer_id = stripe_customer_id or user.stripe_customer_id
    user.stripe_subscription_id = stripe_subscription_id or user.stripe_subscription_id
    user.plan_code = plan_code or user.plan_code
    user.subscription_status = status or user.subscription_status
    user.subscription_period_end = current_period_end
    db.session.commit()


def _find_user_for_subscription(subscription):
    customer_id = subscription.get("customer")
    subscription_id = subscription.get("id")
    metadata = subscription.get("metadata") or {}
    user_id = metadata.get("user_id")

    user = None
    from app.extensions.main import db
    if user_id:
        user = db.session.get(User, int(user_id))
    if not user and subscription_id:
        user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
    if not user and customer_id:
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
    return user


def sync_subscription_from_stripe(subscription_id: str):
    init_stripe()
    subscription = stripe.Subscription.retrieve(subscription_id)
    user = _find_user_for_subscription(subscription)
    if not user:
        current_app.logger.warning("Could not match Stripe subscription %s to a user.", subscription_id)
        return

    item_data = subscription.get("items", {}).get("data", [])
    price_id = item_data[0]["price"]["id"] if item_data else None
    plan_code = None
    if price_id:
        plan_code = DEFAULT_PRICE_ID_TO_PLAN.get(price_id)
        if not plan_code:
            for code, plan in get_configured_plans().items():
                if plan["price_id"] == price_id:
                    plan_code = code
                    break

    period_end = subscription.get("current_period_end")
    period_end_dt = (
        datetime.fromtimestamp(period_end, tz=timezone.utc).replace(tzinfo=None)
        if period_end
        else None
    )
    _sync_user_subscription(
        user,
        stripe_customer_id=subscription.get("customer"),
        stripe_subscription_id=subscription.get("id"),
        plan_code=plan_code,
        status=subscription.get("status"),
        current_period_end=period_end_dt,
    )


def handle_checkout_completed(event):
    session_data = event["data"]["object"]
    user_id = session_data.get("client_reference_id") or (session_data.get("metadata") or {}).get("user_id")
    if not user_id:
        return

    from app.extensions.main import db
    user = db.session.get(User, int(user_id))
    if not user:
        return

    if session_data.get("subscription"):
        sync_subscription_from_stripe(session_data["subscription"])


def handle_invoice_paid(event):
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")
    if subscription_id:
        sync_subscription_from_stripe(subscription_id)


def handle_invoice_payment_failed(event):
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return

    user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
    if user:
        user.subscription_status = "past_due"
        db.session.commit()


def handle_subscription_updated(event):
    subscription = event["data"]["object"]
    if subscription.get("id"):
        sync_subscription_from_stripe(subscription["id"])


def handle_subscription_deleted(event):
    subscription = event["data"]["object"]
    user = _find_user_for_subscription(subscription)
    if not user:
        return

    user.subscription_status = "canceled"
    user.plan_code = None
    user.stripe_subscription_id = None
    user.subscription_period_end = None
    db.session.commit()


WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
}


def process_webhook(payload: bytes, signature: str):
    init_stripe()
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise ValueError("Missing STRIPE_WEBHOOK_SECRET configuration.")

    event = stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=secret,
    )
    event_id = event.get("id")
    event_type = event.get("type", "unknown")
    if event_id and not mark_event_processed(event_id, event_type):
        return {"duplicate": True, "event_type": event_type}

    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler:
        handler(event)

    return {"duplicate": False, "event_type": event_type}
