document.addEventListener("DOMContentLoaded", function() {
    const widget = document.getElementById("chatbot-widget");
    const fab = document.getElementById("chat-toggle");
    const minimizeButton = document.getElementById("chatbot-minimize");
    const closeButton = document.getElementById("chatbot-close");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");
    const sendButton = document.getElementById("chatbot-send");
    const messages = document.getElementById("chatbot-messages");

    if (!widget || !fab) {
        return;
    }

    const endpoint = form?.dataset.endpoint || "/api/chatbot";

    const setOpenState = function(isOpen) {
        widget.hidden = !isOpen;
        widget.setAttribute("aria-hidden", String(!isOpen));
        fab.setAttribute("aria-expanded", String(isOpen));

        if (isOpen && input) {
            window.setTimeout(function() {
                input.focus();
            }, 0);
        }
    };

    const appendMessage = function(sender, text) {
        if (!messages) {
            return;
        }

        const message = document.createElement("div");
        message.className = `chatbot-msg chatbot-msg-${sender}`;
        message.textContent = text;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    };

    const seedWelcomeMessage = function() {
        if (!messages || messages.childElementCount > 0) {
            return;
        }

        appendMessage(
            "bot",
            "Search ist live. Der Assistant beantwortet aktuell nur Basisanfragen.",
        );
    };

    fab.addEventListener("click", function() {
        widget.classList.remove("minimized");
        setOpenState(true);
        seedWelcomeMessage();
    });

    if (minimizeButton) {
        minimizeButton.addEventListener("click", function() {
            widget.classList.toggle("minimized");
        });
    }

    if (closeButton) {
        closeButton.addEventListener("click", function() {
            widget.classList.remove("minimized");
            setOpenState(false);
        });
    }

    document.addEventListener("keydown", function(event) {
        if (event.key === "Escape" && !widget.hidden) {
            widget.classList.remove("minimized");
            setOpenState(false);
        }
    });

    if (form && input && sendButton && messages) {
        form.addEventListener("submit", async function(event) {
            event.preventDefault();

            const text = input.value.trim();
            if (!text) {
                return;
            }

            appendMessage("user", text);
            input.value = "";
            input.disabled = true;
            sendButton.disabled = true;

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text }),
                });
                const payload = await response.json().catch(function() {
                    return {};
                });

                if (!response.ok) {
                    appendMessage(
                        "bot",
                        payload.error || "Assistant derzeit nicht verfuegbar.",
                    );
                    return;
                }

                appendMessage("bot", payload.reply || "Keine Antwort verfuegbar.");
            } catch (error) {
                appendMessage("bot", "Assistant derzeit nicht erreichbar.");
            } finally {
                input.disabled = false;
                sendButton.disabled = false;
                input.focus();
            }
        });
    }

    const handleResize = function() {
        if (window.innerWidth < 600) {
            widget.style.width = "98vw";
            widget.style.right = "1vw";
            widget.style.bottom = "86px";
            return;
        }

        widget.style.width = "340px";
        widget.style.right = "30px";
        widget.style.bottom = "112px";
    };

    window.addEventListener("resize", handleResize);
    handleResize();
});
