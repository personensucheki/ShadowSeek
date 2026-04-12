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
});
