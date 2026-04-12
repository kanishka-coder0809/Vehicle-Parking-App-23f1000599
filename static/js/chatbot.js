// static/js/chatbot.js
// Modern SaaS Chatbot UI/UX Logic

document.addEventListener('DOMContentLoaded', function () {
  // --- FAB Button ---
  const fab = document.createElement('div');
  fab.id = 'chatbot-fab';
  fab.innerHTML = `<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="#fff" fill-opacity="0.08"/><path d="M10.5 19.5v-2.25c0-.414.336-.75.75-.75h9.5c.414 0 .75.336.75.75v2.25c0 1.243-1.007 2.25-2.25 2.25h-6.5a2.25 2.25 0 0 1-2.25-2.25Zm0 0V15a5.5 5.5 0 1 1 11 0v4.5" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12.5" cy="14.5" r="1" fill="#fff"/><circle cx="19.5" cy="14.5" r="1" fill="#fff"/></svg>`;
  document.body.appendChild(fab);

  // --- Chatbot Panel ---
  const panel = document.createElement('div');
  panel.id = 'chatbot-panel';
  panel.innerHTML = `
    <div id="chatbot-header">
      <div class="icon">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="#fff" fill-opacity="0.08"/><path d="M10.5 19.5v-2.25c0-.414.336-.75.75-.75h9.5c.414 0 .75.336.75.75v2.25c0 1.243-1.007 2.25-2.25 2.25h-6.5a2.25 2.25 0 0 1-2.25-2.25Zm0 0V15a5.5 5.5 0 1 1 11 0v4.5" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12.5" cy="14.5" r="1" fill="#fff"/><circle cx="19.5" cy="14.5" r="1" fill="#fff"/></svg>
      </div>
      <div class="titles">
        <div class="title">AI Parking Assistant</div>
        <div class="subtitle">Ask anything about parking</div>
      </div>
      <button class="close-btn" title="Close">&times;</button>
    </div>
    <div id="chatbot-messages"></div>
    <div id="chatbot-typing" style="display:none"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    <div id="chatbot-suggestions"></div>
    <form id="chatbot-input-area" autocomplete="off">
      <input id="chatbot-input" type="text" placeholder="Ask about parking, booking, wallet..." autocomplete="off" />
      <button id="chatbot-send-btn" type="submit" title="Send"><span style="font-size:1.3em;">&#8594;</span></button>
    </form>
  `;
  document.body.appendChild(panel);

  // --- State ---
  let open = false;
  const messagesDiv = panel.querySelector('#chatbot-messages');
  const input = panel.querySelector('#chatbot-input');
  const form = panel.querySelector('#chatbot-input-area');
  const typing = panel.querySelector('#chatbot-typing');
  const suggestionsDiv = panel.querySelector('#chatbot-suggestions');
  const closeBtn = panel.querySelector('.close-btn');

  // --- Suggestions ---
  const suggestions = [
    'Find parking',
    'My bookings',
    'Wallet balance'
  ];
  suggestionsDiv.innerHTML = suggestions.map(
    s => `<button type="button" class="chatbot-chip">${s}</button>`
  ).join('');
  suggestionsDiv.addEventListener('click', e => {
    if (e.target.classList.contains('chatbot-chip')) {
      input.value = e.target.textContent;
      input.focus();
    }
  });

  // --- FAB open/close ---
  function openPanel() {
    panel.classList.add('open');
    open = true;
    setTimeout(() => input.focus(), 350);
  }
  function closePanel() {
    panel.classList.remove('open');
    open = false;
  }
  fab.addEventListener('click', openPanel);
  closeBtn.addEventListener('click', closePanel);

  // --- Message UI ---
  function addMessage(text, who = 'bot') {
    const msg = document.createElement('div');
    msg.className = 'chatbot-msg ' + who;
    msg.textContent = text;
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // --- Typing Indicator ---
  function showTyping(show = true) {
    typing.style.display = show ? '' : 'none';
  }

  // --- Send Message ---
  async function sendMessage(text) {
    addMessage(text, 'user');
    showTyping(true);
    try {
      const res = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      setTimeout(() => {
        showTyping(false);
        addMessage(data.reply, 'bot');
      }, 600 + Math.random()*400);
    } catch (e) {
      showTyping(false);
      addMessage('Sorry, something went wrong.', 'bot');
    }
  }

  // --- Form Submit ---
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const val = input.value.trim();
    if (!val) return;
    sendMessage(val);
    input.value = '';
  });

  // --- Panel Animation (fade/slide) ---
  // (Handled by CSS transitions)

  // --- FAB Bounce on Load ---
  fab.style.animation = 'chatbot-bounce 1.2s cubic-bezier(.4,2,.6,1) 1';

  // --- ESC to close ---
  document.addEventListener('keydown', function (e) {
    if (open && e.key === 'Escape') closePanel();
  });
});
