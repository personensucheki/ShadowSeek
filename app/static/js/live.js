// --- Live Studio: TikTok-Flow (Setup -> Live) ---
let directStream = null;
let currentFacing = "user"; // "user" (Front) oder "environment" (Back)
let micEnabled = true;
let selectedMode = "obs"; // "obs" | "direct"
let currentStreamId = null;

const videoEl = document.getElementById("live-preview-video");
const btnFront = document.getElementById("btn-front");
const btnBack = document.getElementById("btn-back");
const btnMic = document.getElementById("btn-mic");

const btnFrontBroadcast = document.getElementById("btn-front-broadcast");
const btnBackBroadcast = document.getElementById("btn-back-broadcast");
const btnMicBroadcast = document.getElementById("btn-mic-broadcast");
const broadcastControlsEl = document.getElementById("live-broadcast-controls");
const statusEl = document.getElementById("direct-status");

const setupStepEl = document.getElementById("live-step-setup");
const broadcastStepEl = document.getElementById("live-step-broadcast");
const editSetupBtn = document.getElementById("live-edit-setup");
const broadcastTitleEl = document.getElementById("live-broadcast-title");
const broadcastSubEl = document.getElementById("live-broadcast-sub");

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
    const fronts = [btnFront, btnFrontBroadcast].filter(Boolean);
    const backs = [btnBack, btnBackBroadcast].filter(Boolean);
    const mics = [btnMic, btnMicBroadcast].filter(Boolean);

    fronts.forEach((button) => button.classList.toggle("active", currentFacing === "user"));
    backs.forEach((button) => button.classList.toggle("active", currentFacing === "environment"));
    mics.forEach((button) => button.classList.toggle("active", micEnabled));

    if (btnMic) btnMic.textContent = micEnabled ? "Mikro an" : "Mikro aus";
    if (btnMicBroadcast) btnMicBroadcast.textContent = micEnabled ? "Mic" : "Mic off";
}

function bindDirectControls(frontBtn, backBtn, micBtn) {
    if (frontBtn) {
        frontBtn.addEventListener("click", async () => {
            if (currentFacing !== "user") {
                currentFacing = "user";
                await startDirectStream(currentFacing, micEnabled);
            }
        });
    }
    if (backBtn) {
        backBtn.addEventListener("click", async () => {
            if (currentFacing !== "environment") {
                currentFacing = "environment";
                await startDirectStream(currentFacing, micEnabled);
            }
        });
    }
    if (micBtn) {
        micBtn.addEventListener("click", async () => {
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
}

bindDirectControls(btnFront, btnBack, btnMic);
bindDirectControls(btnFrontBroadcast, btnBackBroadcast, btnMicBroadcast);

function stopDirectStreamIfRunning() {
    if (directStream) {
        directStream.getTracks().forEach((track) => track.stop());
        directStream = null;
    }
    if (videoEl) {
        videoEl.srcObject = null;
    }
}

function showBroadcastStep() {
    if (setupStepEl) setupStepEl.hidden = true;
    if (broadcastStepEl) broadcastStepEl.hidden = false;
}

function showSetupStep() {
    if (broadcastStepEl) broadcastStepEl.hidden = true;
    if (setupStepEl) setupStepEl.hidden = false;
    stopDirectStreamIfRunning();
}

if (editSetupBtn) {
    editSetupBtn.addEventListener("click", () => {
        showSetupStep();
    });
}
// Live-Studio-Formular: Stream anlegen
document.addEventListener("DOMContentLoaded", () => {
    // Mode Switch UI (OBS vs Direct)
    const modeButtons = document.querySelectorAll(".live-mode-switch button[data-mode]");
    const modeObs = document.getElementById("mode-obs");
    const modeDirect = document.getElementById("mode-direct");

    function activateMode(mode) {
        selectedMode = mode;
        modeButtons.forEach((btn) => {
            btn.classList.toggle("active", btn.getAttribute("data-mode") === mode);
        });
        if (modeObs) modeObs.classList.toggle("active", mode === "obs");
        if (modeDirect) modeDirect.classList.toggle("active", mode === "direct");
    }

    modeButtons.forEach((btn) => {
        btn.addEventListener("click", () => activateMode(btn.getAttribute("data-mode")));
    });

    activateMode("obs");

    const setupForm = document.getElementById("live-setup-form");
    if (setupForm) {
        setupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const feedback = document.getElementById("live-feedback");
            if (feedback) feedback.textContent = "";

            const formData = new FormData(setupForm);
            const data = {
                title: formData.get("title"),
                description: formData.get("description"),
                category: formData.get("category"),
                game: formData.get("game"),
                tags: formData.get("tags"),
                allow_gifts: formData.get("enable_gifts") ? true : false
            };

            if (!data.title || !data.category) {
                if (feedback) feedback.textContent = "Bitte Titel und Kategorie ausfuellen.";
                return;
            }

            if (broadcastTitleEl) broadcastTitleEl.textContent = data.title;
            if (broadcastSubEl) {
                const pieces = [data.category];
                if (data.game) pieces.push(String(data.game));
                broadcastSubEl.textContent = pieces.filter(Boolean).join(" · ");
            }

            try {
                const res = await fetch("/api/live/stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                if (result.success) {
                    currentStreamId = result.stream_id;
                    showBroadcastStep();

                    // Kamera erst nach dem "Live gehen" starten (nicht davor).
                    if (selectedMode === "direct") {
                        if (broadcastControlsEl) broadcastControlsEl.hidden = false;
                        await startDirectStream(currentFacing, micEnabled);
                    } else {
                        if (broadcastControlsEl) broadcastControlsEl.hidden = true;
                        stopDirectStreamIfRunning();
                        setStatus("OBS-Modus aktiv. Kamera-Vorschau ist aus.", false);
                    }

                    if (currentStreamId) {
                        initLiveSocket(currentStreamId);
                    }
                } else {
                    if (feedback) feedback.textContent = result.error || "Fehler beim Anlegen des Streams.";
                }
            } catch (err) {
                if (feedback) feedback.textContent = "Netzwerkfehler beim Anlegen des Streams.";
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
    const chatBox = document.getElementById("live-chat");
    if (!chatBox) return;

    const row = document.createElement("div");
    const username = (data && (data.username || data.user || data.from)) || "User";
    const message = (data && (data.message || data.text)) || "";
    row.textContent = message ? `${username}: ${message}` : String(data || "");
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
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
    if (streamId) initLiveSocket(streamId);

    const chatForm = document.getElementById("live-chat-form");
    const chatInput = document.getElementById("chat-message");
    if (chatForm && chatInput) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const msg = (chatInput.value || "").trim();
            if (!msg) return;
            chatInput.value = "";

            // Local echo (bis Backend-Chat-API/Sockets fertig ist)
            appendLiveChatMessage({ username: "Ich", message: msg });
            if (socket && currentStreamId) {
                socket.emit("chat_message", { stream_id: currentStreamId, message: msg });
            }
        });
    }
});
