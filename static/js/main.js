// Chatbot Interaktion (Öffnen/Schließen, Animationen, Senden)
document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.getElementById('chat-toggle');
    const chatbotWidget = document.getElementById('chatbot-widget');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');

    // Öffnen/Schließen + Verlauf laden
    chatToggle.addEventListener('click', function() {
        chatbotWidget.removeAttribute('hidden');
        restoreChatHistory();
        chatbotInput.focus();
    });
    // Schließen per X-Button (bereits im HTML)

    // Schließen per ESC
    document.addEventListener('keydown', function(e) {
        if (!chatbotWidget.hasAttribute('hidden') && e.key === 'Escape') {
            chatbotWidget.setAttribute('hidden', '');
        }
    });


    // Senden per Button oder Enter (mit API)
    async function sendMessage() {
        const text = chatbotInput.value.trim();
        if (!text) return;
        appendMessage('user', text);
        chatbotInput.value = '';
        chatbotInput.disabled = true;
        chatbotSend.disabled = true;
        appendMessage('bot', '...'); // Loading-Indicator
        try {
            const res = await fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            // Entferne Loading
            removeLastBotLoading();
            if (res.ok && data.reply) {
                appendMessage('bot', data.reply);
            } else {
                appendMessage('bot', 'Fehler: ' + (data.error || 'Unbekannter Fehler'));
            }
        } catch (e) {
            removeLastBotLoading();
            appendMessage('bot', 'Fehler: Server nicht erreichbar.');
        }
        chatbotInput.disabled = false;
        chatbotSend.disabled = false;
        chatbotInput.focus();
    }
    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    function removeLastBotLoading() {
        const msgs = chatbotMessages.querySelectorAll('.chatbot-msg-bot');
        if (msgs.length) {
            const last = msgs[msgs.length-1];
            if (last.textContent === '...') last.remove();
        }
    }

    // Microanimation beim Öffnen
    chatbotWidget.addEventListener('transitionend', function() {
        if (!chatbotWidget.hasAttribute('hidden')) {
            chatbotWidget.classList.add('chatbot-opened');
            setTimeout(()=>chatbotWidget.classList.remove('chatbot-opened'), 400);
        }
    });

    // Message-Rendering & Verlauf
    function appendMessage(sender, text) {
        const msg = document.createElement('div');
        msg.className = 'chatbot-msg chatbot-msg-' + sender;
        msg.textContent = text;
        chatbotMessages.appendChild(msg);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        saveChatHistory();
    }

    function saveChatHistory() {
        const history = [];
        chatbotMessages.querySelectorAll('.chatbot-msg').forEach(msg => {
            history.push({
                sender: msg.classList.contains('chatbot-msg-user') ? 'user' : 'bot',
                text: msg.textContent
            });
        });
        localStorage.setItem('chatbotHistory', JSON.stringify(history));
    }

    function restoreChatHistory() {
        chatbotMessages.innerHTML = '';
        const history = JSON.parse(localStorage.getItem('chatbotHistory') || '[]');
        history.forEach(item => appendMessage(item.sender, item.text));
    }
});
