// Navbar-Interaktionen: Öffnen der Modals für Login/Registrierung

document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            // Modal-Öffnung folgt in Schritt 7
            window.dispatchEvent(new CustomEvent('openLoginModal'));
        });
    }
    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            // Modal-Öffnung folgt in Schritt 7
            window.dispatchEvent(new CustomEvent('openRegisterModal'));
        });
    }
});
