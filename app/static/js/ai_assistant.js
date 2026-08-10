// ai_assistant.js — Full AI chat functionality

document.addEventListener('DOMContentLoaded', () => {

    const chatMessages   = document.getElementById('chatMessages');
    const chatInput      = document.getElementById('chatInput');
    const sendBtn        = document.getElementById('sendBtn');
    const clearChat      = document.getElementById('clearChat');
    const historyList    = document.getElementById('historyList');

    let chatHistory = [];
    let isTyping = false;

    // ---- Sidebar toggle (reuse dashboard logic) ----
    const sidebar      = document.getElementById('sidebar');
    const sidebarToggle= document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileToggle');
    const mainContent  = document.getElementById('mainContent');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => sidebar.classList.toggle('mobile-open'));
    }

    // ---- Auto-resize textarea ----
    if (chatInput) {
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', handleSend);

    // ---- Clear chat ----
    if (clearChat) {
        clearChat.addEventListener('click', () => {
            // Save to history
            if (chatHistory.length > 1) {
                const firstUserMsg = chatHistory.find(m => m.role === 'user');
                if (firstUserMsg) addHistoryItem(firstUserMsg.content.substring(0, 40) + '...');
            }
            // Reset
            chatHistory = [];
            chatMessages.innerHTML = '';
            appendWelcomeMessage();
        });
    }

    // ---- Send message ----
    async function handleSend() {
        if (isTyping) return;
        const text = chatInput.value.trim();
        if (!text) return;

        appendUserMessage(text);
        chatHistory.push({ role: 'user', content: text });
        chatInput.value = '';
        chatInput.style.height = 'auto';

        showTyping();
        const response = await callAI(text);
        hideTyping();

        appendAIMessage(response);
        chatHistory.push({ role: 'assistant', content: response });
    }

    // ---- Append user message ----
    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user-message';
        div.innerHTML = `
            <div class="msg-avatar user-avatar-msg">U</div>
            <div class="msg-content">
                <div class="msg-bubble">${escapeHtml(text)}</div>
                <span class="msg-time">${getTime()}</span>
            </div>`;
        chatMessages.appendChild(div);
        scrollBottom();
    }

    // ---- Append AI message ----
    function appendAIMessage(text) {
        const div = document.createElement('div');
        div.className = 'message ai-message';
        div.innerHTML = `
            <div class="msg-avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-content">
                <div class="msg-bubble">${formatMarkdown(text)}</div>
                <span class="msg-time">${getTime()}</span>
            </div>`;
        chatMessages.appendChild(div);
        scrollBottom();
    }

    // ---- Typing indicator ----
    function showTyping() {
        isTyping = true;
        sendBtn.disabled = true;
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.id = 'typingIndicator';
        div.innerHTML = `
            <div class="msg-avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="typing-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>`;
        chatMessages.appendChild(div);
        scrollBottom();
    }

    function hideTyping() {
        isTyping = false;
        sendBtn.disabled = false;
        const ind = document.getElementById('typingIndicator');
        if (ind) ind.remove();
    }

    // ---- Call AI ----
    async function callAI(message) {
        try {
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                },
                body: JSON.stringify({ message, history: chatHistory.slice(-10) })
            });
            const data = await res.json();
            return data.response || data.error || 'I could not process your request. Please try again.';
        } catch (err) {
            return 'Unable to connect to the AI service. Please check your connection and try again.';
        }
    }

    // ---- Topic shortcut ----
    window.askTopic = function(message) {
        chatInput.value = message;
        handleSend();
    };

    // ---- Add to history sidebar ----
    function addHistoryItem(preview) {
        const emptyEl = historyList.querySelector('.history-empty');
        if (emptyEl) emptyEl.remove();

        const btn = document.createElement('button');
        btn.className = 'history-item';
        btn.innerHTML = `<i class="fa-regular fa-message"></i> ${escapeHtml(preview)}`;
        historyList.insertBefore(btn, historyList.firstChild);
    }

    // ---- Welcome message ----
    function appendWelcomeMessage() {
        const div = document.createElement('div');
        div.className = 'message ai-message';
        div.innerHTML = `
            <div class="msg-avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-content">
                <div class="msg-bubble">
                    <p>👋 Hello! I'm your <strong>CareBridge AI Health Assistant</strong>, powered by Google Gemini.</p>
                    <p style="margin-top:10px;">I'm here to help you with:</p>
                    <ul>
                        <li>💊 Understanding your medications</li>
                        <li>🥗 Diet and nutrition guidance</li>
                        <li>🏃 Safe exercises during recovery</li>
                        <li>⚠️ Recognizing warning signs</li>
                        <li>📅 Appointment preparation</li>
                        <li>🌍 Multilingual support</li>
                    </ul>
                    <p style="margin-top:10px;">How can I help you today?</p>
                </div>
                <span class="msg-time">Just now</span>
            </div>`;
        chatMessages.appendChild(div);
    }

    // ---- Helpers ----
    function scrollBottom() {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 50);
    }

    function getTime() {
        return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function formatMarkdown(text) {
        return text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/^### (.+)$/gm, '<h5>$1</h5>')
            .replace(/^## (.+)$/gm, '<h4>$1</h4>')
            .replace(/^# (.+)$/gm, '<h3>$1</h3>')
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
            .replace(/\n/g, '<br>');
    }
});
