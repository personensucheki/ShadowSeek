// agent.js – Interaktiver Web-Support-Agent für Registrierung, Login und Profil
// Fügt sich als Overlay/Widget in bestehende Seiten ein

document.addEventListener('DOMContentLoaded', function () {
    // Agent-Overlay entfernt – keine Box/kein AIBOT mehr

    // Utility: Feedback anzeigen
    function agentMessage(msg, type = 'info') {
        const msgDiv = document.getElementById('agent-messages');
        msgDiv.innerHTML = `<div style="color:${type==='error'?'#ff6b6b':'#4ade80'};margin-bottom:6px;">${msg}</div>`;
    }

    // Utility: Validierung
    function validateForm(form) {
        const data = {};
        let valid = true;
        let error = '';
        for (const el of form.elements) {
            if (!el.name) continue;
            data[el.name] = el.value.trim();
            if (el.required && !el.value.trim()) {
                valid = false;
                error = `Bitte fülle das Feld "${el.name}" aus.`;
                break;
            }
            if (el.name === 'email' && el.value) {
                const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
                if (!emailRegex.test(el.value)) {
                    valid = false;
                    error = 'Bitte gib eine gültige E-Mail-Adresse ein.';
                    break;
                }
            }
            if (el.name === 'password' && el.value) {
                if (el.value.length < 8) {
                    valid = false;
                    error = 'Passwort zu kurz (min. 8 Zeichen).';
                    break;
                }
                if (!/[A-Z]/.test(el.value) || !/[a-z]/.test(el.value) || !/\d/.test(el.value)) {
                    valid = false;
                    error = 'Passwort muss Groß-/Kleinbuchstaben und eine Zahl enthalten.';
                    break;
                }
            }
        }
        return { valid, error, data };
    }

    // Utility: POST-Request
    async function agentPost(url, data) {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return resp.json();
    }

    // Formular-Handler
    function handleForm(form, route, successCb, failCb) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const { valid, error, data } = validateForm(form);
            if (!valid) {
                agentMessage(error, 'error');
                return;
            }
            agentMessage('Wird geprüft ...');
            try {
                const result = await agentPost(route, data);
                if (result.success) {
                    agentMessage(result.message || 'Erfolg!', 'success');
                    successCb && successCb(result);
                } else {
                    agentMessage(result.message || 'Fehler!', 'error');
                    failCb && failCb(result);
                }
            } catch (err) {
                agentMessage('Serverfehler. Bitte später erneut versuchen.', 'error');
            }
        });
    }

    // Registrierung
    const regForm = document.querySelector('form[action="/register"]');
    if (regForm) {
        agentMessage('Bitte registriere dich. Alle Pflichtfelder ausfüllen!');
        handleForm(regForm, '/register', () => {
            agentMessage('Registrierung erfolgreich! Du wirst zum Login weitergeleitet.', 'success');
            setTimeout(() => window.location.href = '/login', 1200);
        });
    }

    // Login
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        agentMessage('Bitte logge dich ein.');
        handleForm(loginForm, '/login', () => {
            agentMessage('Login erfolgreich! Weiterleitung zum Profil ...', 'success');
            setTimeout(() => window.location.href = '/profile', 1200);
        });
    }

    // Profilbearbeitung
    const profileForm = document.querySelector('form[action="/profile/update"]');
    if (profileForm) {
        agentMessage('Du kannst jetzt dein Profil bearbeiten.');
        handleForm(profileForm, '/profile/update', () => {
            agentMessage('Profil aktualisiert!', 'success');
            setTimeout(() => window.location.reload(), 1200);
        });
    }
});
