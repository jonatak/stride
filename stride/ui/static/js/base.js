const chatToggle = document.getElementById('chatToggle');
const chatWidget = document.getElementById('chatWidget');
const closeChat = document.getElementById('closeChat');
const chatInput = document.getElementById('chatInput');
const sendChat = document.getElementById('sendChat');
const chatMessages = document.getElementById('chatMessages');
const streamToggle = document.getElementById('streamToggle');

if (chatToggle && chatWidget) {
  chatToggle.addEventListener('click', () => {
    chatWidget.style.display = chatWidget.style.display === 'none' ? 'flex' : 'none';
  });
}

if (closeChat && chatWidget) {
  closeChat.addEventListener('click', () => {
    chatWidget.style.display = 'none';
  });
}

function addMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${sender}`;

  if (sender === 'assistant') {
    // Parse markdown for assistant messages
    messageDiv.innerHTML = marked.parse(text);
  } else {
    messageDiv.textContent = text;
  }

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoadingAnimation() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'chat-message assistant';
  messageDiv.id = 'loading-indicator';
  messageDiv.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLoadingAnimation() {
  const loadingDiv = document.getElementById('loading-indicator');
  if (loadingDiv) {
    loadingDiv.remove();
  }
}

function showThinkingIndicator() {
  // Add a small inline thinking indicator to the current assistant bubble.
  let bubble = document.querySelector('.chat-message.assistant:last-child');
  if (!bubble) {
    bubble = document.createElement('div');
    bubble.className = 'chat-message assistant';
    chatMessages.appendChild(bubble);
  }

  // Avoid adding multiple indicators
  if (bubble.querySelector('#thinking-indicator')) return;

  const span = document.createElement('span');
  span.id = 'thinking-indicator';
  span.className = 'thinking';
  span.innerHTML = '<span></span><span></span><span></span>';
  bubble.appendChild(span);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeThinkingIndicator() {
  const t = document.getElementById('thinking-indicator');
  if (t) t.remove();
}

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  if (streamToggle && streamToggle.checked) {
    await sendMessageStream(message);
    return;
  }

  addMessage(message, 'user');
  chatInput.value = '';
  sendChat.disabled = true;

  showLoadingAnimation();

  try {
    const response = await fetch('/coach/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      removeLoadingAnimation();
      removeThinkingIndicator();
      addMessage('Error: ' + response.statusText, 'error');
      sendChat.disabled = false;
      return;
    }

    const raw = await response.text();
    let answer = raw;

    try {
      const parsed = JSON.parse(raw);
      if (typeof parsed === 'string') {
        answer = parsed;
      } else {
        answer = JSON.stringify(parsed, null, 2);
      }
    } catch (e) {
      // Keep raw text if response is not JSON.
    }

    removeLoadingAnimation();
    removeThinkingIndicator();
    addMessage(answer, 'assistant');
  } catch (error) {
    removeLoadingAnimation();
    removeThinkingIndicator();
    addMessage('Error: ' + error.message, 'error');
  }

  sendChat.disabled = false;
  chatInput.focus();
}

async function sendMessageStream(message) {
  addMessage(message, 'user');
  chatInput.value = '';
  sendChat.disabled = true;

  showLoadingAnimation();

  try {
    const response = await fetch('/coach/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      removeLoadingAnimation();
      removeThinkingIndicator();
      addMessage('Error: ' + response.statusText, 'error');
      sendChat.disabled = false;
      return;
    }

    if (!response.body) {
      removeLoadingAnimation();
      removeThinkingIndicator();
      addMessage('Error: empty response body', 'error');
      sendChat.disabled = false;
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentMessage = '';
    let currentMessageDiv = null;
    let firstEvent = true;
    let buffer = '';

    // Helper to process a single SSE event block
    function processSseEvent(block) {
      // Extract data: lines (support multi-line data:)
      const lines = block.split('\n');
      const dataLines = lines
        .map((l) => (l.startsWith('data: ') ? l.slice(6) : null))
        .filter(Boolean);
      if (dataLines.length === 0) return;

      const dataStr = dataLines.join('\n');
      let json = null;
      try {
        json = JSON.parse(dataStr);
      } catch (e) {
        console.error('Failed to parse SSE JSON:', e, dataStr);
        return;
      }

      if (json.error) {
        removeLoadingAnimation();
        removeThinkingIndicator();
        addMessage(json.error, 'error');
        return;
      }

      // Ping / thinking indicator support
      if (json.ping || json.type === 'ping' || json.status === 'thinking') {
        // Show small inline thinking dots while the model is processing
        showThinkingIndicator();
        return;
      }

      if (json.delta) {
        // remove thinking indicator when actual text arrives
        removeThinkingIndicator();

        if (firstEvent) {
          removeLoadingAnimation();
          firstEvent = false;
        }
        currentMessage += json.delta;

        if (!currentMessageDiv) {
          currentMessageDiv = document.createElement('div');
          currentMessageDiv.className = 'chat-message assistant';
          chatMessages.appendChild(currentMessageDiv);
        }

        // Render accumulated markdown progressively
        currentMessageDiv.innerHTML = marked.parse(currentMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }

      if (json.done) {
        // stream finished; finalize
        removeThinkingIndicator();
        if (currentMessageDiv) {
          currentMessageDiv.innerHTML = marked.parse(currentMessage);
        }
      }
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        processSseEvent(part.trim());
      }
    }

    // Process any trailing event in buffer
    if (buffer.trim()) {
      processSseEvent(buffer.trim());
    }

    // Ensure loading removed
    removeLoadingAnimation();
  } catch (error) {
    removeLoadingAnimation();
    removeThinkingIndicator();
    addMessage('Error: ' + error.message, 'error');
  }

  sendChat.disabled = false;
  chatInput.focus();
}

if (sendChat) {
  sendChat.addEventListener('click', sendMessage);
}

if (chatInput) {
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
}
