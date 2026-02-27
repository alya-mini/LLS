const el = (id) => document.getElementById(id);

function getJournal() {
  return JSON.parse(localStorage.getItem('dream_journal') || '[]');
}
function saveJournal(entry) {
  const data = [entry, ...getJournal()].slice(0, 30);
  localStorage.setItem('dream_journal', JSON.stringify(data));
  renderJournal();
}
function renderJournal() {
  const list = el('journal');
  list.innerHTML = '';
  getJournal().forEach((j) => {
    const li = document.createElement('li');
    li.textContent = `${j.date} | ${j.score}% | ${j.summary}`;
    list.appendChild(li);
  });
}

function renderAvatar(result) {
  const c = el('avatarCanvas');
  const ctx = c.getContext('2d');
  const seed = result.fate_score;
  const grad = ctx.createLinearGradient(0, 0, c.width, c.height);
  grad.addColorStop(0, `hsl(${seed * 2}, 90%, 55%)`);
  grad.addColorStop(1, `hsl(${(seed * 4) % 360}, 90%, 45%)`);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, c.width, c.height);
  for (let i = 0; i < 80; i++) {
    ctx.beginPath();
    ctx.fillStyle = `hsla(${(seed + i * 7) % 360},90%,60%,0.35)`;
    ctx.arc(Math.random() * c.width, Math.random() * c.height, 5 + Math.random() * 25, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 28px sans-serif';
  ctx.fillText(`Kader: %${result.fate_score}`, 20, 46);
}

async function analyzeDream() {
  const dream = el('dreamInput').value.trim();
  if (dream.length < 10) return alert('Rüya metni çok kısa.');
  const payload = {
    dream,
    openai_key: el('openaiKey').value.trim(),
    lang: el('langSelect').value,
    datetime: new Date().toISOString(),
  };
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) return alert(data.error || 'Analiz hatası');

  el('result').classList.remove('hidden');
  el('summary').textContent = data.summary;
  el('symbolAnalysis').textContent = data.symbol_analysis;
  el('archetypes').textContent = `Arketipler: ${(data.jung_archetypes || []).join(', ')}`;
  el('prediction').textContent = `24h Kehanet: ${data.prediction_24h}`;
  el('fateScore').textContent = `🔮 Kader skorun: %${data.fate_score}`;
  el('astro').textContent = `⭐ Astro Uyum: ${astroSummary(data.astro)}`;

  renderAvatar(data);
  setFractalEmotion(data.mood || 0.5);
  saveJournal({ date: new Date().toLocaleString(), score: data.fate_score, summary: data.summary });
}

async function loadTrends() {
  const res = await fetch('/api/trends');
  const data = await res.json();
  const ul = el('trends');
  ul.innerHTML = '';
  if (!data.top_symbols?.length) {
    ul.innerHTML = '<li>Henüz trend için yeterli veri yok.</li>';
    return;
  }
  data.top_symbols.forEach((t) => {
    const li = document.createElement('li');
    li.textContent = `${t.symbol} (${t.count}) → ${t.meaning}`;
    ul.appendChild(li);
  });
}

function setupVoice() {
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Rec) return;
  const rec = new Rec();
  rec.lang = 'tr-TR';
  rec.onresult = (e) => { el('dreamInput').value += ' ' + e.results[0][0].transcript; };
  el('voiceBtn').onclick = () => rec.start();
}

function setupShare() {
  el('shareBtn').onclick = async () => {
    const url = el('avatarCanvas').toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = `ruya-karti-${Date.now()}.png`;
    a.click();
  };
}

function setupI18n() {
  el('langSelect').addEventListener('change', async () => {
    const lang = el('langSelect').value;
    const symbols = await fetch('/api/symbols').then((r) => r.json());
    el('appTitle').textContent = `🌙 ${lang.toUpperCase()} • ${symbols.count}+ sembol`; // lightweight switch
  });
}

el('analyzeBtn').onclick = analyzeDream;
renderJournal();
setupVoice();
setupShare();
setupI18n();
loadTrends();

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/static/service-worker.js');
