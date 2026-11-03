// CTRL ALT CRAC INNOVATIONS - Interactive AI Assistant Client Widget

(function () {
  let sessionId = localStorage.getItem("cac_session_id") || "sess_" + Math.random().toString(36).substring(2, 10);
  localStorage.setItem("cac_session_id", sessionId);

  // Inject widget HTML
  const widgetHtml = `
    <div class="cac-chat-toggle" id="cacChatToggle" title="Chat with CAC AI Assistant">
      <img src="/static/images/logo.jpeg" alt="CAC Innovation" />
    </div>

    <div class="cac-chat-window" id="cacChatWindow">
      <div class="chat-header">
        <div class="chat-header-title">
          <img src="/static/images/logo.jpeg" alt="Logo" />
          <div>
            <div style="color: #fff; font-weight:700;">CAC AI Assistant</div>
            <div style="font-size:0.68rem; color:#22d3ee;">CTRL ALT CRAC INNOVATIONS</div>
          </div>
        </div>
        <button class="chat-close-btn" id="cacChatClose">&times;</button>
      </div>

      <div class="chat-messages" id="cacChatMessages">
        <div class="chat-bubble bot">
          Hello! I am your <strong>CAC AI Solution Engineer</strong>. 
          Ask me about custom ML models, document intelligence, autonomous agents, pricing estimates, or our 5-intern engineering fellowship!
        </div>
      </div>

      <div class="chat-chips">
        <button class="chat-chip" onclick="sendChatPrompt('Give me a project quote for an AI Assistant')">💡 Estimate Project Quote</button>
        <button class="chat-chip" onclick="sendChatPrompt('What services does CTRL ALT CRAC INNOVATIONS provide?')">⚙️ Services</button>
        <button class="chat-chip" onclick="sendChatPrompt('Tell me about the Intern Fellowship Program')">🎓 Intern Tracks</button>
        <button class="chat-chip" onclick="sendChatPrompt('What solutions do you offer for Healthcare?')">🏥 Healthcare AI</button>
      </div>

      <div class="chat-input-bar">
        <input type="text" id="cacChatInput" placeholder="Ask CAC Assistant..." />
        <button class="btn btn-primary btn-sm" id="cacChatSend">Send</button>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", widgetHtml);

  const toggle = document.getElementById("cacChatToggle");
  const win = document.getElementById("cacChatWindow");
  const closeBtn = document.getElementById("cacChatClose");
  const input = document.getElementById("cacChatInput");
  const sendBtn = document.getElementById("cacChatSend");
  const msgContainer = document.getElementById("cacChatMessages");

  toggle.addEventListener("click", () => {
    win.classList.toggle("open");
    if (win.classList.contains("open")) {
      input.focus();
    }
  });

  closeBtn.addEventListener("click", () => {
    win.classList.remove("open");
  });

  window.sendChatPrompt = (text) => {
    input.value = text;
    handleSendMessage();
  };

  async function handleSendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // Append user message
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerText = text;
    msgContainer.appendChild(userBubble);
    input.value = "";
    msgContainer.scrollTop = msgContainer.scrollHeight;

    // Loading indicator
    const loadingBubble = document.createElement("div");
    loadingBubble.className = "chat-bubble bot";
    loadingBubble.innerHTML = "<em>Analyzing and querying RAG knowledge base...</em>";
    msgContainer.appendChild(loadingBubble);
    msgContainer.scrollTop = msgContainer.scrollHeight;

    try {
      const res = await fetch("/api/v1/agents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          agent_code: "website_support"
        })
      });

      const data = await res.json();
      loadingBubble.remove();

      const botBubble = document.createElement("div");
      botBubble.className = "chat-bubble bot";
      
      // Simple markdown formatting for bold and lists
      let formatted = data.reply
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br/>');
        
      if (data.tool_executed) {
        formatted = `<span class="badge badge-cyan" style="font-size:0.65rem; margin-bottom:5px;">Tool Executed: ${data.tool_executed}</span><br/>` + formatted;
      }

      botBubble.innerHTML = formatted;
      msgContainer.appendChild(botBubble);
      msgContainer.scrollTop = msgContainer.scrollHeight;
    } catch (err) {
      loadingBubble.innerHTML = "⚠️ Sorry, unable to reach the AI engine right now.";
    }
  }

  sendBtn.addEventListener("click", handleSendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  });
})();
