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

    // Send Message
    function sendMessage() {
        const message = inputField.value.trim();
        if (message) {
            // Add User Message
            addMessage(message, 'user');
            inputField.value = '';

            // Simulate Bot Response
            setTimeout(() => {
                const response = getBotResponse(message);
                addMessage(response, 'bot');
            }, 500);
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

    function getBotResponse(input) {
        input = input.toLowerCase();
        if (input.includes('register') || input.includes('sign up')) {
            return "You can register by clicking the 'Get Started' button in the hero section.";
        } else if (input.includes('login') || input.includes('sign in')) {
            return "Already have an account? Click the 'Login' button to access your dashboard.";
        } else if (input.includes('price') || input.includes('cost')) {
            return "Our marketplace offers competitive prices directly from farmers. Check the Marketplace section!";
        } else if (input.includes('about')) {
            return "AgriStar connects farmers and buyers directly. We also provide AI-driven farming advice.";
        } else {
            return "I'm here to help you navigate. You can ask about registration, login, or our features.";
        }
    }
});
