function setStatus(message, isError = false) {
  const el = document.getElementById("upload-status");
  if (!el) return;
  el.textContent = message || "";
  el.classList.toggle("error", Boolean(isError));
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("upload-form");
  const mediaType = document.getElementById("media-type");
  const fileInput = document.getElementById("upload-file");

  if (mediaType && fileInput) {
    mediaType.addEventListener("change", () => {
      const type = mediaType.value;
      if (type === "photo") {
        fileInput.accept = "image/png,image/jpeg,image/webp,image/gif";
      } else {
        fileInput.accept = "video/mp4,video/webm,video/quicktime";
      }
    });
  }

  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setStatus("Upload läuft…");

    const fd = new FormData(form);
    try {
      const res = await fetch("/api/upload", { method: "POST", body: fd, credentials: "same-origin" });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Upload fehlgeschlagen.");
      }
      setStatus("Upload erfolgreich. Weiterleitung zum Feed…");
      setTimeout(() => (window.location.href = "/feed"), 600);
    } catch (err) {
      setStatus(err.message || "Upload fehlgeschlagen.", true);
    }
  });
});

