// AgriStar AI Assistant - Complete Frontend
// Handles text chat, voice input/output, image upload, and conversation history

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const voiceBtn = document.getElementById('voice-btn');
const uploadBtn = document.getElementById('upload-btn');
const imageInput = document.getElementById('image-input');
const imagePreviewArea = document.getElementById('image-preview-area');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image');
const statusText = document.getElementById('status-text');
const langEnBtn = document.getElementById('lang-en');
const langSwBtn = document.getElementById('lang-sw');
const conversationList = document.getElementById('conversation-list');

// State
let currentConversationId = chatMessages.dataset.conversationId || null;
let selectedImage = null;
let currentLang = 'en';
let isRecording = false;
let recognition = null;
let speechSynthesis = window.speechSynthesis;

// Get CSRF token from cookie
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

const csrftoken = getCookie('csrftoken');

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
}

// Language detection
function detectLanguage(text) {
    const swahiliWords = /\b(na|kwa|kuna|sasa|siku|nini|nifanye|madoda|majani|mahindi|samahani|tafadhali|asante|habari|vipi|nimeona)\b/i;
    return swahiliWords.test(text) ? 'sw' : 'en';
}

// Append message to chat
function appendMessage(role, content, imageUrl = null, analysis = null) {
    const welcomeMsg = document.getElementById('welcome-msg');
    if (welcomeMsg) welcomeMsg.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (imageUrl) {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'message-image d-block';
        img.onclick = () => window.open(imageUrl, '_blank');
        bubble.appendChild(img);
    }

    const textDiv = document.createElement('div');
    textDiv.innerHTML = formatMessage(content);
    bubble.appendChild(textDiv);

    if (analysis) {
        bubble.appendChild(createAnalysisCard(analysis));
    }

    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message text
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/^(\d+)\. (.+)$/gm, '<div>$1. $2</div>');
}

// Create analysis card
function createAnalysisCard(analysis) {
    const card = document.createElement('div');
    card.className = 'analysis-card mt-2';

    const severityClass = `severity-${(analysis.severity || 'unknown').toLowerCase()}`;

    card.innerHTML = `
        <h6 class="mb-2"><i class="bi bi-clipboard-check me-2"></i>Analysis</h6>
        <p class="mb-1"><strong>Detected:</strong> ${analysis.detected_issue || 'Unknown'}</p>
        <p class="mb-1"><strong>Severity:</strong> <span class="${severityClass}">${analysis.severity || 'Unknown'}</span></p>
        <p class="mb-2"><strong>Confidence:</strong> ${analysis.confidence || 0}%</p>
    `;

    if (analysis.treatment && analysis.treatment.length > 0) {
        card.innerHTML += '<p class="mb-1"><strong>Treatment:</strong></p><ul class="small mb-2">';
        analysis.treatment.forEach(step => {
            card.innerHTML += `<li>${step}</li>`;
        });
        card.innerHTML += '</ul>';
    }

    return card;
}

// Show typing indicator
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

// Send text message
async function sendMessage() {
    const message = userInput.value.trim();

    if (!message && !selectedImage) return;

    if (selectedImage) {
        await uploadImage();
        return;
    }

    const lang = currentLang || detectLanguage(message);

    appendMessage('user', message);
    userInput.value = '';

    userInput.disabled = true;
    sendBtn.disabled = true;
    statusText.textContent = lang === 'sw' ? 'Inajibu...' : 'Thinking...';

    showTyping();

    try {
        const response = await fetch('/ai/message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                message: message,
                lang: lang,
                conversation_id: currentConversationId
            })
        });

        hideTyping();

        if (!response.ok) throw new Error('Network error');

        const data = await response.json();

        if (data.answer) {
            appendMessage('ai', data.answer);
            currentConversationId = data.conversation_id;
            statusText.textContent = 'Ready';

            // Speak response if enabled
            speakText(data.answer, lang);

            loadConversationHistory();
        } else if (data.error) {
            appendMessage('ai', data.error);
            statusText.textContent = 'Error';
        }

    } catch (error) {
        hideTyping();
        console.error('Error:', error);
        appendMessage('ai', 'Samahani, kuna tatizo. / Sorry, an error occurred.');
        statusText.textContent = 'Error';
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Upload and analyze image
async function uploadImage() {
    if (!selectedImage) return;

    const formData = new FormData();
    formData.append('image', selectedImage);
    if (currentConversationId) {
        formData.append('conversation_id', currentConversationId);
    }

    const imageUrl = URL.createObjectURL(selectedImage);
    appendMessage('user', '[Uploaded crop image]', imageUrl);

    clearImagePreview();

    uploadBtn.disabled = true;
    sendBtn.disabled = true;
    statusText.textContent = 'Analyzing image...';

    showTyping();

    try {
        const response = await fetch('/ai/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        });

        hideTyping();

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();

        if (data.analysis) {
            appendMessage('ai', data.ai_response || 'Analysis complete', null, data.analysis);
            currentConversationId = data.conversation_id;
            statusText.textContent = 'Ready';
            loadConversationHistory();
        } else if (data.error) {
            appendMessage('ai', data.error);
            statusText.textContent = 'Error';
        }

    } catch (error) {
        hideTyping();
        console.error('Error:', error);
        appendMessage('ai', 'Failed to analyze image.');
        statusText.textContent = 'Error';
    } finally {
        uploadBtn.disabled = false;
        sendBtn.disabled = false;
    }
}

// Voice input (speech-to-text)
function startVoiceInput() {
    if (!recognition) {
        alert('Voice input not supported in this browser');
        return;
    }

    if (isRecording) {
        recognition.stop();
        return;
    }

    recognition.lang = currentLang === 'sw' ? 'sw-KE' : 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        voiceBtn.classList.add('recording');
        statusText.textContent = currentLang === 'sw' ? 'Sikiliza...' : 'Listening...';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        statusText.textContent = 'Ready';
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        statusText.textContent = 'Voice error';
        isRecording = false;
        voiceBtn.classList.remove('recording');
    };

    recognition.onend = () => {
        isRecording = false;
        voiceBtn.classList.remove('recording');
        statusText.textContent = 'Ready';
    };

    recognition.start();
}

// Voice output (text-to-speech)
function speakText(text, lang) {
    if (!speechSynthesis) return;

    // Stop any ongoing speech
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'sw' ? 'sw-KE' : 'en-US';
    utterance.rate = 0.9;
    utterance.pitch = 1;

    speechSynthesis.speak(utterance);
}

// Image handling
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        alert('Image too large (max 5MB)');
        return;
    }

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        alert('Invalid format (use JPG, PNG, or WEBP)');
        return;
    }

    selectedImage = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreviewArea.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
});

function clearImagePreview() {
    selectedImage = null;
    imageInput.value = '';
    imagePreview.src = '';
    imagePreviewArea.classList.add('d-none');
}

// Load conversation history
async function loadConversationHistory() {
    try {
        const response = await fetch('/ai/history/');
        const data = await response.json();

        if (data.conversations && data.conversations.length > 0) {
            conversationList.innerHTML = '';
            data.conversations.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'p-2 border-bottom conversation-item';
                if (conv.id == currentConversationId) item.classList.add('bg-light');
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <strong class="small">${conv.title}</strong>
                    <p class="small text-muted mb-0">${conv.message_count} messages</p>
                `;
                item.onclick = () => loadConversation(conv.id);
                conversationList.appendChild(item);
            });
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// Load specific conversation
async function loadConversation(convId) {
    try {
        const response = await fetch(`/ai/conversation/${convId}/`);
        const data = await response.json();

        if (data.messages) {
            chatMessages.innerHTML = '';
            currentConversationId = convId;

            data.messages.forEach(msg => {
                appendMessage(msg.role, msg.content, msg.image_url, msg.image_analysis);
            });

            loadConversationHistory();
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}

// Language selection
langEnBtn.addEventListener('click', () => {
    currentLang = 'en';
    langEnBtn.classList.remove('btn-outline-light');
    langEnBtn.classList.add('btn-light');
    langSwBtn.classList.remove('btn-light');
    langSwBtn.classList.add('btn-outline-light');
});

langSwBtn.addEventListener('click', () => {
    currentLang = 'sw';
    langSwBtn.classList.remove('btn-outline-light');
    langSwBtn.classList.add('btn-light');
    langEnBtn.classList.remove('btn-light');
    langEnBtn.classList.add('btn-outline-light');
});

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
voiceBtn.addEventListener('click', startVoiceInput);
uploadBtn.addEventListener('click', () => imageInput.click());
removeImageBtn.addEventListener('click', clearImagePreview);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Quick tips
document.querySelectorAll('.quick-tip').forEach(btn => {
    btn.addEventListener('click', () => {
        userInput.value = btn.getAttribute('data-q');
        sendMessage();
    });
});

// Load history on page load
loadConversationHistory();
userInput.focus();
