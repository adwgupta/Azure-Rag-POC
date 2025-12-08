// Simple frontend JS to interact with the Azure RAG FastAPI server
// Modern, commented frontend JS for Azure RAG demo
// This script uses plain JavaScript to drive UI interactions and
// to perform API calls (or show preview/mock responses).

// Helper to get element by id
function $id(id) { return document.getElementById(id); }

// Return the configured API base URL (useful when not in preview)
function baseUrl() {
  return $id('apiBase').value.replace(/\/$/, '');
}

// Generate or reuse conversation ID per session
let conversationId = localStorage.getItem('conversationId');
if (!conversationId) {
  conversationId = 'user_' + Math.random().toString(36).substr(2, 9);
  localStorage.setItem('conversationId', conversationId);
}


// Preview mode toggle — when true we use mocked responses only
function isPreview() {
  return $id('previewMode').checked;
}

// Small UI helpers: set disabled state on a set of elements
function setDisabled(elements, disabled) {
  elements.forEach(el => { if (el) el.disabled = disabled; });
}

// Perform a fetch against the API; returns {ok, status, data, error}
async function doFetch(path, options = {}) {
  if (isPreview()) {
    // Preview mode: skip real network calls
    return { ok: false, status: 0, error: 'Preview mode — no network call' };
  }

  const url = baseUrl() + path;
  try {
    const resp = await fetch(url, options);
    const text = await resp.text();
    let data = null;
    try { data = JSON.parse(text); } catch(_) { data = text; }
    return { ok: resp.ok, status: resp.status, data };
  } catch (err) {
    return { ok: false, status: 0, error: err.toString() };
  }
}

// HEALTH CHECK: show server status or mocked preview
async function healthCheck() {
  $id('serverStatus').textContent = 'Checking...';
  if (isPreview()) {
    // Provide a quick mocked response for UI testing
    setTimeout(() => {
      $id('serverStatus').textContent = JSON.stringify({ status: 'healthy', message: 'Preview mode — no backend' }, null, 2);
    }, 250);
    return;
  }

  const r = await doFetch('/health');
  if (r.ok) {
    $id('serverStatus').textContent = JSON.stringify(r.data, null, 2);
  } else {
    $id('serverStatus').textContent = `Error (${r.status}): ${r.error || JSON.stringify(r.data)}`;
  }
}

// CREATE INDEX: triggers index creation on the backend or shows a mock
async function createIndex() {
  $id('serverStatus').textContent = 'Creating index...';
  if (isPreview()) {
    setTimeout(() => {
      $id('serverStatus').textContent = JSON.stringify({ status: 'success', message: '(preview) index created' }, null, 2);
    }, 420);
    return;
  }

  const r = await doFetch('/create-index', { method: 'POST' });
  if (r.ok) {
    $id('serverStatus').textContent = JSON.stringify(r.data, null, 2);
  } else {
    $id('serverStatus').textContent = `Error (${r.status}): ${r.error || JSON.stringify(r.data)}`;
  }
}

// INGEST: upload selected file or show preview derived metadata
async function ingestFile(fileOverride) {
  // fileOverride allows programmatic testing; by default use file input
  const fileInput = $id('fileInput');
  const file = fileOverride || (fileInput.files && fileInput.files[0]);
  if (!file) {
    $id('ingestStatus').textContent = 'Please choose a file to upload.';
    return;
  }

  const sourceName = $id('sourceName').value;
  const form = new FormData();
  form.append('file', file, file.name);
  if (sourceName) form.append('source_name', sourceName);

  // UI: disable ingest controls while working
  setDisabled([$id('ingestBtn')], true);
  $id('ingestStatus').textContent = 'Uploading...';

  if (isPreview()) {
    // Read a small sample to estimate chunk count and show a friendly preview
    const reader = new FileReader();
    reader.onload = () => {
      const sample = (reader.result || '').toString().slice(0, 800);
      setTimeout(() => {
        const mock = {
          source: sourceName || file.name,
          chunks_processed: Math.max(1, Math.min(12, Math.ceil(sample.length / 200))),
          status: 'success'
        };
        $id('ingestStatus').textContent = JSON.stringify(mock, null, 2);
        setDisabled([$id('ingestBtn')], false);
      }, 550);
    };
    reader.onerror = () => {
      $id('ingestStatus').textContent = 'Preview read failed';
      setDisabled([$id('ingestBtn')], false);
    };
    reader.readAsText(file.slice(0, 10000));
    return;
  }

  try {
    const resp = await fetch(baseUrl() + '/ingest', {
      method: 'POST',
      body: form
    });

    const json = await resp.json();
    if (resp.ok) {
      $id('ingestStatus').textContent = JSON.stringify(json, null, 2);
    } else {
      $id('ingestStatus').textContent = `Error (${resp.status}): ${JSON.stringify(json)}`;
    }
  } catch (err) {
    $id('ingestStatus').textContent = `Network error: ${err.toString()}`;
  } finally {
    setDisabled([$id('ingestBtn')], false);
  }
}


// --- Chat UI logic ---
const chatHistory = [];

function renderChat() {
  const chatArea = $id('chatArea');
  chatArea.innerHTML = '';
  chatHistory.forEach(msg => {
    if (msg.role === 'user') {
      chatArea.appendChild(renderBubbleUser(msg.content));
    } else if (msg.role === 'ai') {
      chatArea.appendChild(renderBubbleAI(msg.content, msg.sources, msg.context));
    }
  });
  // Scroll to bottom
  chatArea.scrollTop = chatArea.scrollHeight;
}

function renderBubbleUser(text) {
  const div = document.createElement('div');
  div.className = 'chat-bubble user';
  div.innerHTML = `<strong>You</strong><br>${escapeHtml(text)}`;
  return div;
}

function renderBubbleAI(answer, sources, context) {
  const div = document.createElement('div');
  div.className = 'chat-bubble ai';
  div.innerHTML = `<strong>RAG PoC</strong><br>${escapeHtml(answer || '')}`;
  if (sources && sources.length) {
    div.innerHTML += `<div class="sources"><b>Sources:</b> ${sources.map(s => `<code>${escapeHtml(s)}</code>`).join(', ')}</div>`;
  }
  if (context && context.length) {
    div.innerHTML += `<div class="context"><b>Context:</b><ul style='margin:0;padding-left:18px'>${context.map(c => `<li><b>${escapeHtml(c.source)}</b> (chunk ${c.chunk_id}): <span>${escapeHtml(c.content)}</span></li>`).join('')}</ul></div>`;
  }
  return div;
}


// QUERY: ask the backend (or show a mocked preview answer) and update chat
// Chat query
async function queryQuestion(ev) {
  if (ev) ev.preventDefault();
  const question = $id('question').value.trim();
  if (!question) return;

  chatHistory.push({ role: 'user', content: question });
  renderChat();
  $id('question').value = '';
  setDisabled([$id('queryBtn')], true);

  chatHistory.push({ role: 'ai', content: 'Thinking...', sources: [], context: [] });
  renderChat();

  if (isPreview()) {
    setTimeout(() => {
      chatHistory.pop();
      chatHistory.push({
        role: 'ai',
        content: `This is a preview answer to: "${question}".`,
        sources: ['Preview_Doc_1.txt', 'Preview_Doc_2.txt'],
        context: [
          { id: 'Preview_Doc_1_0', content: 'Sample chunk 1...', source: 'Preview_Doc_1.txt', chunk_id: 0, score: 0.98 },
          { id: 'Preview_Doc_2_1', content: 'Sample chunk 2...', source: 'Preview_Doc_2.txt', chunk_id: 1, score: 0.87 }
        ]
      });
      renderChat();
      setDisabled([$id('queryBtn')], false);
    }, 700);
    return;
  }

  try {
    // Use /chat and send conversation_id
    const r = await fetch(baseUrl() + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question, conversation_id: conversationId })
    });

    const json = await r.json();
    chatHistory.pop(); // remove "Thinking..."
    if (r.ok) chatHistory.push({ role: 'ai', content: json.answer, sources: json.sources, context: json.context || [] });
    else chatHistory.push({ role: 'ai', content: `Error (${r.status}): ${JSON.stringify(json)}` });
    renderChat();
  } catch (err) {
    chatHistory.pop();
    chatHistory.push({ role: 'ai', content: `Network error: ${err.toString()}` });
    renderChat();
  } finally {
    setDisabled([$id('queryBtn')], false);
  }
}


// Basic HTML-escape helper to avoid injection when rendering server text
function escapeHtml(s) {
  if (!s) return '';
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br/>');
}

// DRAG & DROP UX: wire drop area to the hidden file input for nice UX
function setupDropZone() {
  const drop = $id('dropZone');
  const fileInput = $id('fileInput');

  if (!drop || !fileInput) return;

  ['dragenter','dragover'].forEach(e => {
    drop.addEventListener(e, ev => {
      ev.preventDefault();
      drop.classList.add('dragover');
    });
  });
  ['dragleave','drop'].forEach(e => {
    drop.addEventListener(e, ev => {
      ev.preventDefault();
      drop.classList.remove('dragover');
    });
  });

  drop.addEventListener('drop', ev => {
    const f = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (f) {
      // set the file input's files via DataTransfer if supported
      try {
        const dt = new DataTransfer();
        dt.items.add(f);
        fileInput.files = dt.files;
      } catch (e) {
        // fallback: nothing; we will call ingestFile with file directly
      }
      ingestFile(f);
    }
  });

  // Clicking the drop zone should open file browser
  drop.addEventListener('click', () => fileInput.click());
}

// Attach event handlers on DOM ready
window.addEventListener('DOMContentLoaded', () => {
  $id('healthBtn').addEventListener('click', healthCheck);
  $id('createIndexBtn').addEventListener('click', createIndex);
  $id('ingestBtn').addEventListener('click', () => ingestFile());

  // Chat input form submit (Enter or button)
  const chatForm = document.getElementById('chatForm');
  if (chatForm) {
    chatForm.addEventListener('submit', queryQuestion);
  }

  // initialize drop zone behavior
  setupDropZone();

  // Initial render
  renderChat();
});
