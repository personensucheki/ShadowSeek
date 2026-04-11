// static/js/profile.js

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('profile-form');
    const msgDiv = document.getElementById('profile-message');
    if (!form) return;
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        msgDiv.textContent = '';
        const data = {
            display_name: form.display_name.value,
            email: form.email.value,
            password: form.password.value,
            bio: form.bio.value
        };
        const resp = await fetch('/profile/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        msgDiv.textContent = result.message;
        msgDiv.style.color = result.success ? '#00FF9F' : '#FF00FF';
        msgDiv.style.fontWeight = 'bold';
        if (result.success) {
            setTimeout(() => msgDiv.textContent = '', 2500);
        }
    });
});
