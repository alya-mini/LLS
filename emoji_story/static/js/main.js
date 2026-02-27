/* Ana controller: speech, animation, video, db ve PWA */
(() => {
  const $ = (id) => document.getElementById(id);
  const el = {
    storyInput: $('storyInput'), titleInput: $('titleInput'), emojiOutput: $('emojiOutput'),
    recordBtn: $('recordBtn'), stopBtn: $('stopBtn'), renderBtn: $('renderBtn'),
    exportBtn: $('exportBtn'), shareBtn: $('shareBtn'), saveStoryBtn: $('saveStoryBtn'),
    timerText: $('timerText'), timerRing: $('timerRing'), langSelect: $('langSelect'),
    themeSelect: $('themeSelect'), musicTheme: $('musicTheme'), trendingList: $('trendingList'),
    installBtn: $('installBtn')
  };

  const speech = new window.EmojiSpeechEngine();
  const animator = new window.StoryAnimator($('storyCanvas'), $('lottieLayer'));
  const exporter = new window.VideoExporter($('storyCanvas'));
  let lastBlob = null;
  let deferredPrompt = null;

  const MUSIC_BASE64 = {
    epic: 'data:audio/mp3;base64,//uQxAADBQ...',
    funny: 'data:audio/mp3;base64,//uQxAADBQ...',
    calm: 'data:audio/mp3;base64,//uQxAADBQ...',
    dramatic: 'data:audio/mp3;base64,//uQxAADBQ...',
    romantic: 'data:audio/mp3;base64,//uQxAADBQ...'
  };
  const SFX = { start: new Audio('https://assets.mixkit.co/active_storage/sfx/2515/2515-preview.mp3'),
    stop: new Audio('https://assets.mixkit.co/active_storage/sfx/270/270-preview.mp3'),
    emoji: new Audio('https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3') };

  let bgAudio = null;
  function playMusic(theme) {
    if (bgAudio) { bgAudio.pause(); }
    bgAudio = new Audio(MUSIC_BASE64[theme] || MUSIC_BASE64.funny);
    bgAudio.loop = true; bgAudio.volume = 0.25; bgAudio.play().catch(() => {});
  }

  speech.onResult = ({ text, emojis }) => {
    el.storyInput.value = text;
    el.emojiOutput.textContent = emojis;
    animator.setStory(text, emojis);
    SFX.emoji.currentTime = 0; SFX.emoji.play().catch(() => {});
  };

  speech.onState = (state) => {
    if (state === 'start') SFX.start.play().catch(() => {});
    if (state === 'end') SFX.stop.play().catch(() => {});
  };

  function startCountdown(seconds = 15) {
    el.timerText.textContent = `${seconds}`;
    const intv = setInterval(() => {
      seconds -= 1;
      el.timerText.textContent = `${Math.max(seconds, 0)}`;
      if (seconds <= 0) clearInterval(intv);
    }, 1000);
  }

  async function api(path, method = 'GET', body = null) {
    const res = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : null
    });
    return res.json();
  }

  async function loadTrending() {
    const data = await api('/api/trending?limit=10');
    el.trendingList.innerHTML = '';
    (data.items || []).forEach((item) => {
      const li = document.createElement('li');
      li.textContent = `${item.emoji_sequence} ${item.title} • score:${item.trend_score}`;
      el.trendingList.appendChild(li);
    });
  }

  el.recordBtn.onclick = () => {
    speech.start();
    startCountdown(15);
    navigator.vibrate?.(60);
  };
  el.stopBtn.onclick = () => speech.stop();
  el.renderBtn.onclick = () => {
    const text = el.storyInput.value.trim();
    const emojis = speech.textToEmoji(text);
    el.emojiOutput.textContent = emojis;
    animator.setStory(text, emojis);
    gsap.fromTo('.emoji-output', { scale: 0.9 }, { scale: 1.02, yoyo: true, repeat: 1, duration: 0.2 });
  };

  el.exportBtn.onclick = async () => {
    startCountdown(15);
    lastBlob = await exporter.exportAndDownload();
    navigator.vibrate?.([40, 50, 40]);
  };

  el.shareBtn.onclick = async () => {
    if (!lastBlob) lastBlob = await exporter.record15s();
    await exporter.share(lastBlob, 'Senin hikayen emoji olunca ne olur? #EmojiStory');
  };

  el.saveStoryBtn.onclick = async () => {
    const payload = {
      title: el.titleInput.value || 'Emoji Story',
      text: el.storyInput.value,
      emoji_sequence: el.emojiOutput.textContent,
      language: el.langSelect.value.slice(0, 2),
      mood: el.musicTheme.value,
      author_name: 'WebUser',
      theme: el.musicTheme.value,
      duration_seconds: 15,
      score: Math.floor(Math.random() * 100)
    };
    const created = await api('/api/stories', 'POST', payload);
    if (created.id) {
      await api(`/api/stories/${created.id}/event`, 'POST', { event_name: 'share', meta: { source: 'manual_save' } });
      await loadTrending();
    }
  };

  el.langSelect.onchange = (e) => speech.setLanguage(e.target.value);
  el.themeSelect.onchange = (e) => document.documentElement.setAttribute('data-theme', e.target.value);
  el.musicTheme.onchange = (e) => { playMusic(e.target.value); animator.loadLottie(e.target.value); };

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
  });

  el.installBtn.onclick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
  };

  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js');

  // Mobil swipe gesture ile temayı değiştir.
  let sx = 0;
  window.addEventListener('touchstart', (e) => { sx = e.changedTouches[0].clientX; }, { passive: true });
  window.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - sx;
    if (Math.abs(dx) < 60) return;
    const order = ['dark', 'light', 'neon'];
    const idx = order.indexOf(document.documentElement.getAttribute('data-theme'));
    const next = dx > 0 ? order[(idx + 1) % order.length] : order[(idx + 2) % order.length];
    document.documentElement.setAttribute('data-theme', next);
    el.themeSelect.value = next;
  }, { passive: true });

  animator.loadLottie('funny');
  animator.playLoop();
  playMusic('funny');
  api('/api/seed', 'POST').then(loadTrending);
})();
