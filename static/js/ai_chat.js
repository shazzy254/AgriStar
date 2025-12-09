document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements - Inputs
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-input-btn') || document.getElementById('send-btn');
    const imageInput = document.getElementById('image-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const micBtn = document.getElementById('mic-btn');

    // DOM Elements - UI Areas
    const chatMessages = document.getElementById('chat-messages');
    const filePreviewArea = document.getElementById('file-preview-area');
    const standardInputs = document.getElementById('standard-inputs');
    const recordingUI = document.getElementById('recording-ui');
    const audioReviewUI = document.getElementById('audio-review-ui');
    const recordTimer = document.getElementById('record-timer');

    // DOM Elements - Sidebar
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyList = document.getElementById('history-list');

    // DOM Elements - Audio Review
    const stopRecordBtn = document.getElementById('stop-record-btn');
    const discardAudioBtn = document.getElementById('discard-audio-btn');
    const sendAudioBtn = document.getElementById('send-audio-btn');
    const audioPreviewPlayer = document.getElementById('audio-preview');

    // State
    let currentSessionId = null;
    let currentLang = 'en';
    let selectedImage = null;
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let audioBlobInfo = null; // { blob, url }
    let recordingStartTime = 0;
    let recordingInterval = null;

    // --- Initialization ---
    // CSRF Token Helper
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

    // Language Toggles
    document.querySelectorAll('.lang-opt').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.lang-opt').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentLang = btn.dataset.lang;
        });
    });

    // --- Sidebar / History Logic ---
    newChatBtn.addEventListener('click', startNewChat);

    function startNewChat() {
        currentSessionId = null;
        chatMessages.innerHTML = `
            <div class="message bot">
                <div class="message-content">
                    Hello! I'm ready for a new conversation. How can I help you?
                </div>
            </div>
        `;
        document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
        document.getElementById('chat-title').textContent = "New Conversation";
    }

    // Delegate click for history items
    historyList.addEventListener('click', (e) => {
        const item = e.target.closest('.history-item');
        if (item) {
            const sid = item.dataset.sessionId;
            loadSession(sid);
            document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        }
    });

    async function loadSession(sessionId) {
        // Show loading
        chatMessages.innerHTML = '<div class="text-center text-white-50 mt-5">Loading history...</div>';

        try {
            const res = await fetch(`/ai/history/${sessionId}/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrftoken
                }
            });
            if (res.ok) {
                const data = await res.json();
                renderMessages(data.messages);
                currentSessionId = sessionId;
            } else {
                chatMessages.innerHTML = '<div class="text-white text-center">Failed to load history</div>';
            }
        } catch (error) {
            console.error('Load session error:', error);
            chatMessages.innerHTML = '<div class="text-white text-center">Network Error</div>';
        }
    }

    function renderMessages(messages) {
        chatMessages.innerHTML = '';
        messages.forEach(msg => {
            let content = msg.text;

            if (msg.audio_url) {
                content = `<audio controls src="${msg.audio_url}" class="w-100"></audio><br><em>(Transcript): ${msg.text}</em>`;
            }
            if (msg.image_url) {
                content = `<img src="${msg.image_url}" style="max-width:200px;border-radius:10px;"><br>${msg.text}`;
            }

            addMessageToUI(content, msg.sender);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- Audio Recording Logic ---
    micBtn.addEventListener('click', startRecording);
    stopRecordBtn.addEventListener('click', stopRecording);
    discardAudioBtn.addEventListener('click', discardAudio);
    sendAudioBtn.addEventListener('click', sendAudioMessage);

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

            mediaRecorder.onstop = () => {
                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                const url = URL.createObjectURL(blob);
                audioBlobInfo = { blob, url };

                // Show Review UI
                audioPreviewPlayer.src = url;
                recordingUI.classList.add('d-none');
                audioReviewUI.classList.remove('d-none');
            };

            mediaRecorder.start();
            isRecording = true;

            // UI Toggle
            standardInputs.classList.remove('d-flex');
            standardInputs.classList.add('d-none');
            recordingUI.classList.remove('d-none');
            recordingUI.classList.add('d-flex');

            // Timer
            recordingStartTime = Date.now();
            updateTimer();
            recordingInterval = setInterval(updateTimer, 1000);

        } catch (err) {
            alert("Microphone access failed: " + err.message);
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            clearInterval(recordingInterval);
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    function updateTimer() {
        const diff = Math.floor((Date.now() - recordingStartTime) / 1000);
        const mins = Math.floor(diff / 60);
        const secs = diff % 60;
        recordTimer.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    function discardAudio() {
        audioBlobInfo = null;
        audioPreviewPlayer.src = '';

        // Reset UI
        audioReviewUI.classList.add('d-none');
        standardInputs.classList.add('d-flex');
        standardInputs.classList.remove('d-none');
    }

    async function sendAudioMessage() {
        if (!audioBlobInfo) return;

        // Add to UI immediately
        const audioMsg = `<audio controls src="${audioBlobInfo.url}" class="w-100"></audio>`;
        addMessageToUI(audioMsg, 'user');

        // Prepare Send
        const blobToSend = audioBlobInfo.blob;
        discardAudio(); // Reset UI immediately

        showLoading();

        const formData = new FormData();
        formData.append('audio', blobToSend, 'recording.webm');
        formData.append('language', currentLang);
        if (currentSessionId) formData.append('session_id', currentSessionId);

        try {
            const res = await fetch('/ai/voice/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            });
            const data = await res.json();
            hideLoading();

            if (res.ok) {
                addMessageToUI(data.response, 'bot');
                if (data.session_id) updateSessionState(data.session_id, data.session_title);
            } else {
                addMessageToUI("Error processing audio.", 'bot');
            }
        } catch (e) {
            hideLoading();
            addMessageToUI("Network error.", 'bot');
        }
    }

    // --- Image Upload Logic ---
    const cameraInput = document.getElementById('camera-upload');
    const cameraOption = document.getElementById('camera-option');
    const galleryOption = document.getElementById('gallery-option');

    // Handle gallery option
    if (galleryOption) {
        galleryOption.addEventListener('click', (e) => {
            e.preventDefault();
            imageInput.click();
        });
    }

    // Handle camera option
    if (cameraOption) {
        cameraOption.addEventListener('click', (e) => {
            e.preventDefault();
            cameraInput.click();
        });
    }

    // Handle image selection from gallery
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            selectedImage = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                filePreviewArea.classList.remove('d-none');
                filePreviewArea.innerHTML = `
                    <div class="position-relative d-inline-block">
                        <img src="${e.target.result}" style="max-height:100px; border-radius:10px;">
                        <button class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                                onclick="clearImage()" style="padding:0 5px;">×</button>
                    </div>`;
            };
            reader.readAsDataURL(selectedImage);
        }
    });

    // Handle image capture from camera
    if (cameraInput) {
        cameraInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                selectedImage = e.target.files[0];
                const reader = new FileReader();
                reader.onload = (e) => {
                    filePreviewArea.classList.remove('d-none');
                    filePreviewArea.innerHTML = `
                        <div class="position-relative d-inline-block">
                            <img src="${e.target.result}" style="max-height:100px; border-radius:10px;">
                            <button class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                                    onclick="clearImage()" style="padding:0 5px;">×</button>
                        </div>`;
                };
                reader.readAsDataURL(selectedImage);
            }
        });
    }

    window.clearImage = function () {
        selectedImage = null;
        imageInput.value = '';
        filePreviewArea.innerHTML = '';
        filePreviewArea.classList.add('d-none');
    }

    // --- Text Chat Logic ---
    sendBtn.addEventListener('click', sendTextMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            console.log('Enter pressed, sending message...');
            sendTextMessage();
        }
    });

    async function sendTextMessage() {
        const text = chatInput.value.trim();
        if (!text && !selectedImage) return;

        // UI Updates
        if (text) addMessageToUI(text, 'user');
        if (selectedImage) {
            const url = URL.createObjectURL(selectedImage);
            addMessageToUI(`<img src="${url}" style="max-width:200px;border-radius:10px;">`, 'user');
        }

        chatInput.value = '';
        showLoading();

        try {
            let res, data;

            if (selectedImage) {
                const formData = new FormData();
                formData.append('image', selectedImage);
                formData.append('message', text || "Describe this image");
                formData.append('language', currentLang);
                if (currentSessionId) formData.append('session_id', currentSessionId);

                res = await fetch('/ai/vision/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData
                });
                clearImage();
            } else {
                const payload = {
                    message: text,
                    language: currentLang,
                    session_id: currentSessionId
                };

                res = await fetch('/ai/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify(payload)
                });
            }

            data = await res.json();
            hideLoading();

            if (res.ok) {
                addMessageToUI(data.response, 'bot');
                if (data.session_id) updateSessionState(data.session_id, data.session_title);
            } else {
                addMessageToUI("Error: " + (data.error || "Unknown"), 'bot');
            }

        } catch (e) {
            hideLoading();
            addMessageToUI("Network error.", 'bot');
        }

        // --- Helpers ---
        function addMessageToUI(content, sender) {
            const div = document.createElement('div');
            div.classList.add('message-row', sender);

            const avatarClass = sender === 'bot' ? 'avatar-bot' : 'avatar-user';
            const icon = sender === 'bot' ? '<i class="bi bi-robot"></i>' : '<i class="bi bi-person"></i>';

            div.innerHTML = `
            <div class="message-content-wrapper">
                <div class="avatar-icon ${avatarClass}">${icon}</div>
                <div class="message-bubble">${content}</div>
            </div>
        `;

            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showLoading() {
            const div = document.createElement('div');
            div.id = 'loading-indicator';
            div.classList.add('message-row', 'bot');
            div.innerHTML = `
            <div class="message-content-wrapper">
                <div class="avatar-icon avatar-bot"><i class="bi bi-robot"></i></div>
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideLoading() {
            const loader = document.getElementById('loading-indicator');
            if (loader) loader.remove();
        }

        function renderMessages(messages) {
            chatMessages.innerHTML = '';
            messages.forEach(msg => {
                let content = msg.text;
                if (msg.audio_url) {
                    content = `<audio controls src="${msg.audio_url}" class="w-100"></audio><br><em>(Transcript): ${msg.text}</em>`;
                }
                if (msg.image_url) {
                    content = `<img src="${msg.image_url}" style="max-width:300px;border-radius:5px;"><br>${msg.text}`;
                }
                addMessageToUI(content, msg.sender);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function updateSessionState(sid, title) {
            if (currentSessionId !== sid) {
                currentSessionId = sid;
                const exists = document.querySelector(`.history-item[data-session-id="${sid}"]`);
                if (!exists) {
                    const div = document.createElement('div');
                    div.className = 'history-item active';
                    div.dataset.sessionId = sid;
                    div.innerHTML = `<i class="bi bi-chat-left-text me-2"></i> ${title || 'New Chat'}`;
                    historyList.prepend(div);

                    document.querySelectorAll('.history-item').forEach(i => {
                        if (i !== div) i.classList.remove('active');
                    });
                }
                document.getElementById('chat-title').textContent = title || 'New Chat';
            }
        }

        window.clearImage = function () {
            selectedImage = null;
            imageInput.value = '';
            filePreviewArea.innerHTML = '';
            filePreviewArea.classList.add('d-none');
        }

        // --- Text Chat Logic ---
        sendBtn.addEventListener('click', sendTextMessage);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter pressed, sending message...');
                sendTextMessage();
            }
        });

        async function sendTextMessage() {
            const text = chatInput.value.trim();
            if (!text && !selectedImage) return;

            // UI Updates
            if (text) addMessageToUI(text, 'user');
            if (selectedImage) {
                const url = URL.createObjectURL(selectedImage);
                addMessageToUI(`<img src="${url}" style="max-width:200px;border-radius:10px;">`, 'user');
            }

            chatInput.value = '';
            showLoading();

            try {
                let res, data;

                if (selectedImage) {
                    const formData = new FormData();
                    formData.append('image', selectedImage);
                    formData.append('message', text || "Describe this image");
                    formData.append('language', currentLang);
                    if (currentSessionId) formData.append('session_id', currentSessionId);

                    res = await fetch('/ai/vision/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrftoken },
                        body: formData
                    });
                    clearImage();
                } else {
                    const payload = {
                        message: text,
                        language: currentLang,
                        session_id: currentSessionId
                    };

                    res = await fetch('/ai/chat/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrftoken
                        },
                        body: JSON.stringify(payload)
                    });
                }

                data = await res.json();
                hideLoading();

                if (res.ok) {
                    addMessageToUI(data.response, 'bot');
                    if (data.session_id) updateSessionState(data.session_id, data.session_title);
                } else {
                    addMessageToUI("Error: " + (data.error || "Unknown"), 'bot');
                }

            } catch (e) {
                hideLoading();
                addMessageToUI("Network error.", 'bot');
            }

            // --- Helpers ---
            function addMessageToUI(content, sender) {
                const div = document.createElement('div');
                div.classList.add('message-row', sender);

                const avatarClass = sender === 'bot' ? 'avatar-bot' : 'avatar-user';
                const icon = sender === 'bot' ? '<i class="bi bi-robot"></i>' : '<i class="bi bi-person"></i>';

                div.innerHTML = `
            <div class="message-content-wrapper">
                <div class="avatar-icon ${avatarClass}">${icon}</div>
                <div class="message-bubble">${content}</div>
            </div>
        `;

                chatMessages.appendChild(div);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function showLoading() {
                const div = document.createElement('div');
                div.id = 'loading-indicator';
                div.classList.add('message-row', 'bot');
                div.innerHTML = `
            <div class="message-content-wrapper">
                <div class="avatar-icon avatar-bot"><i class="bi bi-robot"></i></div>
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
                chatMessages.appendChild(div);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function hideLoading() {
                const loader = document.getElementById('loading-indicator');
                if (loader) loader.remove();
            }

            function renderMessages(messages) {
                chatMessages.innerHTML = '';
                messages.forEach(msg => {
                    let content = msg.text;
                    if (msg.audio_url) {
                        content = `<audio controls src="${msg.audio_url}" class="w-100"></audio><br><em>(Transcript): ${msg.text}</em>`;
                    }
                    if (msg.image_url) {
                        content = `<img src="${msg.image_url}" style="max-width:300px;border-radius:5px;"><br>${msg.text}`;
                    }
                    addMessageToUI(content, msg.sender);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function updateSessionState(sid, title) {
                if (currentSessionId !== sid) {
                    currentSessionId = sid;
                    const exists = document.querySelector(`.history-item[data-session-id="${sid}"]`);
                    if (!exists) {
                        const div = document.createElement('div');
                        div.className = 'history-item active';
                        div.dataset.sessionId = sid;
                        div.innerHTML = `<i class="bi bi-chat-left-text me-2"></i> ${title || 'New Chat'}`;
                        historyList.prepend(div);

                        document.querySelectorAll('.history-item').forEach(i => {
                            if (i !== div) i.classList.remove('active');
                        });
                    }
                }
            }
        }

        // --- Context Menu for Chat History ---
        const contextMenu = document.getElementById('context-menu');
        let contextMenuTarget = null;
        let longPressTimer = null;

        // Right-click (desktop)
        historyList.addEventListener('contextmenu', (e) => {
            const item = e.target.closest('.history-item');
            if (item) {
                e.preventDefault();
                showContextMenu(e.clientX, e.clientY, item);
            }
        });

        // Long press (mobile)
        historyList.addEventListener('touchstart', (e) => {
            const item = e.target.closest('.history-item');
            if (item) {
                longPressTimer = setTimeout(() => {
                    const touch = e.touches[0];
                    showContextMenu(touch.clientX, touch.clientY, item);
                }, 500);
            }
        });

        historyList.addEventListener('touchend', () => {
            if (longPressTimer) clearTimeout(longPressTimer);
        });

        historyList.addEventListener('touchmove', () => {
            if (longPressTimer) clearTimeout(longPressTimer);
        });

        function showContextMenu(x, y, item) {
            contextMenuTarget = item;
            contextMenu.style.left = x + 'px';
            contextMenu.style.top = y + 'px';
            contextMenu.classList.add('show');
        }

        // Hide context menu on click outside
        document.addEventListener('click', () => {
            contextMenu.classList.remove('show');
        });

        // Rename chat
        document.getElementById('rename-chat').addEventListener('click', async () => {
            if (!contextMenuTarget) return;
            const sessionId = contextMenuTarget.dataset.sessionId;
            const currentTitle = contextMenuTarget.textContent.trim();

            const newTitle = prompt('Enter new chat name:', currentTitle);
            if (newTitle && newTitle.trim()) {
                try {
                    const res = await fetch(`/ai/history/${sessionId}/`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrftoken
                        },
                        body: JSON.stringify({ title: newTitle.trim() })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        contextMenuTarget.innerHTML = `<i class="bi bi-chat-left text-white-50 me-2"></i> ${data.title}`;
                    }
                } catch (error) {
                    console.error('Rename error:', error);
                }
            }
        });

        // Delete chat
        document.getElementById('delete-chat').addEventListener('click', async () => {
            if (!contextMenuTarget) return;
            const sessionId = contextMenuTarget.dataset.sessionId;

            if (confirm('Are you sure you want to delete this chat?')) {
                try {
                    const res = await fetch(`/ai/history/${sessionId}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': csrftoken
                        }
                    });

                    if (res.ok) {
                        contextMenuTarget.remove();
                        if (currentSessionId == sessionId) {
                            startNewChat();
                        }
                    }
                } catch (error) {
                    console.error('Delete error:', error);
                }
            }
        });
    });
