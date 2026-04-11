# app/rbac.py
"""
Rollen- und Berechtigungssystem (RBAC) für ShadowSeek
"""

ROLES = [
    "super_admin",
    "admin",
    "analyst",
    "moderator",
    "support",
    "billing_manager",
    "user",
    "guest",
]

PERMISSIONS = [
    "manage_users",
    "manage_roles",
    "view_system_logs",
    "view_search_logs",
    "view_all_saved_queries",
    "manage_settings",
    "manage_integrations",
    "use_search",
    "use_deepsearch",
    "use_chatbot",
    "export_results",
    "manage_billing",
    "view_health",
    "manage_feature_flags",
]

ROLE_PERMISSIONS = {
    "super_admin": set(PERMISSIONS),
    "admin": {
        "manage_users", "manage_roles", "view_system_logs", "view_search_logs", "view_all_saved_queries",
        "manage_settings", "manage_integrations", "use_search", "use_deepsearch", "use_chatbot", "export_results",
        "view_health"
    },
    "analyst": {
        "use_search", "use_deepsearch", "use_chatbot", "export_results", "view_all_saved_queries"
    },
    "moderator": {
        "use_search", "use_chatbot", "view_search_logs"
    },
    "support": {
        "view_search_logs", "use_search", "use_chatbot"
    },
    "billing_manager": {
        "manage_billing"
    },
    "user": {
        "use_search", "use_chatbot"
    },
    "guest": set(),
}

def role_has_permission(role: str, permission: str) -> bool:
    """Prüft, ob eine Rolle eine bestimmte Permission hat."""
    return permission in ROLE_PERMISSIONS.get(role, set())

# Hilfsfunktion für Templates/Frontend

def get_permissions_for_role(role: str):
    return list(ROLE_PERMISSIONS.get(role, set()))

# Beispiel:
# role_has_permission('admin', 'manage_users')  # True
# get_permissions_for_role('analyst')
