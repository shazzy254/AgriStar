document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('chatbot-toggle');
    const closeBtn = document.getElementById('chatbot-close');
    const chatWindow = document.getElementById('chatbot-window');
    const sendBtn = document.getElementById('chatbot-send');
    const inputField = document.getElementById('chatbot-input');
    const messagesContainer = document.getElementById('chatbot-messages');

    // Toggle Chat Window
    toggleBtn.addEventListener('click', () => {
        chatWindow.classList.toggle('d-none');
    });

    closeBtn.addEventListener('click', () => {
        chatWindow.classList.add('d-none');
    });

    // Get CSRF Token helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Send Message
    async function sendMessage() {
        const message = inputField.value.trim();
        if (message) {
            // Add User Message
            addMessage(message, 'user');
            inputField.value = '';

            // Show Loading Indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('bot-message', 'loading');
            loadingDiv.innerHTML = '<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
            messagesContainer.appendChild(loadingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            try {
                // Get CSRF token
                const csrftoken = getCookie('csrftoken');

                const response = await fetch('/ai/public-chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({ message: message })
                });

                // Check content type to identify HTML errors (403/500)
                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    // Try to read text to log it
                    const text = await response.text();
                    console.error("Server returned non-JSON:", text.substring(0, 100)); // Log first 100 chars
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Remove Loading Indicator
                if (messagesContainer.contains(loadingDiv)) {
                    messagesContainer.removeChild(loadingDiv);
                }

                if (response.ok) {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage(data.error || "Sorry, I can't answer that right now.", 'bot');
                }
            } catch (error) {
                console.error("Chatbot Error:", error);
                if (messagesContainer.contains(loadingDiv)) {
                    messagesContainer.removeChild(loadingDiv);
                }
                addMessage("I'm having trouble connecting to the server. Please try again.", 'bot');
            }
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        div.textContent = text;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
