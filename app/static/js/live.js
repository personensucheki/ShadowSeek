// Live-Studio-Formular: Stream anlegen
document.addEventListener("DOMContentLoaded", () => {
    const setupForm = document.getElementById("live-setup-form");
    if (setupForm) {
        setupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(setupForm);
            const data = {
                title: formData.get("title"),
                description: formData.get("description"),
                category: formData.get("category"),
                game: formData.get("game"),
                tags: formData.get("tags"),
                allow_gifts: formData.get("enable_gifts") ? true : false
            };
            // Thumbnail/Cover wird vorerst nicht per API gesendet
            try {
                const res = await fetch("/api/live/stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                if (result.success) {
                    // Weiterleitung oder Feedback
                    window.location.href = `/live/view/${result.stream_id}`;
                } else {
                    alert(result.error || "Fehler beim Anlegen des Streams.");
                }
            } catch (err) {
                alert("Netzwerkfehler beim Anlegen des Streams.");
            }
        });
    }
});

// --- SocketIO-Integration für Live-Viewer ---
let socket = null;
function initLiveSocket(streamId) {
    if (!window.io || !streamId) return;
    socket = io("/live");
    socket.on("connect", () => {
        socket.emit("join_stream", { stream_id: streamId });
    });
    window.addEventListener("beforeunload", () => {
        socket.emit("leave_stream", { stream_id: streamId });
    });
    // Chat
    socket.on("new_message", data => {
        // Chat-Nachricht im UI anzeigen
        appendLiveChatMessage(data);
    });
    // Like
    socket.on("new_like", data => {
        // Like-Animation/Floating-Heart triggern
        triggerLikeAnimation(data);
    });
    // Gift
    socket.on("new_gift", data => {
        // Geschenk-Animation/UI-Update
        triggerGiftAnimation(data);
    });
    // Viewer Count
    socket.on("viewer_update", data => {
        updateViewerCount(data.viewer_count);
    });
    // Leaderboard
    socket.on("leaderboard_update", data => {
        updateLeaderboard(data.leaderboard);
    });
    // Stream-State
    socket.on("stream_state_update", data => {
        updateStreamState(data.state);
    });
}

// --- Hilfsfunktionen für UI-Update (Platzhalter, implementiere nach Bedarf) ---
function appendLiveChatMessage(data) {
    // ...
}
function triggerLikeAnimation(data) {
    // ...
}
function triggerGiftAnimation(data) {
    // ...
}
function updateViewerCount(count) {
    const el = document.getElementById("viewer-count");
    if (el) el.textContent = count;
}
function updateLeaderboard(list) {
    // ...
}
function updateStreamState(state) {
    // ...
}

// --- Initialisierung auf Viewer-Seite ---
document.addEventListener("DOMContentLoaded", () => {
    const streamId = window.LIVE_STREAM_ID;
    if (streamId) {
        initLiveSocket(streamId);
    }
});
