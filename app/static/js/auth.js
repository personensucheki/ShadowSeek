function showModal(id) {
    const modal = document.getElementById(id);
    if (!modal) {
        return;
    }

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (!modal) {
        return;
    }

    modal.style.display = "none";
    document.body.style.overflow = "";
}

function hideAllModals() {
    ["login-modal", "register-modal", "forgot-modal"].forEach(hideModal);
}

function setModalError(id, message) {
    const target = document.getElementById(id);
    if (!target) {
        return;
    }
    target.textContent = message || "";
}

async function submitAuthForm(form, errorId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
    const formData = new FormData(form);

    const response = await fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
            Accept: "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        credentials: "same-origin",
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.success === false) {
        setModalError(errorId, payload.message || "Aktion fehlgeschlagen.");
        return;
    }

    hideAllModals();
    window.location.href = payload.redirect || "/search";
}

window.addEventListener("openLoginModal", () => {
    hideAllModals();
    showModal("login-modal");
});

window.addEventListener("openRegisterModal", () => {
    hideAllModals();
    showModal("register-modal");
});

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".modal-close").forEach((button) => {
        button.addEventListener("click", () => hideAllModals());
    });

    document.querySelectorAll(".modal-overlay").forEach((overlay) => {
        overlay.addEventListener("mousedown", function(event) {
            if (event.target === overlay) {
                hideAllModals();
            }
        });
    });

    document.addEventListener("keydown", function(event) {
        if (event.key === "Escape") {
            hideAllModals();
        }
    });

    const forgotLink = document.getElementById("forgot-link");
    if (forgotLink) {
        forgotLink.addEventListener("click", function(event) {
            event.preventDefault();
            hideAllModals();
            showModal("forgot-modal");
        });
    }

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            setModalError("login-error", "");
            await submitAuthForm(loginForm, "login-error");
        });
    }

    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            setModalError("register-error", "");
            const password = registerForm.querySelector('input[name="password"]')?.value || "";
            const password2 = registerForm.querySelector('input[name="password2"]')?.value || "";
            if (password !== password2) {
                setModalError("register-error", "Passwoerter stimmen nicht ueberein.");
                return;
            }
            await submitAuthForm(registerForm, "register-error");
        });
    }

    const forgotForm = document.getElementById("forgot-form");
    if (forgotForm) {
        forgotForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            setModalError("forgot-error", "");
            await submitAuthForm(forgotForm, "forgot-error");
        });
    }
});
