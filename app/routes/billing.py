from __future__ import annotations

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from app.models import User
from app.services.billing import (
    billing_enabled,
    create_checkout_session,
    create_portal_session,
    get_configured_plans,
    get_user_entitlements,
    process_webhook,
    serialize_user_subscription,
    stripe_configured,
)


billing_bp = Blueprint("billing", __name__)


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def _json_unauthorized():
    return jsonify({"success": False, "error": "Bitte zuerst anmelden."}), 401


@billing_bp.route("/billing")
def billing_page():
    user = _current_user()
    plans = get_configured_plans()
    return render_template(
        "subscription.html",
        plans=plans,
        current_subscription=serialize_user_subscription(user),
        billing_enabled=billing_enabled(),
        stripe_ready=stripe_configured(),
    )


@billing_bp.route("/api/billing/plans", methods=["GET"])
def billing_plans():
    return jsonify(
        {
            "success": True,
            "billing_enabled": billing_enabled(),
            "stripe_ready": stripe_configured(),
            "plans": list(get_configured_plans().values()),
        }
    )


@billing_bp.route("/api/billing/status", methods=["GET"])
def billing_status():
    user = _current_user()
    return jsonify(
        {
            "success": True,
            "billing_enabled": billing_enabled(),
            "subscription": serialize_user_subscription(user),
            "entitlements": get_user_entitlements(user),
        }
    )


@billing_bp.route("/api/entitlements/current", methods=["GET"])
def current_entitlements():
    user = _current_user()
    return jsonify(
        {
            "success": True,
            "billing_enabled": billing_enabled(),
            "subscription": serialize_user_subscription(user),
            "entitlements": get_user_entitlements(user),
        }
    )


@billing_bp.route("/api/entitlements/<int:user_id>", methods=["GET"])
def entitlements_by_user(user_id: int):
    current_user = _current_user()
    if not current_user:
        return _json_unauthorized()
    if current_user.id != user_id and not current_user.is_admin():
        return jsonify({"success": False, "error": "Nicht erlaubt."}), 403

    user = User.query.get(user_id)
    return jsonify(
        {
            "success": True,
            "billing_enabled": billing_enabled(),
            "subscription": serialize_user_subscription(user),
            "entitlements": get_user_entitlements(user),
        }
    )


@billing_bp.route("/api/billing/create-checkout-session", methods=["POST"])
def create_checkout():
    user = _current_user()
    if not user:
        return _json_unauthorized()
    if not billing_enabled():
        return jsonify({"success": False, "error": "Billing ist nicht aktiviert."}), 409
    if not stripe_configured():
        return jsonify({"success": False, "error": "Stripe ist nicht konfiguriert."}), 500

    data = request.get_json(silent=True) or {}
    plan_code = (data.get("plan_code") or data.get("plan") or "").strip().lower()
    if not plan_code:
        return jsonify({"success": False, "error": "Kein Plan ausgewaehlt."}), 400

    try:
        checkout_session = create_checkout_session(user, plan_code)
        return jsonify(
            {
                "success": True,
                "checkout_url": checkout_session["url"],
                "session_id": checkout_session["id"],
            }
        )
    except Exception as exc:
        current_app.logger.exception("Stripe checkout session creation failed.")
        return jsonify({"success": False, "error": str(exc)}), 500


@billing_bp.route("/api/billing/create-portal-session", methods=["POST"])
def create_portal():
    user = _current_user()
    if not user:
        return _json_unauthorized()
    if not billing_enabled():
        return jsonify({"success": False, "error": "Billing ist nicht aktiviert."}), 409
    if not stripe_configured():
        return jsonify({"success": False, "error": "Stripe ist nicht konfiguriert."}), 500

    try:
        portal_session = create_portal_session(user)
        return jsonify({"success": True, "portal_url": portal_session["url"]})
    except Exception as exc:
        current_app.logger.exception("Stripe portal session creation failed.")
        return jsonify({"success": False, "error": str(exc)}), 500


@billing_bp.route("/api/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if not billing_enabled():
        return jsonify({"success": False, "error": "Billing ist nicht aktiviert."}), 409
    if not stripe_configured():
        return jsonify({"success": False, "error": "Stripe ist nicht konfiguriert."}), 500

    signature = request.headers.get("Stripe-Signature", "")
    try:
        result = process_webhook(request.get_data(), signature)
        return jsonify({"success": True, **result})
    except Exception as exc:
        current_app.logger.exception("Stripe webhook processing failed.")
        return jsonify({"success": False, "error": str(exc)}), 400


@billing_bp.route("/billing/success", methods=["GET"])
def billing_success():
    return redirect(url_for("billing.billing_page", checkout="success"))


@billing_bp.route("/billing/cancel", methods=["GET"])
def billing_cancel():
    return redirect(url_for("billing.billing_page", checkout="cancel"))


@billing_bp.route("/billing/account", methods=["GET"])
def billing_account():
    return redirect(url_for("billing.billing_page", portal="return"))
