document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("profile-form");
    const message = document.getElementById("profile-message");
    if (!form || !message) {
        return;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        message.textContent = "";

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
        const payload = new FormData(form);

        try {
            const response = await fetch("/profile/update", {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
                },
                credentials: "same-origin",
                body: payload,
            });

            const result = await response.json();
            message.textContent = result.message || (response.ok ? "Profil gespeichert." : "Fehler.");
            message.style.color = result.success ? "#00FF9F" : "#FF00FF";
            message.style.fontWeight = "bold";

            if (result.success) {
                window.setTimeout(() => {
                    window.location.reload();
                }, 700);
            }
        } catch {
            message.textContent = "Profil konnte nicht gespeichert werden.";
            message.style.color = "#FF00FF";
            message.style.fontWeight = "bold";
        }
    });
});
