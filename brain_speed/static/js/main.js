(() => {
  const state = {
    lang: 'tr',
    dark: true,
    running: false,
    tests: [],
    index: 0,
    results: [],
    currentStart: 0,
    audioCtx: null,
  };

  const i18n = {
    tr: { start: 'TESTE BAŞLA', prompt: 'Cevabı girip Enter bas.', done: 'Test tamamlandı!' },
    en: { start: 'START TEST', prompt: 'Type answer and hit Enter.', done: 'Test completed!' }
  };

  const el = id => document.getElementById(id);

  async function init() {
    registerPWA();
    populateCountries();
    wireEvents();
    setupNeuroCanvas();
    loadLeaderboard();
    setInterval(loadLeaderboard, 5000);

    if (window.gsap) {
      gsap.from('.glass', { y: 20, opacity: 0, duration: 0.5, stagger: 0.08 });
    }
  }

  function wireEvents() {
    el('startBtn').addEventListener('click', startTest);
    el('themeBtn').addEventListener('click', toggleTheme);
    el('langBtn').addEventListener('click', toggleLang);
    el('shareBtn').addEventListener('click', shareScore);
    el('exportBtn').addEventListener('click', exportScoreCard);

    el('createRoomBtn').addEventListener('click', async () => {
      const data = await Multiplayer.createRoom(getUsername(), el('country').value, state.lang);
      if (!data.ok) alert(data.error || 'Oluşturulamadı');
      else el('roomCode').value = data.roomCode;
    });

    el('joinRoomBtn').addEventListener('click', async () => {
      const data = await Multiplayer.joinRoom(getUsername(), el('roomCode').value, el('country').value, state.lang);
      if (!data.ok) alert(data.error || 'Katılım hatası');
    });

    el('readyBtn').addEventListener('click', () => Multiplayer.ready(getUsername()));
  }

  function getUsername() {
    return (el('username').value || 'guest-' + Math.floor(Math.random() * 1000)).trim().slice(0, 32);
  }

  async function startTest() {
    if (state.running) return;
    state.running = true;
    state.tests = TestEngine.generateSet(10, 1);
    state.index = 0;
    state.results = [];
    nextQuestion();
  }

  function nextQuestion() {
    const area = el('testArea');
    const timer = area.querySelector('.timer');
    if (state.index >= state.tests.length) {
      finishAll();
      return;
    }

    const q = state.tests[state.index];
    const prompt = q.html ? q.prompt : escapeHtml(q.prompt);
    area.innerHTML = `<div class="timer">000 ms</div><div class="mt-2 text-lg">${prompt}</div>
      <input id="answerInput" class="input mt-3 w-full" placeholder="${i18n[state.lang].prompt}" />`;

    if (q.reactive) {
      runReactionRound();
      return;
    }

    state.currentStart = performance.now();
    const input = el('answerInput');
    input.focus();
    input.addEventListener('keydown', (ev) => {
      if (ev.key !== 'Enter') return;
      submitAnswer(input.value, q);
    });

    const int = setInterval(() => {
      const ms = Math.floor(performance.now() - state.currentStart);
      const t = area.querySelector('.timer');
      if (!t) return clearInterval(int);
      t.textContent = `${String(ms).padStart(3, '0')} ms`;
    }, 16);
  }

  function runReactionRound() {
    const area = el('testArea');
    const wait = 500 + Math.random() * 2000;
    let active = false;
    area.innerHTML = `<div class="timer">Bekle...</div><button id="reactBtn" class="btn-neon mt-4">Dokun</button>`;
    const btn = el('reactBtn');

    const onTap = () => {
      const reactionMs = Math.max(1, performance.now() - state.currentStart);
      const correct = active;
      state.results.push({ testType: 'reaction', correct, reactionMs, accuracy: correct ? 1 : 0 });
      feedback(correct);
      state.index += 1;
      setTimeout(nextQuestion, 350);
    };

    btn.addEventListener('click', onTap, { once: true });
    btn.addEventListener('touchstart', onTap, { once: true });

    setTimeout(() => {
      active = true;
      state.currentStart = performance.now();
      area.style.background = 'rgba(22,163,74,0.2)';
      playSound(880);
      navigator.vibrate?.(30);
    }, wait);
  }

  function submitAnswer(answer, q) {
    const reactionMs = Math.max(1, performance.now() - state.currentStart);
    const normalized = String(answer).trim().toUpperCase();
    const expected = String(q.answer).trim().toUpperCase();
    const correct = normalized === expected;

    state.results.push({ testType: q.type, correct, reactionMs, accuracy: correct ? 1 : 0 });
    feedback(correct);
    state.index += 1;
    Multiplayer.progress(getUsername(), TestEngine.calculateMetrics(state.results).score);
    setTimeout(nextQuestion, 300);
  }

  function feedback(ok) {
    playSound(ok ? 740 : 180);
    navigator.vibrate?.(ok ? [20, 10, 20] : [60]);
  }

  async function finishAll() {
    state.running = false;
    const metrics = TestEngine.calculateMetrics(state.results);
    const payload = {
      username: getUsername(),
      country: el('country').value,
      lang: state.lang,
      testType: 'mixed',
      accuracy: metrics.accuracy,
      avgReactionMs: metrics.avgReactionMs,
      details: state.results
    };

    const res = await fetch('/api/submit_score', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const data = await res.json();

    el('scoreValue').textContent = String(data.score ?? metrics.score);
    el('percentileValue').textContent = `${data.percentile ?? 0}%`;
    el('brainTypeValue').textContent = data.brainType || '-';
    el('testArea').innerHTML = `<div class="timer">${Math.round(metrics.avgReactionMs)} ms</div><p>${i18n[state.lang].done}</p>`;

    Multiplayer.finish(getUsername(), Number(data.score ?? metrics.score), metrics.avgReactionMs);
  }

  async function loadLeaderboard() {
    const res = await fetch('/api/leaderboard');
    const data = await res.json();
    const list = el('leaderboard');
    list.innerHTML = data.global.slice(0, 10).map((r, i) => `
      <li class="lb-item"><span>#${i + 1} ${escapeHtml(r.username)} (${r.country})</span><span>${r.score.toFixed(2)}</span></li>
    `).join('');
  }

  function toggleTheme() {
    state.dark = !state.dark;
    document.documentElement.classList.toggle('dark', state.dark);
  }

  function toggleLang() {
    state.lang = state.lang === 'tr' ? 'en' : 'tr';
    el('startBtn').textContent = i18n[state.lang].start;
    el('subtitle').textContent = state.lang === 'tr' ? 'Beynin kaç milisaniye?' : 'How many milliseconds is your brain?';
  }

  async function populateCountries() {
    const res = await fetch('/api/countries');
    const data = await res.json();
    el('country').innerHTML = data.countries.map(c => `<option value="${c}">${c}</option>`).join('');
  }

  async function shareScore() {
    const txt = `🧠 Benim beynim ${el('scoreValue').textContent} puan! #BeynimKaçMS`;
    const url = location.href;
    if (navigator.share) {
      await navigator.share({ title: 'Düşünce Hızı Testi', text: txt, url });
    } else {
      window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(txt + ' ' + url)}`, '_blank');
    }
  }

  function exportScoreCard() {
    const canvas = document.createElement('canvas');
    canvas.width = 1080; canvas.height = 1080;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#020617'; ctx.fillRect(0, 0, 1080, 1080);
    ctx.fillStyle = '#00f0ff'; ctx.font = 'bold 72px sans-serif';
    ctx.fillText('Düşünce Hızı Testi', 110, 180);
    ctx.fillStyle = '#e2e8f0'; ctx.font = '56px monospace';
    ctx.fillText(`Skor: ${el('scoreValue').textContent}`, 150, 380);
    ctx.fillText(`Percentile: ${el('percentileValue').textContent}`, 150, 500);
    ctx.fillText(`Profil: ${el('brainTypeValue').textContent}`, 150, 620);

    const link = document.createElement('a');
    link.download = 'beyin-skor-karti.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  function playSound(freq) {
    state.audioCtx = state.audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const osc = state.audioCtx.createOscillator();
    const gain = state.audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.value = freq;
    gain.gain.value = 0.03;
    osc.connect(gain); gain.connect(state.audioCtx.destination);
    osc.start();
    setTimeout(() => osc.stop(), 100);
  }

  function setupNeuroCanvas() {
    const canvas = el('neuroCanvas');
    const ctx = canvas.getContext('2d');
    const particles = Array.from({ length: 90 }, () => ({
      x: Math.random() * innerWidth, y: Math.random() * innerHeight,
      vx: (Math.random() - 0.5) * 1.2, vy: (Math.random() - 0.5) * 1.2,
      r: Math.random() * 2 + 1,
    }));

    const resize = () => { canvas.width = innerWidth; canvas.height = innerHeight; };
    addEventListener('resize', resize); resize();

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.fillStyle = 'rgba(0,240,255,0.7)';
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(render);
    };
    render();
  }

  function registerPWA() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js').catch(console.error);
    }
  }

  function escapeHtml(txt) {
    return String(txt).replace(/[&<>'"]/g, s => ({ '&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','"':'&quot;' }[s]));
  }

  document.addEventListener('DOMContentLoaded', init);
})();
