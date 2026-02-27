import { initAgeUI } from './age.js';
import { renderTimeline } from './timeline.js';
import { runPivot } from './pivot.js';

function addBubble(role, text) {
  const log = document.getElementById('chat-log');
  const d = document.createElement('div');
  d.className = `bubble ${role}`;
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function loadGallery() {
  const data = await fetch('/api/dialogues/top').then(r => r.json());
  const gallery = document.getElementById('gallery');
  gallery.innerHTML = data.items.map(i => `<div class='small'>[${i.age}] ${i.userText.slice(0,60)} → ${i.aiText.slice(0,90)}...</div>`).join('') || 'Henüz diyalog yok.';
}

async function sendChat() {
  const age = Number(document.getElementById('age').value);
  const mood = document.getElementById('mood').value;
  const birthDate = document.getElementById('birthDate').value;
  const message = document.getElementById('message').value;
  const apiKey = document.getElementById('apiKey').value.trim();
  if (!message) return;

  addBubble('user', message);
  const started = performance.now();
  const res = await fetch('/api/chat', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ age, mood, birthDate, message, apiKey })
  });
  const data = await res.json();
  addBubble('ai', data.reply);
  document.getElementById('latency').textContent = `${Math.round(performance.now() - started)}ms`;
  renderTimeline(age);
  await runPivot(age, mood);
  await loadGallery();
}

async function saveCapsule() {
  await fetch('/api/time-capsule', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ alias: capsuleAlias.value, openYear: capsuleYear.value, message: capsuleMsg.value })
  });
  alert('Zaman kapsülü kaydedildi!');
}

window.addEventListener('DOMContentLoaded', async () => {
  initAgeUI();
  renderTimeline(30);
  await runPivot(30, 'motivated');
  await loadGallery();

  sendBtn.addEventListener('click', sendChat);
  message.addEventListener('keydown', (e) => e.key === 'Enter' && sendChat());
  capsuleBtn.addEventListener('click', saveCapsule);

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js').catch(() => {});
  }
});
