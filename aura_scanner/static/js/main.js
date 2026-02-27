import { FaceScanner } from './face.js';
import { EnergyField } from './energy.js';
import { chakraStatusMap } from './chakra.js';
import { auraGradient, personaText } from './aura.js';
import { predictionHtml } from './prediction.js';

const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const scanBtn = document.getElementById('scanBtn');
const result = document.getElementById('result');
const chakraList = document.getElementById('chakraList');
const pred = document.getElementById('prediction');
const trendText = document.getElementById('trendText');
const journalForm = document.getElementById('journalForm');
const journalList = document.getElementById('journalList');
const timerOutput = document.getElementById('timerOutput');

const scanner = new FaceScanner(video, overlay);
const energy = new EnergyField(document.getElementById('energyCanvas'));

let timerId = null;
let timerLeft = 300;
let lastAura = null;

function renderTimer() {
  const mm = String(Math.floor(timerLeft / 60)).padStart(2, '0');
  const ss = String(timerLeft % 60).padStart(2, '0');
  timerOutput.textContent = `${mm}:${ss}`;
}

function startMeditation() {
  clearInterval(timerId);
  timerLeft = 300;
  renderTimer();
  timerId = setInterval(() => {
    timerLeft -= 1;
    renderTimer();
    if (timerLeft <= 0) clearInterval(timerId);
  }, 1000);
}

document.getElementById('meditateBtn').addEventListener('click', startMeditation);

async function fetchTrends() {
  const r = await fetch('/api/trends');
  const t = await r.json();
  trendText.textContent = t.headline;
}

function renderChakras(chakra) {
  chakraList.innerHTML = chakraStatusMap(chakra).map((c) => `
    <div class="flex items-center gap-2">
      <span class="chakra-pill" style="background:${c.color}22;color:${c.color}">${c.name}</span>
      <div class="h-2 rounded bg-white/10 flex-1 overflow-hidden">
        <div class="h-2 rounded" style="width:${c.score}%; background:${c.color}"></div>
      </div>
      <span class="text-xs">%${c.score} ${c.state}</span>
    </div>
  `).join('');
}

function persistLocalJournal(note) {
  const items = JSON.parse(localStorage.getItem('auraJournal') || '[]');
  items.unshift({ note, date: new Date().toISOString() });
  localStorage.setItem('auraJournal', JSON.stringify(items.slice(0, 30)));
}

function renderLocalJournal() {
  const items = JSON.parse(localStorage.getItem('auraJournal') || '[]');
  journalList.innerHTML = items.map((i) => `<li class="text-sm">${new Date(i.date).toLocaleString('tr-TR')}: ${i.note}</li>`).join('');
}

scanBtn.addEventListener('click', async () => {
  scanBtn.disabled = true;
  scanBtn.textContent = '10s Aura Taranıyor...';
  const started = performance.now();
  while (performance.now() - started < 10000) {
    scanner.draw();
    await new Promise((res) => setTimeout(res, 100));
  }

  const metrics = scanner.sampleFrame();
  const r = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  });
  const data = await r.json();
  lastAura = data.aura;

  result.style.background = auraGradient(data.aura.hex);
  result.innerHTML = `<h3 class="text-xl font-bold">${data.aura.name} Aura</h3>
    <p class="text-sm">${personaText(data.aura)}</p>
    <p class="text-xs mt-1">Güven skoru: ${(data.confidence * 100).toFixed(1)}%</p>`;
  renderChakras(data.chakra);
  pred.innerHTML = predictionHtml(data.prediction);
  energy.setAura(data.aura.hex);

  scanBtn.disabled = false;
  scanBtn.textContent = 'Aura Taramasını Başlat';
});

journalForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(journalForm);
  const note = fd.get('note')?.toString().trim();
  if (!note) return;

  persistLocalJournal(note);
  renderLocalJournal();

  await fetch('/api/journal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note, mood: Number(fd.get('mood') || 3), aura_key: lastAura?.key || null }),
  });
  journalForm.reset();
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/static/service-worker.js'));
}

(async function init() {
  await scanner.start();
  energy.start();
  renderLocalJournal();
  renderTimer();
  fetchTrends();
})();
