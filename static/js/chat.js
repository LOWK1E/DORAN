document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const clearHistoryBtn = document.getElementById('clear-history');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');

    // Function to get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
    }

    // Add a message to the chat
    function addMessage(message, isUser  = false, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser  ? 'message-user' : 'message-bot'}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = message;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';

        // Use provided timestamp or current time
        const now = timestamp || new Date().toLocaleString();

        // Add icon based on sender
        const icon = document.createElement('i');
        icon.className = isUser  ? 'fas fa-user me-1' : 'fas fa-robot me-1';
        messageTime.appendChild(icon);

        // Add timestamp text
        const timeText = document.createTextNode(now);
        messageTime.appendChild(timeText);

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);

        // Add with animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        chatMessages.appendChild(messageDiv);

        // Trigger animation after a small delay
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease-out';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
            scrollToBottom(); // Scroll to bottom after adding the message
        }, 10);
    }

    // Send message to server and get response
    async function sendMessage(message) {
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            addMessage(data.response, false, data.timestamp);
            scrollToBottom(); // Scroll to bottom after the bot's response is added
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request. Please try again.', false);
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const message = userInput.value.trim();
        if (message) {
            // Hide the welcome message when user sends a message
            const welcomeMessage = document.querySelector('.chat-welcome');
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            addMessage(message, true); // Add user message
            sendMessage(message); // Send message to server
            userInput.value = ''; // Clear input
        }
    });

    // Handle suggestion button clicks
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const message = this.textContent.trim();

            // Hide the welcome message when a suggestion is clicked
            const welcomeMessage = document.querySelector('.chat-welcome');
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            addMessage(message, true); // Add user message
            sendMessage(message); // Send message to server
        });
    });

    // Handle clear history if the button exists
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async function() {
            if (confirm('Are you sure you want to clear your chat history?')) {
                try {
                    const response = await fetch('/clear_history', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCsrfToken()
                        }
                    });

                    if (response.ok) {
                        // Remove all messages except the welcome message
                        const welcomeMessage = document.querySelector('.chat-welcome');
                        chatMessages.innerHTML = '';
                        chatMessages.appendChild(welcomeMessage);
                    } else {
                        alert('Failed to clear history. Please try again.');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                }
            }
        });
    }

    // Scroll to bottom on load
    scrollToBottom();
});