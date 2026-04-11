// Modal logic
function showLoginModal() {
    closeAllModals();
    document.getElementById('login-modal').style.display = 'flex';
}
function showRegisterModal() {
    closeAllModals();
    document.getElementById('register-modal').style.display = 'flex';
}
function showForgotModal() {
    closeAllModals();
    document.getElementById('forgot-modal').style.display = 'flex';
}
function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}
function closeAllModals() {
    ['login-modal','register-modal','forgot-modal'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
}
// Form submit logic
function setupModalForms() {
    document.getElementById('login-form').onsubmit = function(e){ e.preventDefault(); login(); };
    document.getElementById('register-form').onsubmit = function(e){ e.preventDefault(); register(); };
    document.getElementById('forgot-form').onsubmit = function(e){ e.preventDefault(); sendResetLink(); };
}
document.addEventListener('DOMContentLoaded', setupModalForms);

// Chatbot logic
function setupChatbot() {
    const toggleBtn = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const messagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');

    function addMessage(text, isUser = false) {
        const div = document.createElement('div');
        div.style.marginBottom = '16px';
        div.style.padding = '10px 14px';
        div.style.borderRadius = '12px';
        div.style.maxWidth = '85%';
        div.style.background = isUser ? '#00f0ff' : '#2a3a52';
        div.style.color = isUser ? '#0a0c14' : '#e0e0e0';
        div.style.marginLeft = isUser ? 'auto' : '0';
        div.textContent = text;
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    toggleBtn.addEventListener('click', () => {
        chatWindow.style.display = chatWindow.style.display === 'block' ? 'none' : 'block';
    });

    sendBtn.addEventListener('click', async () => {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, true);
        input.value = '';

        const loading = document.createElement('div');
        loading.textContent = 'denkt...';
        loading.style.color = '#666';
        loading.style.fontStyle = 'italic';
        messagesDiv.appendChild(loading);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            loading.remove();
            if (data.reply) addMessage(data.reply);
        } catch (e) {
            loading.remove();
            addMessage('Sorry, bin gerade offline.', false);
        }
    });

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendBtn.click();
    });
}
document.addEventListener('DOMContentLoaded', setupChatbot);
