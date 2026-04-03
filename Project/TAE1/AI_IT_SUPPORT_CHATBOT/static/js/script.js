/**
 * AI IT Support Chatbot - Frontend JavaScript
 * ===========================================
 * Handles chat interface, API communication, and user interactions
 */

// ==================== GLOBAL VARIABLES ====================
let sessionId = null;
let isTyping = false;
let messageHistory = [];

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Generate or retrieve session ID
    sessionId = localStorage.getItem('chatSessionId') || generateSessionId();
    localStorage.setItem('chatSessionId', sessionId);
    
    // Set welcome message time
    document.getElementById('welcomeTime').textContent = formatTime(new Date());
    
    // Initialize event listeners
    setupEventListeners();
    
    // Load saved theme
    loadTheme();
    
    // Start chat session on server
    startServerSession();
    
    // Focus input
    document.getElementById('messageInput').focus();
    
    console.log('🤖 IT Support Chatbot initialized');
    console.log('Session ID:', sessionId);
}

function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function setupEventListeners() {
    // Message input
    const messageInput = document.getElementById('messageInput');
    
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    messageInput.addEventListener('input', function() {
        autoResizeTextarea();
        updateCharCount();
    });
    
    // Sidebar toggle
    document.getElementById('sidebarToggle').addEventListener('click', toggleSidebar);
    document.getElementById('menuBtn').addEventListener('click', toggleSidebarMobile);
    
    // Close modal on escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeTicketModal();
        }
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const menuBtn = document.getElementById('menuBtn');
        
        if (window.innerWidth <= 768 && 
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            !menuBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// ==================== API COMMUNICATION ====================

async function startServerSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_name: null,
                user_email: null
            })
        });
        
        const data = await response.json();
        if (data.success) {
            sessionId = data.session_id;
            localStorage.setItem('chatSessionId', sessionId);
        }
    } catch (error) {
        console.error('Error starting session:', error);
    }
}

async function sendMessageToBot(message) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        return {
            success: false,
            error: 'Failed to connect to server. Please try again.'
        };
    }
}

async function createSupportTicket(ticketData) {
    try {
        const response = await fetch('/api/tickets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...ticketData,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error creating ticket:', error);
        return {
            success: false,
            error: 'Failed to create ticket. Please try again.'
        };
    }
}

// ==================== MESSAGE HANDLING ====================

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Add user message to chat
    addUserMessage(message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateCharCount();
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to bot
    sendMessageToBot(message)
        .then(response => {
            hideTypingIndicator();
            
            if (response.success) {
                addBotMessage(response.response, {
                    category: response.category,
                    confidence: response.confidence
                });
                
                // If escalation required, show ticket suggestion
                if (response.escalation_required) {
                    showEscalationSuggestion();
                }
            } else {
                addBotMessage("I'm sorry, I encountered an error. Please try again or create a support ticket.");
            }
        })
        .catch(error => {
            hideTypingIndicator();
            addBotMessage("I'm having trouble connecting. Please check your internet connection and try again.");
        });
}

function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    autoResizeTextarea();
    updateCharCount();
    sendMessage();
}

function addUserMessage(message) {
    const messagesArea = document.getElementById('messagesArea');
    const time = formatTime(new Date());
    
    const messageHTML = `
        <div class="message user-message">
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">You</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-body">
                    <p>${escapeHtml(message)}</p>
                </div>
            </div>
        </div>
    `;
    
    messagesArea.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
    
    // Save to history
    messageHistory.push({ type: 'user', message, time });
}

function addBotMessage(message, metadata = {}) {
    const messagesArea = document.getElementById('messagesArea');
    const time = formatTime(new Date());
    
    // Convert newlines to HTML and format the message
    const formattedMessage = formatBotMessage(message);
    
    let metaHTML = '';
    if (metadata.category && metadata.category !== 'Unknown') {
        metaHTML += `<span class="message-category" style="font-size: 0.75rem; color: var(--text-muted); margin-right: 10px;">
            <i class="fas fa-tag"></i> ${escapeHtml(metadata.category)}
        </span>`;
    }
    
    const messageHTML = `
        <div class="message bot-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">IT Support Bot</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-body">
                    ${formattedMessage}
                </div>
                ${metaHTML ? `<div style="margin-top: 8px; border-top: 1px solid var(--border-color); padding-top: 8px;">${metaHTML}</div>` : ''}
            </div>
        </div>
    `;
    
    messagesArea.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
    
    // Save to history
    messageHistory.push({ type: 'bot', message, time, metadata });
}

function formatBotMessage(message) {
    // Convert newlines to <p> tags
    const paragraphs = message.split('\n\n');
    let formatted = '';
    
    paragraphs.forEach(paragraph => {
        paragraph = paragraph.trim();
        if (!paragraph) return;
        
        // Check if it's a list item
        if (paragraph.startsWith('•') || paragraph.startsWith('-') || /^\d+\./.test(paragraph)) {
            const lines = paragraph.split('\n');
            const isOrdered = /^\d+\./.test(lines[0]);
            const listTag = isOrdered ? 'ol' : 'ul';
            
            formatted += `<${listTag}>`;
            lines.forEach(line => {
                const cleanLine = line.replace(/^[•\-\d.\s]+/, '').trim();
                if (cleanLine) {
                    formatted += `<li>${escapeHtml(cleanLine)}</li>`;
                }
            });
            formatted += `</${listTag}>`;
        } else {
            formatted += `<p>${escapeHtml(paragraph)}</p>`;
        }
    });
    
    return formatted;
}

function showTypingIndicator() {
    isTyping = true;
    document.getElementById('typingIndicator').style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    isTyping = false;
    document.getElementById('typingIndicator').style.display = 'none';
}

function showEscalationSuggestion() {
    setTimeout(() => {
        addBotMessage("Would you like to create a support ticket for further assistance? Click the ticket icon above or type 'create ticket'.");
    }, 500);
}

// ==================== TICKET FORM ====================

function showTicketForm() {
    document.getElementById('ticketModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.remove('active');
    document.body.style.overflow = '';
    document.getElementById('ticketForm').reset();
}

async function submitTicket() {
    const name = document.getElementById('ticketName').value.trim();
    const email = document.getElementById('ticketEmail').value.trim();
    const category = document.getElementById('ticketCategory').value;
    const priority = document.getElementById('ticketPriority').value;
    const description = document.getElementById('ticketDescription').value.trim();
    
    // Validation
    if (!name || !email || !description) {
        showToast('Please fill in all required fields', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return;
    }
    
    // Show loading
    showLoading(true);
    
    const result = await createSupportTicket({
        name,
        email,
        category,
        priority,
        issue_description: description
    });
    
    showLoading(false);
    
    if (result.success) {
        closeTicketModal();
        showToast(`Ticket ${result.ticket_number} created successfully!`);
        
        // Add confirmation message in chat
        setTimeout(() => {
            addBotMessage(`✅ Your support ticket has been created successfully!\n\n**Ticket Number:** ${result.ticket_number}\n\nOur IT team will review your request and contact you within 24 hours. You can reference this ticket number for any follow-up inquiries.`);
        }, 300);
    } else {
        showToast(result.error || 'Failed to create ticket', 'error');
    }
}

// ==================== UI HELPERS ====================

function scrollToBottom() {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function updateCharCount() {
    const textarea = document.getElementById('messageInput');
    const count = textarea.value.length;
    const max = 500;
    const counter = document.getElementById('charCount');
    
    counter.textContent = `${count}/${max}`;
    
    if (count > max * 0.9) {
        counter.style.color = 'var(--danger)';
    } else {
        counter.style.color = 'var(--text-muted)';
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

function toggleSidebarMobile() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function startNewChat() {
    // Clear messages area except welcome message
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.innerHTML = `
        <div class="message bot-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">IT Support Bot</span>
                    <span class="message-time">${formatTime(new Date())}</span>
                </div>
                <div class="message-body">
                    <p>Hello! 👋 I'm your IT Support Assistant. How can I help you today?</p>
                </div>
            </div>
        </div>
    `;
    
    // Generate new session
    sessionId = generateSessionId();
    localStorage.setItem('chatSessionId', sessionId);
    startServerSession();
    
    // Clear history
    messageHistory = [];
    
    showToast('New chat started');
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        startNewChat();
    }
}

// ==================== THEME ====================

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update button
    const icon = document.getElementById('themeIcon');
    const text = document.getElementById('themeText');
    
    if (newTheme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        text.textContent = 'Light Mode';
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        text.textContent = 'Dark Mode';
    }
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const icon = document.getElementById('themeIcon');
    const text = document.getElementById('themeText');
    
    if (savedTheme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        text.textContent = 'Light Mode';
    }
}

// ==================== NOTIFICATIONS ====================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const icon = toast.querySelector('i');
    
    toastMessage.textContent = message;
    
    if (type === 'error') {
        toast.style.backgroundColor = 'var(--danger)';
        icon.className = 'fas fa-exclamation-circle';
    } else {
        toast.style.backgroundColor = 'var(--success)';
        icon.className = 'fas fa-check-circle';
    }
    
    toast.classList.add('active');
    
    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// ==================== UTILITY FUNCTIONS ====================

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('messageInput').focus();
    }
    
    // Ctrl/Cmd + N for new chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        startNewChat();
    }
    
    // Ctrl/Cmd + T for ticket
    if ((e.ctrlKey || e.metaKey) && e.key === 't') {
        e.preventDefault();
        showTicketForm();
    }
});

// ==================== EXPORT CHAT ====================

function exportChat() {
    if (messageHistory.length === 0) {
        showToast('No messages to export', 'error');
        return;
    }
    
    let content = `IT Support Chat - ${new Date().toLocaleString()}\n`;
    content += `Session ID: ${sessionId}\n`;
    content += '='.repeat(60) + '\n\n';
    
    messageHistory.forEach(msg => {
        content += `[${msg.time}] ${msg.type === 'user' ? 'You' : 'Bot'}:\n`;
        content += `${msg.message}\n\n`;
    });
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${sessionId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Chat exported successfully');
}

// ==================== SERVICE WORKER (for PWA) ====================

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Uncomment when service worker is implemented
        // navigator.serviceWorker.register('/static/js/sw.js');
    });
}

// ==================== CONSOLE EASTER EGG ====================

console.log('%c🤖 IT Support Chatbot', 'font-size: 24px; font-weight: bold; color: #4f46e5;');
console.log('%cBuilt with ❤️ using Flask & JavaScript', 'font-size: 14px; color: #6c757d;');
console.log('%cType help() for available commands', 'font-size: 12px; color: #10b981;');

window.help = function() {
    console.log('%cAvailable Commands:', 'font-weight: bold;');
    console.log('  startNewChat()    - Start a new chat session');
    console.log('  showTicketForm()  - Open the ticket creation form');
    console.log('  exportChat()      - Export chat history to file');
    console.log('  toggleTheme()     - Toggle dark/light mode');
    console.log('  clearChat()       - Clear current chat');
};
