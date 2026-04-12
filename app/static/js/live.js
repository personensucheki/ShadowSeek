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
<<<<<<< ours
<<<<<<< ours
    // Kategorie-/Game-Dropdown-Logik
    const categorySelect = document.getElementById("live-category");
    const gameRow = document.getElementById("game-row");
    const topicRow = document.getElementById("topic-row");
    if (categorySelect && gameRow && topicRow) {
        function updateGameTopicVisibility() {
            if (categorySelect.value === "Games") {
                gameRow.style.display = "block";
                topicRow.style.display = "none";
            } else {
                gameRow.style.display = "none";
                topicRow.style.display = "block";
            }
        }
        categorySelect.addEventListener("change", updateGameTopicVisibility);
        updateGameTopicVisibility();
    }

    // Dynamische Game-Suche
    const gameSearchInput = document.getElementById("live-game-search");
    const gameSearchResults = document.getElementById("game-search-results");
    const gameHiddenInput = document.getElementById("live-game");
    if (gameSearchInput && gameSearchResults && gameHiddenInput) {
        let lastQuery = "";
        let debounceTimeout = null;
        gameSearchInput.addEventListener("input", function() {
            const q = gameSearchInput.value.trim();
            if (q.length < 2) {
                gameSearchResults.innerHTML = "";
                return;
            }
            if (debounceTimeout) clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                fetch(`/api/games/search?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (!data.success) return;
                        gameSearchResults.innerHTML = "";
                        data.results.forEach(game => {
                            const div = document.createElement("div");
                            div.className = "game-search-result";
                            div.innerHTML = `
                                <span class="game-name">${game.name}</span>
                                ${game.cover ? `<img src="${game.cover}" alt="${game.name}" class="game-cover">` : ""}
                            `;
                            div.addEventListener("click", () => {
                                gameSearchInput.value = game.name;
                                gameHiddenInput.value = game.id;
                                gameSearchResults.innerHTML = "";
                            });
                            gameSearchResults.appendChild(div);
                        });
                    });
            }, 180);
        });
        // Reset hidden input if user changes text
        gameSearchInput.addEventListener("input", function() {
            gameHiddenInput.value = "";
        });
    }
=======
>>>>>>> theirs
=======
>>>>>>> theirs
document.addEventListener("DOMContentLoaded", () => {
    const modeButtons = document.querySelectorAll("[data-mode]");
    const modeObs = document.getElementById("mode-obs");
    const modeDirect = document.getElementById("mode-direct");
    const previewVideo = document.getElementById("live-preview-video");
    const enableCameraBtn = document.getElementById("enable-camera");
    const disableCameraBtn = document.getElementById("disable-camera");
    const toggleKeyBtn = document.getElementById("toggle-key");
    const copyKeyBtn = document.getElementById("copy-key");
    const streamKeyInput = document.getElementById("live-stream-key");
    const setupForm = document.getElementById("live-setup-form");
    const feedback = document.getElementById("live-feedback");

    let previewStream = null;

    modeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const mode = button.dataset.mode;
            modeButtons.forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");

            const obsActive = mode === "obs";
            modeObs.classList.toggle("active", obsActive);
            modeDirect.classList.toggle("active", !obsActive);
        });
    });

    async function startCameraPreview() {
        try {
            previewStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true,
            });
            previewVideo.srcObject = previewStream;
            feedback.textContent = "Kamera und Mikrofon sind aktiv.";
        } catch (error) {
            feedback.textContent = "Kein Zugriff auf Kamera/Mikrofon möglich.";
        }
    }

    function stopCameraPreview() {
        if (!previewStream) {
            return;
        }
        previewStream.getTracks().forEach((track) => track.stop());
        previewVideo.srcObject = null;
        previewStream = null;
        feedback.textContent = "Kamera-Vorschau gestoppt.";
    }

    enableCameraBtn?.addEventListener("click", startCameraPreview);
    disableCameraBtn?.addEventListener("click", stopCameraPreview);

    toggleKeyBtn?.addEventListener("click", () => {
        const showing = streamKeyInput.type === "text";
        streamKeyInput.type = showing ? "password" : "text";
        toggleKeyBtn.textContent = showing ? "Anzeigen" : "Verbergen";
    });

    copyKeyBtn?.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(streamKeyInput.value);
            feedback.textContent = "Stream-Key in die Zwischenablage kopiert.";
        } catch (error) {
            feedback.textContent = "Kopieren nicht möglich.";
        }
    });

    setupForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(setupForm);
        const title = (formData.get("title") || "").toString().trim();
        const category = (formData.get("category") || "").toString().trim();
        if (!title || !category) {
            feedback.textContent = "Bitte Titel und Kategorie auswählen.";
            return;
        }
        feedback.textContent = "Live-Setup gespeichert. Als nächstes: Stream starten.";
    });
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< HEAD
=======
});document.addEventListener("DOMContentLoaded", () => {
    const modeButtons = document.querySelectorAll("[data-mode]");
    const modeObs = document.getElementById("mode-obs");
    const modeDirect = document.getElementById("mode-direct");
    const previewVideo = document.getElementById("live-preview-video");
    const enableCameraBtn = document.getElementById("enable-camera");
    const disableCameraBtn = document.getElementById("disable-camera");
    const toggleKeyBtn = document.getElementById("toggle-key");
    const copyKeyBtn = document.getElementById("copy-key");
    const streamKeyInput = document.getElementById("live-stream-key");
    const setupForm = document.getElementById("live-setup-form");
    const feedback = document.getElementById("live-feedback");

    let previewStream = null;

    modeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const mode = button.dataset.mode;
            modeButtons.forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");

            const obsActive = mode === "obs";
            modeObs.classList.toggle("active", obsActive);
            modeDirect.classList.toggle("active", !obsActive);
        });
    });

    async function startCameraPreview() {
        try {
            previewStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true,
            });
            previewVideo.srcObject = previewStream;
            feedback.textContent = "Kamera und Mikrofon sind aktiv.";
        } catch (error) {
            feedback.textContent = "Kein Zugriff auf Kamera/Mikrofon möglich.";
        }
    }

    function stopCameraPreview() {
        if (!previewStream) {
            return;
        }
        previewStream.getTracks().forEach((track) => track.stop());
        previewVideo.srcObject = null;
        previewStream = null;
        feedback.textContent = "Kamera-Vorschau gestoppt.";
    }

    enableCameraBtn?.addEventListener("click", startCameraPreview);
    disableCameraBtn?.addEventListener("click", stopCameraPreview);

    toggleKeyBtn?.addEventListener("click", () => {
        const showing = streamKeyInput.type === "text";
        streamKeyInput.type = showing ? "password" : "text";
        toggleKeyBtn.textContent = showing ? "Anzeigen" : "Verbergen";
    });

    copyKeyBtn?.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(streamKeyInput.value);
            feedback.textContent = "Stream-Key in die Zwischenablage kopiert.";
        } catch (error) {
            feedback.textContent = "Kopieren nicht möglich.";
        }
    });

    setupForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(setupForm);
        const title = (formData.get("title") || "").toString().trim();
        const category = (formData.get("category") || "").toString().trim();
        if (!title || !category) {
            feedback.textContent = "Bitte Titel und Kategorie auswählen.";
            return;
        }
        feedback.textContent = "Live-Setup gespeichert. Als nächstes: Stream starten.";
    });
>>>>>>> ca53806 (Login reperatur)
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
});
