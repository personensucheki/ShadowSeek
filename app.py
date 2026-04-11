# === Billing & Subscription API ===
from flask import session

@app.route("/api/billing/create-checkout-session", methods=["POST"])
def create_checkout_session():
    user_id = session.get("user_id") or request.json.get("user_id")
    plan_code = request.json.get("plan_code")
    if not user_id or not plan_code or plan_code not in PLANS:
        return jsonify({"error": "Ungültige Anfrage oder Plan."}), 400
    price_id = PLANS[plan_code]["price_id"]
    try:
        customer_row = get_customer_record_by_user_id(user_id)
        if customer_row and customer_row["stripe_customer_id"]:
            customer_id = customer_row["stripe_customer_id"]
        else:
            # Stripe Customer anlegen
            user = None
            try:
                from app.models.user import User as SAUser
                user = SAUser.query.get(user_id)
            except Exception:
                pass
            email = user.email if user else None
            customer = stripe.Customer.create(email=email)
            customer_id = customer.id
            upsert_billing_customer(user_id, email, customer_id, None, None, plan_code, "pending", None, None, None, 0)
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{APP_BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_BASE_URL}/billing/cancel",
            allow_promotion_codes=True,
            metadata={"user_id": user_id, "plan_code": plan_code},
        )
        # Session speichern
        upsert_billing_customer(user_id, None, customer_id, None, price_id, plan_code, "pending", None, None, checkout_session.id, 0)
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": f"Stripe-Fehler: {str(e)}"}), 500


@app.route("/api/billing/create-portal-session", methods=["POST"])
def create_portal_session():
    user_id = session.get("user_id") or request.json.get("user_id")
    if not user_id:
        return jsonify({"error": "Nicht eingeloggt."}), 401
    customer_row = get_customer_record_by_user_id(user_id)
    if not customer_row or not customer_row["stripe_customer_id"]:
        return jsonify({"error": "Kein Stripe-Kunde."}), 400
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_row["stripe_customer_id"],
            return_url=f"{APP_BASE_URL}/billing",
        )
        return jsonify({"portal_url": portal_session.url})
    except Exception as e:
        return jsonify({"error": f"Stripe-Fehler: {str(e)}"}), 500


@app.route("/api/billing/status/<user_id>", methods=["GET"])
def billing_status(user_id):
    row = get_customer_record_by_user_id(user_id)
    if not row:
        return jsonify({"active": False, "plan_code": None, "subscription_status": None})
    return jsonify(serialize_billing_row(row))


@app.route("/api/entitlements/<user_id>", methods=["GET"])
def entitlements(user_id):
    row = get_customer_record_by_user_id(user_id)
    if not row:
        return jsonify(get_plan_entitlements(None))
    return jsonify(get_plan_entitlements(row["plan_code"]))


def stripe_webhook():
@app.route("/api/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if request.method != "POST" or not request.content_type.startswith("application/json"):
        return jsonify({"error": "Invalid method or content type"}), 400
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        print(f"[Stripe Webhook] Signature error: {e}")
        return jsonify({"error": f"Webhook-Signatur ungültig: {str(e)}"}), 400
    except Exception as e:
        print(f"[Stripe Webhook] General error: {e}")
        return jsonify({"error": f"Webhook-Fehler: {str(e)}"}), 400
    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        return jsonify({"error": "Fehlende Event-Daten"}), 400
    db = get_db()
    # Idempotenz: Event nur einmal verarbeiten
    if db.execute("SELECT 1 FROM processed_webhook_events WHERE event_id = ?", (event_id,)).fetchone():
        return jsonify({"status": "already_processed"})
    try:
        if event_type == "checkout.session.completed":
            session_obj = event["data"]["object"]
            user_id = session_obj["metadata"].get("user_id")
            plan_code = session_obj["metadata"].get("plan_code")
            customer_id = session_obj["customer"]
            subscription_id = session_obj["subscription"]
            price = None
            if "display_items" in session_obj and session_obj["display_items"]:
                price = session_obj["display_items"][0].get("price")
            upsert_billing_customer(user_id, None, customer_id, subscription_id, price, plan_code, "active", None, None, session_obj["id"], 1)
        elif event_type == "invoice.paid":
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            db.execute("UPDATE billing_customers SET subscription_status = ?, latest_invoice_id = ?, updated_at = ? WHERE stripe_subscription_id = ?", ("active", invoice["id"], utc_now_iso(), subscription_id))
            db.commit()
        elif event_type == "invoice.payment_failed":
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            db.execute("UPDATE billing_customers SET subscription_status = ?, latest_invoice_id = ?, updated_at = ? WHERE stripe_subscription_id = ?", ("past_due", invoice["id"], utc_now_iso(), subscription_id))
            db.commit()
        elif event_type == "customer.subscription.updated":
            sub = event["data"]["object"]
            db.execute("UPDATE billing_customers SET subscription_status = ?, current_period_end = ?, updated_at = ? WHERE stripe_subscription_id = ?", (sub["status"], unix_to_iso(sub["current_period_end"]), utc_now_iso(), sub["id"]))
            db.commit()
        elif event_type == "customer.subscription.deleted":
            sub = event["data"]["object"]
            db.execute("UPDATE billing_customers SET subscription_status = ?, updated_at = ? WHERE stripe_subscription_id = ?", ("canceled", utc_now_iso(), sub["id"]))
            db.commit()
    except Exception as e:
        print(f"[Stripe Webhook] Event-Handling-Fehler: {e}")
        return jsonify({"error": f"Webhook-Event-Fehler: {str(e)}"}), 500
    # Event als verarbeitet markieren
    db.execute("INSERT INTO processed_webhook_events (event_id, event_type, processed_at) VALUES (?, ?, ?)", (event_id, event_type, utc_now_iso()))
    db.commit()
    return jsonify({"status": "processed"})

import os
import re
import sqlite3
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
import stripe
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000").rstrip("/")
DATABASE_PATH = os.getenv("DATABASE_PATH", "shadowseek.db")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
STRIPE_API_VERSION = os.getenv("STRIPE_API_VERSION", "2025-03-31.basil")
CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")

MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
SEARCH_TIMEOUT_SECONDS = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "6.0"))
SEARCH_MAX_WORKERS = int(os.getenv("SEARCH_MAX_WORKERS", "8"))

if not STRIPE_SECRET_KEY:
    raise RuntimeError("Missing STRIPE_SECRET_KEY environment variable")

stripe.api_key = STRIPE_SECRET_KEY
stripe.api_version = STRIPE_API_VERSION

UPLOAD_DIR = Path(UPLOAD_FOLDER)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 ShadowSeek/1.0"
    )
}

PLANS: Dict[str, Dict[str, Any]] = {
    "abo_1": {
        "name": "ShadowSeek Abo 1",
        "price_id": "price_1TLAB1QOOkzbRZU4jSarleNT",
        "amount_eur": 1.99,
        "features": ["home", "username_search", "tiktok", "instagram"],
    },
    "abo_2": {
        "name": "ShadowSeek Abo 2",
        "price_id": "price_1TLABSQOOkzbRZU4BRpP4oWY",
        "amount_eur": 3.99,
        "features": ["home", "pulse", "adult", "all_social_media"],
    },
    "abo_3": {
        "name": "ShadowSeek Abo 3",
        "price_id": "price_1TLAC4QOOkzbRZU4AMWDCQRu",
        "amount_eur": 6.50,
        "features": ["home", "pulse", "adult", "all_social_media", "knuddels", "lovoo", "badoo", "tinder"],
    },
    "abo_4": {
        "name": "ShadowSeek Abo 4",
        "price_id": "price_1TLACdQOOkzbRZU4S7bYMJbn",
        "amount_eur": 9.99,
        "features": ["all_features", "deepsearch", "home", "pulse", "adult", "all_social_media", "knuddels", "lovoo", "badoo", "tinder"],
    },
}
PRICE_TO_PLAN = {config["price_id"]: plan_code for plan_code, config in PLANS.items()}

PLATFORM_CATALOG: Dict[str, Dict[str, Any]] = {
    "tiktok": {
        "display_name": "TikTok",
        "mode": "public_profile",
        "url_template": "https://www.tiktok.com/@{username}",
        "required_any": ["tiktok", "all_social_media"],
        "priority": 100,
    },
    "instagram": {
        "display_name": "Instagram",
        "mode": "public_profile",
        "url_template": "https://www.instagram.com/{username}/",
        "required_any": ["instagram", "all_social_media"],
        "priority": 99,
    },
    "x": {
        "display_name": "X",
        "mode": "public_profile",
        "url_template": "https://x.com/{username}",
        "required_any": ["all_social_media"],
        "priority": 95,
    },
    "youtube": {
        "display_name": "YouTube",
        "mode": "public_profile",
        "url_template": "https://www.youtube.com/@{username}",
        "required_any": ["all_social_media"],
        "priority": 94,
    },
    "twitch": {
        "display_name": "Twitch",
        "mode": "public_profile",
        "url_template": "https://www.twitch.tv/{username}",
        "required_any": ["all_social_media"],
        "priority": 93,
    },
    "onlyfans": {
        "display_name": "OnlyFans",
        "mode": "public_profile",
        "url_template": "https://onlyfans.com/{username}",
        "required_any": ["adult", "all_social_media"],
        "priority": 92,
    },
    "reddit": {
        "display_name": "Reddit",
        "mode": "public_profile",
        "url_template": "https://www.reddit.com/user/{username}",
        "required_any": ["all_social_media"],
        "priority": 91,
    },
    "telegram": {
        "display_name": "Telegram",
        "mode": "public_profile",
        "url_template": "https://t.me/{username}",
        "required_any": ["all_social_media"],
        "priority": 90,
    },
    "knuddels": {
        "display_name": "Knuddels",
        "mode": "search_link",
        "required_any": ["knuddels"],
        "priority": 80,
        "search_templates": ["https://www.google.com/search?q={query}", "https://www.bing.com/search?q={query}"],
        "query_template": 'site:knuddels.de "{username}"',
    },
    "lovoo": {
        "display_name": "Lovoo",
        "mode": "search_link",
        "required_any": ["lovoo"],
        "priority": 79,
        "search_templates": ["https://www.google.com/search?q={query}", "https://www.bing.com/search?q={query}"],
        "query_template": 'site:lovoo.com "{username}"',
    },
    "badoo": {
        "display_name": "Badoo",
        "mode": "search_link",
        "required_any": ["badoo"],
        "priority": 78,
        "search_templates": ["https://www.google.com/search?q={query}", "https://www.bing.com/search?q={query}"],
        "query_template": 'site:badoo.com "{username}"',
    },
    "tinder": {
        "display_name": "Tinder",
        "mode": "search_link",
        "required_any": ["tinder"],
        "priority": 77,
        "search_templates": ["https://www.google.com/search?q={query}", "https://www.bing.com/search?q={query}"],
        "query_template": 'site:tinder.com "{username}"',
    },
}

SUBSCRIPTION_ACTIVE_STATUSES = {"active", "trialing"}


app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE_MB * 1024 * 1024
app.config["PLANS"] = PLANS


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS billing_customers (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                stripe_price_id TEXT,
                plan_code TEXT,
                subscription_status TEXT,
                current_period_end TEXT,
                latest_invoice_id TEXT,
                checkout_session_id TEXT,
                access_enabled INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_customers_customer_id
            ON billing_customers (stripe_customer_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_customers_subscription_id
            ON billing_customers (stripe_subscription_id);

            CREATE TABLE IF NOT EXISTS processed_webhook_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                processed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                deepsearch_requested INTEGER DEFAULT 0,
                active_plan TEXT,
                result_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


@app.before_request
def ensure_db() -> None:
    init_db()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = CORS_ALLOW_ORIGIN
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/<path:_subpath>", methods=["OPTIONS"])
def options_preflight(_subpath: str):
    return ("", 204)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def unix_to_iso(timestamp: Optional[int]) -> Optional[str]:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def bool_to_int(value: bool) -> int:
    return 1 if value else 0


def json_error(message: str, status_code: int = 400, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    response = jsonify(payload)
    response.status_code = status_code
    return response


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


def normalize_text(value: Optional[str]) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    value = (
        value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        .replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return value


def slug_token(value: Optional[str], keep_separators: bool = False) -> str:
    value = normalize_text(value).lower()
    if keep_separators:
        value = re.sub(r"[^a-z0-9._-]+", "", value)
    else:
        value = re.sub(r"[^a-z0-9]+", "", value)
    return value.strip("._-")


def unique_keep_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in values:
        item = item.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def allowed_image(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(file_storage) -> Optional[Dict[str, str]]:
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image(file_storage.filename):
        raise BadRequest("Unsupported image type. Allowed: jpg, jpeg, png, webp, gif")
    safe_name = secure_filename(file_storage.filename)
    ext = safe_name.rsplit(".", 1)[1].lower()
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    target_path = UPLOAD_DIR / saved_name
    file_storage.save(target_path)
    hosted_url = f"{APP_BASE_URL}/uploads/{saved_name}"
    return {"filename": saved_name, "hosted_url": hosted_url, "local_path": str(target_path)}


def get_customer_record_by_user_id(user_id: str) -> Optional[sqlite3.Row]:
    with closing(get_db()) as conn:
        return conn.execute("SELECT * FROM billing_customers WHERE user_id = ?", (user_id,)).fetchone()


def get_customer_record_by_customer_id(customer_id: str) -> Optional[sqlite3.Row]:
    with closing(get_db()) as conn:
        return conn.execute("SELECT * FROM billing_customers WHERE stripe_customer_id = ?", (customer_id,)).fetchone()


def get_customer_record_by_subscription_id(subscription_id: str) -> Optional[sqlite3.Row]:
    with closing(get_db()) as conn:
        return conn.execute("SELECT * FROM billing_customers WHERE stripe_subscription_id = ?", (subscription_id,)).fetchone()


def upsert_billing_customer(
    *,
    user_id: str,
    email: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    stripe_price_id: Optional[str] = None,
    plan_code: Optional[str] = None,
    subscription_status: Optional[str] = None,
    current_period_end: Optional[str] = None,
    latest_invoice_id: Optional[str] = None,
    checkout_session_id: Optional[str] = None,
    access_enabled: Optional[bool] = None,
) -> None:
    now = utc_now_iso()
    existing = get_customer_record_by_user_id(user_id)
    payload = {
        "email": email if email is not None else (existing["email"] if existing else None),
        "stripe_customer_id": stripe_customer_id if stripe_customer_id is not None else (existing["stripe_customer_id"] if existing else None),
        "stripe_subscription_id": stripe_subscription_id if stripe_subscription_id is not None else (existing["stripe_subscription_id"] if existing else None),
        "stripe_price_id": stripe_price_id if stripe_price_id is not None else (existing["stripe_price_id"] if existing else None),
        "plan_code": plan_code if plan_code is not None else (existing["plan_code"] if existing else None),
        "subscription_status": subscription_status if subscription_status is not None else (existing["subscription_status"] if existing else None),
        "current_period_end": current_period_end if current_period_end is not None else (existing["current_period_end"] if existing else None),
        "latest_invoice_id": latest_invoice_id if latest_invoice_id is not None else (existing["latest_invoice_id"] if existing else None),
        "checkout_session_id": checkout_session_id if checkout_session_id is not None else (existing["checkout_session_id"] if existing else None),
        "access_enabled": bool_to_int(access_enabled) if access_enabled is not None else (existing["access_enabled"] if existing else 0),
    }
    with closing(get_db()) as conn:
        conn.execute(
            """
            INSERT INTO billing_customers (
                user_id, email, stripe_customer_id, stripe_subscription_id, stripe_price_id,
                plan_code, subscription_status, current_period_end, latest_invoice_id,
                checkout_session_id, access_enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email = excluded.email,
                stripe_customer_id = excluded.stripe_customer_id,
                stripe_subscription_id = excluded.stripe_subscription_id,
                stripe_price_id = excluded.stripe_price_id,
                plan_code = excluded.plan_code,
                subscription_status = excluded.subscription_status,
                current_period_end = excluded.current_period_end,
                latest_invoice_id = excluded.latest_invoice_id,
                checkout_session_id = excluded.checkout_session_id,
                access_enabled = excluded.access_enabled,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                payload["email"],
                payload["stripe_customer_id"],
                payload["stripe_subscription_id"],
                payload["stripe_price_id"],
                payload["plan_code"],
                payload["subscription_status"],
                payload["current_period_end"],
                payload["latest_invoice_id"],
                payload["checkout_session_id"],
                payload["access_enabled"],
                existing["created_at"] if existing else now,
                now,
            ),
        )
        conn.commit()


def mark_event_processed(event_id: str, event_type: str) -> bool:
    with closing(get_db()) as conn:
        try:
            conn.execute(
                "INSERT INTO processed_webhook_events (event_id, event_type, processed_at) VALUES (?, ?, ?)",
                (event_id, event_type, utc_now_iso()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def log_search(user_id: Optional[str], username: str, deepsearch_requested: bool, active_plan: Optional[str], result_count: int) -> None:
    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO search_logs (user_id, username, deepsearch_requested, active_plan, result_count, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, bool_to_int(deepsearch_requested), active_plan, result_count, utc_now_iso()),
        )
        conn.commit()


def plan_from_price_id(price_id: Optional[str]) -> Optional[str]:
    return PRICE_TO_PLAN.get(price_id) if price_id else None


def extract_subscription_price_id(subscription: Any) -> Optional[str]:
    try:
        items = subscription["items"]["data"]
        return items[0]["price"]["id"] if items else None
    except Exception:
        return None


def is_subscription_access_enabled(status: Optional[str]) -> bool:
    return bool(status and status in SUBSCRIPTION_ACTIVE_STATUSES)


def has_feature(plan_code: Optional[str], feature_name: str) -> bool:
    if not plan_code or plan_code not in PLANS:
        return False
    features = set(PLANS[plan_code]["features"])
    return "all_features" in features or feature_name in features


def is_allowed_by_required_any(plan_code: Optional[str], required_any: Iterable[str]) -> bool:
    if not plan_code or plan_code not in PLANS:
        return False
    features = set(PLANS[plan_code]["features"])
    if "all_features" in features:
        return True
    return any(feature_name in features for feature_name in required_any)


def get_plan_entitlements(plan_code: Optional[str]) -> Dict[str, Any]:
    if not plan_code or plan_code not in PLANS:
        return {
            "plan_code": None,
            "plan_name": None,
            "features": [],
            "enabled_platforms": [],
            "ui_modules": [],
            "deepsearch_allowed": False,
        }
    features = PLANS[plan_code]["features"]
    enabled_platforms = [
        platform_key for platform_key, config in PLATFORM_CATALOG.items()
        if is_allowed_by_required_any(plan_code, config["required_any"])
    ]
    ui_modules = sorted({feature_name for feature_name in features if feature_name in {"home", "pulse", "adult", "deepsearch"}})
    return {
        "plan_code": plan_code,
        "plan_name": PLANS[plan_code]["name"],
        "features": features,
        "enabled_platforms": sorted(enabled_platforms),
        "ui_modules": ui_modules,
        "deepsearch_allowed": has_feature(plan_code, "deepsearch"),
    }


def serialize_billing_row(row: sqlite3.Row) -> Dict[str, Any]:
    entitlements = get_plan_entitlements(row["plan_code"])
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "stripe_customer_id": row["stripe_customer_id"],
        "stripe_subscription_id": row["stripe_subscription_id"],
        "stripe_price_id": row["stripe_price_id"],
        "plan_code": row["plan_code"],
        "plan_name": entitlements["plan_name"],
        "features": entitlements["features"],
        "enabled_platforms": entitlements["enabled_platforms"],
        "ui_modules": entitlements["ui_modules"],
        "subscription_status": row["subscription_status"],
        "current_period_end": row["current_period_end"],
        "latest_invoice_id": row["latest_invoice_id"],
        "access_enabled": bool(row["access_enabled"]),
        "checkout_session_id": row["checkout_session_id"],
        "updated_at": row["updated_at"],
    }


def get_user_plan_context(user_id: Optional[str]) -> Dict[str, Any]:
    if not user_id:
        return {"subscription": None, "entitlements": get_plan_entitlements(None), "access_enabled": False}
    row = get_customer_record_by_user_id(user_id)
    if not row:
        return {"subscription": None, "entitlements": get_plan_entitlements(None), "access_enabled": False}
    subscription = serialize_billing_row(row)
    return {"subscription": subscription, "entitlements": get_plan_entitlements(subscription["plan_code"]), "access_enabled": bool(subscription["access_enabled"])}


def generate_username_variations(
    username: str,
    real_name: Optional[str] = None,
    clan_name: Optional[str] = None,
    age: Optional[str] = None,
    postal_code: Optional[str] = None,
    max_variants: int = 10,
) -> List[str]:
    username_base = slug_token(username, keep_separators=True)
    username_compact = slug_token(username)
    real_name_compact = slug_token(real_name)
    clan_compact = slug_token(clan_name)
    age_digits = re.sub(r"\D+", "", age or "")[:2]
    postal_digits = re.sub(r"\D+", "", postal_code or "")[:5]

    candidates = [username_base, username_compact, username_compact.replace("_", "").replace(".", "").replace("-", "")]
    if username_compact:
        candidates.extend([f"{username_compact}_official", f"{username_compact}.official", f"{username_compact}tv"])
    if real_name_compact:
        candidates.extend([real_name_compact, f"{real_name_compact}_{username_compact}" if username_compact else real_name_compact, f"{username_compact}_{real_name_compact}" if username_compact else real_name_compact])
    if clan_compact and username_compact:
        candidates.extend([f"{clan_compact}_{username_compact}", f"{username_compact}_{clan_compact}"])
    if age_digits and username_compact:
        candidates.extend([f"{username_compact}{age_digits}", f"{username_compact}_{age_digits}"])
    if postal_digits and username_compact:
        candidates.extend([f"{username_compact}{postal_digits}", f"{username_compact}_{postal_digits}"])

    cleaned = []
    for candidate in candidates:
        candidate = re.sub(r"\.\.", ".", candidate.strip("._-"))
        candidate = re.sub(r"__+", "_", candidate)
        candidate = re.sub(r"--+", "-", candidate)
        if len(candidate) >= 2:
            cleaned.append(candidate)
    return unique_keep_order(cleaned)[:max_variants]


def build_reverse_image_links(upload_info: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    if not upload_info:
        return None
    hosted_url = upload_info["hosted_url"]
    encoded_url = quote_plus(hosted_url)
    return {
        "hosted_image_url": hosted_url,
        "google_lens": "https://lens.google.com/upload",
        "google_images_by_url": f"https://www.google.com/searchbyimage?image_url={encoded_url}",
        "tineye": "https://tineye.com/",
        "tineye_by_url": f"https://tineye.com/search?url={encoded_url}",
        "yandex_images": "https://yandex.com/images/",
        "yandex_by_url": f"https://yandex.com/images/search?rpt=imageview&url={encoded_url}",
    }


def build_search_links_for_platform(platform_key: str, username: str) -> List[str]:
    config = PLATFORM_CATALOG[platform_key]
    query = quote_plus(config.get("query_template", '"{username}"').format(username=username))
    return [template.format(query=query) for template in config.get("search_templates", [])]


def probe_public_profile(platform_key: str, username: str) -> Dict[str, Any]:
    config = PLATFORM_CATALOG[platform_key]
    profile_url = config["url_template"].format(username=username)
    result = {
        "platform": platform_key,
        "display_name": config["display_name"],
        "mode": config["mode"],
        "username": username,
        "profile_url": profile_url,
        "match_state": "unknown",
        "http_status": None,
        "reachable": False,
    }
    try:
        response = requests.get(profile_url, headers=DEFAULT_HEADERS, timeout=SEARCH_TIMEOUT_SECONDS, allow_redirects=True)
        result["http_status"] = response.status_code
        result["final_url"] = response.url
        if response.status_code == 200:
            result["match_state"] = "found"
            result["reachable"] = True
        elif response.status_code == 404:
            result["match_state"] = "not_found"
        elif response.status_code in {401, 403, 429}:
            result["match_state"] = "unknown"
            result["note"] = "Request blocked or rate-limited by target platform."
        else:
            result["match_state"] = "unknown"
            result["note"] = f"Unexpected HTTP status {response.status_code}."
    except requests.RequestException as exc:
        result["match_state"] = "unknown"
        result["note"] = f"Network probe failed: {exc.__class__.__name__}"
    return result


def probe_search_link_platform(platform_key: str, username: str) -> Dict[str, Any]:
    config = PLATFORM_CATALOG[platform_key]
    return {
        "platform": platform_key,
        "display_name": config["display_name"],
        "mode": config["mode"],
        "username": username,
        "match_state": "search_link_only",
        "search_links": build_search_links_for_platform(platform_key, username),
        "note": "This platform is exposed through search links because public username profile URLs are not consistently available.",
    }


def perform_platform_checks(allowed_platforms: List[str], username_variations: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    public_jobs: List[Tuple[str, str]] = []
    for platform_key in allowed_platforms:
        config = PLATFORM_CATALOG[platform_key]
        if config["mode"] == "public_profile":
            for username in username_variations:
                public_jobs.append((platform_key, username))
        else:
            results.append(probe_search_link_platform(platform_key, username_variations[0]))

    if public_jobs:
        with ThreadPoolExecutor(max_workers=SEARCH_MAX_WORKERS) as executor:
            future_map = {executor.submit(probe_public_profile, platform_key, username): (platform_key, username) for platform_key, username in public_jobs}
            for future in as_completed(future_map):
                results.append(future.result())
    return results


def deepsearch_rerank(results: List[Dict[str, Any]], username_variations: List[str]) -> List[Dict[str, Any]]:
    variation_rank = {username: index for index, username in enumerate(username_variations)}
    def score(item: Dict[str, Any]) -> Tuple[int, int, int]:
        config = PLATFORM_CATALOG.get(item["platform"], {})
        platform_priority = int(config.get("priority", 0))
        state_bonus = {"found": 1000, "search_link_only": 500, "unknown": 100, "not_found": 0}.get(item.get("match_state", "unknown"), 0)
        username_penalty = variation_rank.get(item.get("username", ""), 999)
        return (state_bonus + platform_priority, -platform_priority, -username_penalty)
    return sorted(results, key=score, reverse=True)


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_results": len(results),
        "found_count": len([item for item in results if item.get("match_state") == "found"]),
        "search_link_count": len([item for item in results if item.get("match_state") == "search_link_only"]),
        "unknown_count": len([item for item in results if item.get("match_state") == "unknown"]),
        "not_found_count": len([item for item in results if item.get("match_state") == "not_found"]),
    }


def require_json() -> Dict[str, Any]:
    if not request.is_json:
        raise BadRequest("Expected application/json request body")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("Invalid JSON body")
    return data


@app.get("/api/health")
def health_check():
    return jsonify({"ok": True, "service": "shadowseek", "billing_enabled": True, "search_enabled": True})


@app.get("/api/billing/plans")
def list_plans():
    return jsonify({
        "ok": True,
        "plans": [{
            "code": plan_code,
            "name": config["name"],
            "amount_eur": config["amount_eur"],
            "currency": "eur",
            "interval": "month",
            "features": config["features"],
            "enabled_platforms": get_plan_entitlements(plan_code)["enabled_platforms"],
        } for plan_code, config in PLANS.items()]
    })


@app.get("/api/billing/status/<user_id>")
def billing_status(user_id: str):
    return jsonify({"ok": True, **get_user_plan_context(user_id)})


@app.get("/api/entitlements/<user_id>")
def entitlements(user_id: str):
    return jsonify({"ok": True, **get_user_plan_context(user_id)})


@app.post("/api/billing/create-checkout-session")
def create_checkout_session():
    data = require_json()
    user_id = str(data.get("user_id", "")).strip()
    email = str(data.get("email", "")).strip() or None
    plan_code = str(data.get("plan", "")).strip().lower()
    if not user_id:
        return json_error("Missing user_id", 400)
    if plan_code not in PLANS:
        return json_error("Invalid plan selected", 400)

    existing = get_customer_record_by_user_id(user_id)
    if existing and existing["access_enabled"] and existing["stripe_subscription_id"]:
        return json_error("User already has an active subscription. Use /api/billing/change-plan or the customer portal.", 409, action="change_plan_required")

    customer_id = existing["stripe_customer_id"] if existing and existing["stripe_customer_id"] else None
    if not customer_id:
        customer = stripe.Customer.create(email=email, metadata={"user_id": user_id, "source": "shadowseek"})
        customer_id = customer["id"]

    plan = PLANS[plan_code]
    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        success_url=f"{APP_BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_BASE_URL}/billing/cancel",
        customer=customer_id,
        client_reference_id=user_id,
        customer_update={"address": "auto", "name": "auto"},
        line_items=[{"price": plan["price_id"], "quantity": 1}],
        allow_promotion_codes=True,
        billing_address_collection="auto",
        metadata={"user_id": user_id, "plan_code": plan_code, "source": "shadowseek_checkout"},
        subscription_data={"metadata": {"user_id": user_id, "plan_code": plan_code, "source": "shadowseek_subscription"}},
    )

    upsert_billing_customer(
        user_id=user_id,
        email=email,
        stripe_customer_id=customer_id,
        stripe_price_id=plan["price_id"],
        plan_code=plan_code,
        checkout_session_id=checkout_session["id"],
        subscription_status=(existing["subscription_status"] if existing else "checkout_created"),
        access_enabled=bool(existing["access_enabled"]) if existing else False,
    )
    return jsonify({"ok": True, "checkout_url": checkout_session["url"], "session_id": checkout_session["id"], "plan": {"code": plan_code, "name": plan["name"], "amount_eur": plan["amount_eur"]}})


@app.post("/api/billing/change-plan")
def change_plan():
    data = require_json()
    user_id = str(data.get("user_id", "")).strip()
    new_plan_code = str(data.get("plan", "")).strip().lower()
    proration_behavior = str(data.get("proration_behavior", "create_prorations")).strip()
    if not user_id:
        return json_error("Missing user_id", 400)
    if new_plan_code not in PLANS:
        return json_error("Invalid target plan", 400)
    if proration_behavior not in {"create_prorations", "none", "always_invoice"}:
        return json_error("Invalid proration_behavior", 400)

    row = get_customer_record_by_user_id(user_id)
    if not row or not row["stripe_subscription_id"]:
        return json_error("No active subscription found for this user", 404)
    if not row["access_enabled"]:
        return json_error("Subscription is not active enough for a plan change", 409)

    if row["plan_code"] == new_plan_code:
        return jsonify({"ok": True, "changed": False, "message": "User already has this plan.", "subscription": serialize_billing_row(row)})

    subscription = stripe.Subscription.retrieve(row["stripe_subscription_id"])
    items = subscription.get("items", {}).get("data", [])
    if not items:
        return json_error("Stripe subscription has no updatable items", 500)

    updated = stripe.Subscription.modify(
        row["stripe_subscription_id"],
        proration_behavior=proration_behavior,
        items=[{"id": items[0]["id"], "price": PLANS[new_plan_code]["price_id"], "quantity": 1}],
        metadata={**(subscription.get("metadata", {}) or {}), "plan_code": new_plan_code},
    )

    upsert_billing_customer(
        user_id=user_id,
        email=row["email"],
        stripe_customer_id=row["stripe_customer_id"],
        stripe_subscription_id=row["stripe_subscription_id"],
        stripe_price_id=PLANS[new_plan_code]["price_id"],
        plan_code=new_plan_code,
        subscription_status=updated.get("status"),
        current_period_end=unix_to_iso(updated.get("current_period_end")),
        latest_invoice_id=updated.get("latest_invoice"),
        access_enabled=is_subscription_access_enabled(updated.get("status")),
    )
    refreshed = get_customer_record_by_user_id(user_id)
    return jsonify({"ok": True, "changed": True, "message": "Subscription plan updated.", "subscription": serialize_billing_row(refreshed) if refreshed else None})


@app.post("/api/billing/create-portal-session")
def create_portal_session():
    data = require_json()
    user_id = str(data.get("user_id", "")).strip()
    if not user_id:
        return json_error("Missing user_id", 400)
    row = get_customer_record_by_user_id(user_id)
    if not row or not row["stripe_customer_id"]:
        return json_error("No Stripe customer found for this user", 404)
    portal_session = stripe.billing_portal.Session.create(customer=row["stripe_customer_id"], return_url=f"{APP_BASE_URL}/billing/account")
    return jsonify({"ok": True, "portal_url": portal_session["url"]})


@app.get("/billing/success")
def billing_success():
    return jsonify({"ok": True, "message": "Checkout finished. Access becomes active after verified Stripe webhook sync.", "session_id": request.args.get("session_id", "")})


@app.get("/billing/cancel")
def billing_cancel():
    return jsonify({"ok": True, "message": "Checkout canceled."})


@app.get("/billing/account")
def billing_account():
    return jsonify({"ok": True, "message": "Returned from Stripe Billing Portal."})


@app.post("/api/search")
def search_profiles():
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        data = request.form.to_dict(flat=True)
        image_file = request.files.get("image")
    else:
        data = require_json()
        image_file = None

    user_id = str(data.get("user_id", "")).strip()
    username = str(data.get("username", "")).strip()
    real_name = str(data.get("real_name", "")).strip() or None
    clan_name = str(data.get("clan_name", "")).strip() or None
    age = str(data.get("age", "")).strip() or None
    postal_code = str(data.get("postal_code", "")).strip() or None
    deepsearch_requested = parse_bool(data.get("deepsearch"))
    explicit_platforms = data.get("platforms")

    if not user_id:
        return json_error("Missing user_id", 400)
    if not username and not image_file:
        return json_error("Provide at least a username or an image upload", 400)

    context = get_user_plan_context(user_id)
    subscription = context["subscription"]
    entitlements = context["entitlements"]
    if not context["access_enabled"]:
        return json_error("No active subscription found for this user.", 403, entitlements=entitlements, billing_status=subscription)

    username_variations = generate_username_variations(username=username or "image_only_search", real_name=real_name, clan_name=clan_name, age=age, postal_code=postal_code)
    if explicit_platforms:
        if isinstance(explicit_platforms, str):
            requested_platforms = [part.strip().lower() for part in explicit_platforms.split(",") if part.strip()]
        elif isinstance(explicit_platforms, list):
            requested_platforms = [str(part).strip().lower() for part in explicit_platforms if str(part).strip()]
        else:
            return json_error("platforms must be a comma-separated string or array", 400)
    else:
        requested_platforms = entitlements["enabled_platforms"]

    requested_platforms = [platform for platform in requested_platforms if platform in PLATFORM_CATALOG]
    allowed_platforms = [platform for platform in requested_platforms if platform in entitlements["enabled_platforms"]]
    denied_platforms = sorted(set(requested_platforms) - set(allowed_platforms))

    upload_info = save_uploaded_image(image_file) if image_file else None
    reverse_image_links = build_reverse_image_links(upload_info)

    results = perform_platform_checks(allowed_platforms, username_variations)
    deepsearch_applied = False
    deepsearch_message = None
    if deepsearch_requested:
        if entitlements["deepsearch_allowed"]:
            results = deepsearch_rerank(results, username_variations)
            deepsearch_applied = True
        else:
            deepsearch_message = "DeepSearch requested but not included in current subscription."

    summary = summarize_results(results)
    log_search(user_id=user_id, username=username or "", deepsearch_requested=deepsearch_requested, active_plan=subscription["plan_code"] if subscription else None, result_count=summary["total_results"])

    return jsonify({
        "ok": True,
        "search": {
            "user_id": user_id,
            "username": username,
            "real_name": real_name,
            "clan_name": clan_name,
            "age": age,
            "postal_code": postal_code,
            "deepsearch_requested": deepsearch_requested,
            "deepsearch_applied": deepsearch_applied,
            "deepsearch_message": deepsearch_message,
        },
        "billing": {
            "plan_code": subscription["plan_code"] if subscription else None,
            "plan_name": subscription["plan_name"] if subscription else None,
            "access_enabled": context["access_enabled"],
        },
        "entitlements": entitlements,
        "username_variations": username_variations,
        "allowed_platforms": allowed_platforms,
        "denied_platforms": denied_platforms,
        "summary": summary,
        "profiles": results,
        "reverse_image_search": reverse_image_links,
    })


@app.get("/api/search/platforms/<user_id>")
def search_platforms(user_id: str):
    context = get_user_plan_context(user_id)
    return jsonify({
        "ok": True,
        "subscription": context["subscription"],
        "entitlements": context["entitlements"],
        "platform_catalog": {key: {"display_name": value["display_name"], "mode": value["mode"], "required_any": value["required_any"]} for key, value in PLATFORM_CATALOG.items()},
    })


@app.get("/uploads/<path:filename>")
def serve_upload(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)


def sync_subscription_from_stripe(subscription_id: str) -> None:
    subscription = stripe.Subscription.retrieve(subscription_id)
    customer_id = subscription.get("customer")
    price_id = extract_subscription_price_id(subscription)
    plan_code = plan_from_price_id(price_id)
    status = subscription.get("status")
    current_period_end = unix_to_iso(subscription.get("current_period_end"))
    latest_invoice_id = subscription.get("latest_invoice")

    row = get_customer_record_by_subscription_id(subscription_id)
    if not row and customer_id:
        row = get_customer_record_by_customer_id(customer_id)

    user_id = row["user_id"] if row else (subscription.get("metadata", {}) or {}).get("user_id")
    if not user_id:
        app.logger.warning("Could not match subscription %s to a local user.", subscription_id)
        return

    upsert_billing_customer(
        user_id=user_id,
        email=row["email"] if row else None,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_price_id=price_id,
        plan_code=plan_code,
        subscription_status=status,
        current_period_end=current_period_end,
        latest_invoice_id=latest_invoice_id,
        access_enabled=is_subscription_access_enabled(status),
    )


def handle_checkout_session_completed(event: Dict[str, Any]) -> None:
    session = event["data"]["object"]
    user_id = session.get("client_reference_id") or (session.get("metadata", {}) or {}).get("user_id")
    if not user_id:
        app.logger.warning("checkout.session.completed received without user_id")
        return
    plan_code = (session.get("metadata", {}) or {}).get("plan_code")
    price_id = PLANS[plan_code]["price_id"] if plan_code in PLANS else None
    upsert_billing_customer(
        user_id=user_id,
        email=(session.get("customer_details", {}) or {}).get("email") or session.get("customer_email"),
        stripe_customer_id=session.get("customer"),
        stripe_subscription_id=session.get("subscription"),
        stripe_price_id=price_id,
        plan_code=plan_code,
        checkout_session_id=session.get("id"),
        subscription_status="checkout_completed",
        access_enabled=False,
    )
    if session.get("subscription"):
        sync_subscription_from_stripe(session["subscription"])


def handle_invoice_paid(event: Dict[str, Any]) -> None:
    subscription_id = event["data"]["object"].get("subscription")
    if subscription_id:
        sync_subscription_from_stripe(subscription_id)


def handle_invoice_payment_failed(event: Dict[str, Any]) -> None:
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return
    row = get_customer_record_by_subscription_id(subscription_id)
    if not row:
        sync_subscription_from_stripe(subscription_id)
        row = get_customer_record_by_subscription_id(subscription_id)
    if not row:
        return
    upsert_billing_customer(
        user_id=row["user_id"],
        email=row["email"],
        stripe_customer_id=row["stripe_customer_id"],
        stripe_subscription_id=subscription_id,
        stripe_price_id=row["stripe_price_id"],
        plan_code=row["plan_code"],
        subscription_status="past_due",
        current_period_end=row["current_period_end"],
        latest_invoice_id=invoice.get("id"),
        access_enabled=False,
    )


def handle_subscription_updated(event: Dict[str, Any]) -> None:
    subscription_id = event["data"]["object"].get("id")
    if subscription_id:
        sync_subscription_from_stripe(subscription_id)


def handle_subscription_deleted(event: Dict[str, Any]) -> None:
    subscription = event["data"]["object"]
    subscription_id = subscription.get("id")
    if not subscription_id:
        return
    row = get_customer_record_by_subscription_id(subscription_id)
    if not row:
        return
    upsert_billing_customer(
        user_id=row["user_id"],
        email=row["email"],
        stripe_customer_id=row["stripe_customer_id"],
        stripe_subscription_id=subscription_id,
        stripe_price_id=row["stripe_price_id"],
        plan_code=row["plan_code"],
        subscription_status="canceled",
        current_period_end=unix_to_iso(subscription.get("ended_at")),
        latest_invoice_id=row["latest_invoice_id"],
        access_enabled=False,
    )


WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_session_completed,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
}


@app.post("/api/stripe/webhook")
def stripe_webhook():
    if not STRIPE_WEBHOOK_SECRET:
        return json_error("Missing STRIPE_WEBHOOK_SECRET configuration", 500)
    payload = request.get_data(as_text=False)
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return json_error("Invalid webhook payload", 400)
    except stripe.error.SignatureVerificationError:
        return json_error("Invalid webhook signature", 400)

    event_id = event.get("id")
    event_type = event.get("type", "unknown")
    if event_id and not mark_event_processed(event_id, event_type):
        return jsonify({"ok": True, "duplicate": True, "event_type": event_type})

    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler:
        try:
            handler(event)
        except Exception as exc:
            app.logger.exception("Webhook handler failed for %s", event_type)
            return json_error(f"Webhook handler error: {exc}", 500)
    return jsonify({"ok": True, "received": True, "event_type": event_type})


@app.errorhandler(BadRequest)
def bad_request_handler(exc: BadRequest):
    return json_error(str(exc.description), 400)


@app.errorhandler(404)
def not_found_handler(_exc):
    return json_error("Endpoint not found", 404)


@app.errorhandler(413)
def payload_too_large_handler(_exc):
    return json_error(f"Uploaded file is too large. Limit is {MAX_IMAGE_SIZE_MB} MB.", 413)


@app.errorhandler(500)
def internal_error_handler(_exc):
    return json_error("Internal server error", 500)


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
