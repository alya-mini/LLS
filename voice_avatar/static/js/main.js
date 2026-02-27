import { VoiceEngine } from './voice.js';
import { AvatarStudio, fetchAvatars } from './avatar.js';
import { AnimationEngine } from './animation.js';
import { VideoExporter } from './video.js';

const statusEl = document.getElementById('status');
const avatarCanvas = document.getElementById('avatarCanvas');
const avatarSelect = document.getElementById('avatarSelect');
const languageSelect = document.getElementById('language');
const cameraFeed = document.getElementById('cameraFeed');

const avatarStudio = new AvatarStudio(avatarCanvas);
const voiceEngine = new VoiceEngine(statusEl);
const animationEngine = new AnimationEngine(avatarStudio, document.getElementById('waveform'));
const exporter = new VideoExporter(avatarCanvas, statusEl);

let deferredPrompt = null;
let avatars = [];

async function bootstrap() {
  const [avatarData, configData] = await Promise.all([
    fetchAvatars(),
    fetch('/api/config').then((r) => r.json()),
  ]);
  avatars = avatarData;

  avatarData.forEach((a) => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = `${a.name} (${a.style})`;
    avatarSelect.append(opt);
  });

  configData.languages.forEach((lang) => {
    const opt = document.createElement('option');
    opt.value = lang;
    opt.textContent = lang;
    languageSelect.append(opt);
  });
  languageSelect.value = 'tr-TR';

  if (avatars[0]) await avatarStudio.loadAvatar(avatars[0].model_url);
  renderTrending();
}

avatarSelect.addEventListener('change', async () => {
  const selected = avatars.find((a) => a.id === Number(avatarSelect.value));
  if (selected) await avatarStudio.loadAvatar(selected.model_url);
});

document.getElementById('startMic').addEventListener('click', async () => {
  await voiceEngine.start({
    pitch: Number(document.getElementById('pitch').value),
    speed: Number(document.getElementById('speed').value),
    emotion: document.getElementById('emotion').value,
    language: languageSelect.value,
  });
  animationEngine.start(voiceEngine, () => document.getElementById('emotion').value);
  navigator.vibrate?.(60);
});

document.getElementById('stopMic').addEventListener('click', () => {
  animationEngine.stop();
  voiceEngine.stop();
});

document.getElementById('exportVideo').addEventListener('click', async () => {
  await exporter.export15s(voiceEngine.stream);
});

document.getElementById('arToggle').addEventListener('click', async () => {
  if (cameraFeed.style.display === 'block') {
    cameraFeed.srcObject?.getTracks().forEach((t) => t.stop());
    cameraFeed.style.display = 'none';
    statusEl.textContent = 'AR modu kapalı';
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    cameraFeed.srcObject = stream;
    cameraFeed.style.display = 'block';
    statusEl.textContent = 'AR kamera aktif';
  } catch {
    statusEl.textContent = 'Kamera izni verilmedi';
  }
});

async function renderTrending() {
  const data = await fetch('/api/trending').then((r) => r.json());
  document.getElementById('trending').innerHTML = data.trending
    .map((item, i) => `<div>#${i + 1} ${item.name} - ${item.style}</div>`)
    .join('');
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
});

document.getElementById('installBtn').addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/service-worker.js');
}

bootstrap();
