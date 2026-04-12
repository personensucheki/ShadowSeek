
// Moderner, mehrstufiger Upload- und Video-Editor-Flow
// Steps: MediaPicker → VideoEditor → PublishScreen

document.addEventListener("DOMContentLoaded", () => {
  // Step-Elemente
  const stepMediaPicker = document.getElementById("step-media-picker");
  const stepVideoEditor = document.getElementById("step-video-editor");
  const stepPublish = document.getElementById("step-publish");

  // MediaPicker
  const fileInput = document.getElementById("media-file");
  const mediaPreview = document.getElementById("media-preview");
  const toEditorBtn = document.getElementById("to-editor");

  // VideoEditor
  const editorVideo = document.getElementById("editor-video");
  const trimStart = document.getElementById("trim-start");
  const trimEnd = document.getElementById("trim-end");
  const toPublishBtn = document.getElementById("to-publish");
  const backToPickerBtn = document.getElementById("back-to-picker");

  // PublishScreen
  const publishForm = document.getElementById("publish-form");
  const backToEditorBtn = document.getElementById("back-to-editor");
  const uploadStatus = document.getElementById("upload-status");

  // State
  let selectedFile = null;
  let isVideo = false;
  let trim = { start: 0, end: 100 };

  // Helper: Statusanzeige
  function setStatus(message, isError = false) {
    if (!uploadStatus) return;
    uploadStatus.textContent = message || "";
    uploadStatus.classList.toggle("error", Boolean(isError));
  }

  // Step-Navigation
  function showStep(step) {
    stepMediaPicker.style.display = step === 1 ? "block" : "none";
    stepVideoEditor.style.display = step === 2 ? "block" : "none";
    stepPublish.style.display = step === 3 ? "block" : "none";
  }

  // Step 1: MediaPicker
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    selectedFile = file;
    mediaPreview.innerHTML = "";
    toEditorBtn.disabled = !file;
    if (!file) return;
    isVideo = file.type.startsWith("video/");
    if (isVideo) {
      const url = URL.createObjectURL(file);
      mediaPreview.innerHTML = `<video src="${url}" controls style="max-width:100%;border-radius:12px;"></video>`;
    } else {
      const url = URL.createObjectURL(file);
      mediaPreview.innerHTML = `<img src="${url}" style="max-width:100%;border-radius:12px;" />`;
    }
  });

  toEditorBtn.addEventListener("click", () => {
    if (!selectedFile) return;
    if (isVideo) {
      // VideoEditor anzeigen
      const url = URL.createObjectURL(selectedFile);
      editorVideo.src = url;
      trimStart.value = 0;
      trimEnd.value = 100;
      showStep(2);
    } else {
      // Direkt zu PublishScreen
      showStep(3);
    }
  });

  // Step 2: VideoEditor
  if (backToPickerBtn) {
    backToPickerBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showStep(1);
    });
  }
  if (toPublishBtn) {
    toPublishBtn.addEventListener("click", (e) => {
      e.preventDefault();
      trim.start = parseInt(trimStart.value, 10);
      trim.end = parseInt(trimEnd.value, 10);
      showStep(3);
    });
  }

  // Step 3: PublishScreen
  if (backToEditorBtn) {
    backToEditorBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (isVideo) {
        showStep(2);
      } else {
        showStep(1);
      }
    });
  }

  if (publishForm) {
    publishForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      setStatus("Upload läuft…");
      if (!selectedFile) {
        setStatus("Keine Datei gewählt.", true);
        return;
      }
      const caption = document.getElementById("publish-caption").value;
      const hashtags = document.getElementById("publish-hashtags").value;
      const location = document.getElementById("publish-location").value;
      const isPublic = document.getElementById("publish-public").checked;

      // FormData bauen
      const fd = new FormData();
      fd.append("file", selectedFile);
      fd.append("caption", caption);
      fd.append("hashtags", hashtags);
      fd.append("location", location);
      fd.append("is_public", isPublic ? "true" : "false");
      if (isVideo) {
        fd.append("trim_start", trim.start);
        fd.append("trim_end", trim.end);
      }

      try {
        const res = await fetch("/api/upload", { method: "POST", body: fd, credentials: "same-origin" });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || "Upload fehlgeschlagen.");
        }
        setStatus("Upload erfolgreich. Weiterleitung zum Feed…");
        setTimeout(() => (window.location.href = "/feed"), 800);
      } catch (err) {
        setStatus(err.message || "Upload fehlgeschlagen.", true);
      }
    });
  }

  // Initial Step
  showStep(1);
});

