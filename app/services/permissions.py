from __future__ import annotations

"""
ShadowSeek Feature-Gating (Plan -> Features)

Ziel: Zentraler Ort, der entscheidet, ob ein User ein Feature nutzen darf.
Dieses Modul ist bewusst unabhängig von UI/Frontend und wird serverseitig
in Guards/Decorators und API-Endpunkten verwendet.
"""

from dataclasses import dataclass

from app.models.user import User


FEATURE_HOME = "home"
FEATURE_MEMBERS = "members"
FEATURE_LIVE = "live"
FEATURE_MEINE_SUCHE = "meine_suche"
FEATURE_PULSE = "pulse"
FEATURE_PLATFORM_INSTAGRAM = "platform.instagram"
FEATURE_PLATFORM_TIKTOK = "platform.tiktok"
FEATURE_PLATFORM_SOCIAL_ALL = "platform.social_all"
FEATURE_PLATFORM_DATING_CHAT_ALL = "platform.dating_chat_all"
FEATURE_FULL_ACCESS = "full_access"

ALL_FEATURES: tuple[str, ...] = (
    FEATURE_HOME,
    FEATURE_MEMBERS,
    FEATURE_LIVE,
    FEATURE_MEINE_SUCHE,
    FEATURE_PULSE,
    FEATURE_PLATFORM_INSTAGRAM,
    FEATURE_PLATFORM_TIKTOK,
    FEATURE_PLATFORM_SOCIAL_ALL,
    FEATURE_PLATFORM_DATING_CHAT_ALL,
    FEATURE_FULL_ACCESS,
)


PLAN_REGISTERED = "registered"
PLAN_ABO_1 = "abo_1"
PLAN_ABO_2 = "abo_2"
PLAN_ABO_3 = "abo_3"
PLAN_ABO_4 = "abo_4"


PLAN_FEATURES: dict[str, set[str]] = {
    PLAN_REGISTERED: {FEATURE_HOME, FEATURE_MEMBERS, FEATURE_LIVE},
    PLAN_ABO_1: {
        FEATURE_HOME,
        FEATURE_MEMBERS,
        FEATURE_LIVE,
        FEATURE_PLATFORM_INSTAGRAM,
        FEATURE_PLATFORM_TIKTOK,
    },
    PLAN_ABO_2: {
        FEATURE_HOME,
        FEATURE_MEMBERS,
        FEATURE_LIVE,
        FEATURE_MEINE_SUCHE,
        FEATURE_PLATFORM_INSTAGRAM,
        FEATURE_PLATFORM_TIKTOK,
        FEATURE_PLATFORM_SOCIAL_ALL,
    },
    PLAN_ABO_3: {
        FEATURE_HOME,
        FEATURE_MEMBERS,
        FEATURE_LIVE,
        FEATURE_MEINE_SUCHE,
        FEATURE_PULSE,
        FEATURE_PLATFORM_INSTAGRAM,
        FEATURE_PLATFORM_TIKTOK,
        FEATURE_PLATFORM_SOCIAL_ALL,
        FEATURE_PLATFORM_DATING_CHAT_ALL,
    },
    PLAN_ABO_4: {FEATURE_FULL_ACCESS},
}


SUBSCRIPTION_ACTIVE_STATUSES = {"active", "trialing"}


@dataclass(frozen=True)
class PermissionSnapshot:
    """
    Serialisierbarer Snapshot der Features für den aktuellen Request/User.
    """

    plan_code: str
    subscription_active: bool
    features: tuple[str, ...]

    def has(self, feature: str) -> bool:
        if FEATURE_FULL_ACCESS in self.features:
            return True
        return feature in self.features

    def has_any(self, *features: str) -> bool:
        if FEATURE_FULL_ACCESS in self.features:
            return True
        return any(feature in self.features for feature in features)


def _is_subscription_active(user: User | None) -> bool:
    return bool(user and user.subscription_status in SUBSCRIPTION_ACTIVE_STATUSES and user.plan_code)


def resolve_effective_plan_code(user: User | None) -> str:
    """
    Liefert einen internen Plan-Code.
    - Ohne aktives Abo: registered
    - Mit aktivem Abo: user.plan_code (abo_1..abo_4)
    """

    if not user:
        return PLAN_REGISTERED
    if not _is_subscription_active(user):
        return PLAN_REGISTERED
    return (user.plan_code or PLAN_REGISTERED).strip().lower()


def get_permission_snapshot(user: User | None) -> PermissionSnapshot:
    effective_plan = resolve_effective_plan_code(user)
    plan_features = PLAN_FEATURES.get(effective_plan) or PLAN_FEATURES[PLAN_REGISTERED]
    snapshot = PermissionSnapshot(
        plan_code=effective_plan,
        subscription_active=_is_subscription_active(user),
        features=tuple(sorted(plan_features)),
    )
    return snapshot


def has_permission(user: User | None, feature: str) -> bool:
    """
    Kernfunktion wie gefordert: has_permission(user, feature).
    Diese Funktion bewertet nur den User-Plan (serverseitig), nicht UI-State.
    """

    snapshot = get_permission_snapshot(user)
    return snapshot.has(feature)


def has_any_permission(user: User | None, *features: str) -> bool:
    snapshot = get_permission_snapshot(user)
    return snapshot.has_any(*features)

