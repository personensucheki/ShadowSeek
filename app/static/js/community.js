document.addEventListener("DOMContentLoaded", () => {
    const unreadBadge = document.getElementById("navbar-messages-unread");
    if (!unreadBadge) {
        return;
    }

    fetch("/api/messages/unread", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Unread count failed");
            }
            return response.json();
        })
        .then((payload) => {
            const unreadCount = Number(payload.unread_count || 0);
            if (unreadCount > 0) {
                unreadBadge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
                unreadBadge.hidden = false;
            }
        })
        .catch(() => {
            unreadBadge.hidden = true;
        });
});
