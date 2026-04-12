// --- Mobile Direct-Live Kamera/Mikrofon Steuerung ---
let directStream = null;
let currentFacing = "user"; // "user" (Front) oder "environment" (Back)
let micEnabled = true;
const videoEl = document.getElementById("live-preview-video");
const btnFront = document.getElementById("btn-front");
const btnBack = document.getElementById("btn-back");
const btnMic = document.getElementById("btn-mic");
const statusEl = document.getElementById("direct-status");

function setStatus(msg, error = false) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.style.color = error ? "#FF00FF" : "#00FF9F";
}

async function startDirectStream(facing = "user", audio = true) {
    setStatus("Starte Kamera...", false);
    if (directStream) {
        directStream.getTracks().forEach(track => track.stop());
        directStream = null;
    }
    let constraints = {
        video: { facingMode: facing },
        audio: audio
    };
    try {
        directStream = await navigator.mediaDevices.getUserMedia(constraints);
        if (videoEl) {
            videoEl.srcObject = directStream;
        }
        setStatus("Kamera aktiv", false);
        micEnabled = audio;
        updateButtonStates();
    } catch (err) {
        setStatus("Fehler: " + (err.message || err), true);
        updateButtonStates();
    }
}

function stopDirectStream() {
    if (directStream) {
        directStream.getTracks().forEach(track => track.stop());
        directStream = null;
        if (videoEl) videoEl.srcObject = null;
    }
    setStatus("Kamera gestoppt", false);
    updateButtonStates();
}

function updateButtonStates() {
    if (!btnFront || !btnBack || !btnMic) return;
    btnFront.classList.toggle("active", currentFacing === "user");
    btnBack.classList.toggle("active", currentFacing === "environment");
    btnMic.classList.toggle("active", micEnabled);
    btnMic.textContent = micEnabled ? "Mikro an" : "Mikro aus";
}

if (btnFront && btnBack && btnMic) {
    btnFront.addEventListener("click", async () => {
        if (currentFacing !== "user") {
            currentFacing = "user";
            await startDirectStream(currentFacing, micEnabled);
        }
    });
    btnBack.addEventListener("click", async () => {
        if (currentFacing !== "environment") {
            currentFacing = "environment";
            await startDirectStream(currentFacing, micEnabled);
        }
    });
    btnMic.addEventListener("click", async () => {
        micEnabled = !micEnabled;
        // Versuche Audio-Track zu aktivieren/deaktivieren
        if (directStream) {
            const audioTracks = directStream.getAudioTracks();
            if (audioTracks.length) {
                audioTracks.forEach(track => track.enabled = micEnabled);
                setStatus(micEnabled ? "Mikro an" : "Mikro aus", false);
            } else {
                // Kein Audio-Track vorhanden, Stream neu holen
                await startDirectStream(currentFacing, micEnabled);
            }
        } else {
            await startDirectStream(currentFacing, micEnabled);
        }
        updateButtonStates();
    });
}

// Standard: Frontkamera + Mikro an
if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches) {
    // Nur auf Mobile automatisch starten
    startDirectStream("user", true);
}
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
