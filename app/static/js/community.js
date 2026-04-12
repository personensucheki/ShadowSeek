document.addEventListener("DOMContentLoaded", () => {
    // Unread badge logic
    const unreadBadge = document.getElementById("navbar-messages-unread");
    if (unreadBadge) {
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
    }

    // Profilnavigation für Mitglieder
    function handleProfileNavigation(e) {
        const profileUrl = this.getAttribute("data-profile-url");
        if (profileUrl) {
            window.location.assign(profileUrl);
        }
    }
    document.querySelectorAll(".member-avatar-button, .member-name-button, .member-profile-button").forEach((el) => {
        el.addEventListener("click", handleProfileNavigation);
    });
});
