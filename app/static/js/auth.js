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
});
