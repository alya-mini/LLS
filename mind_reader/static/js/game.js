window.App = window.App || {};
(() => {
  const socketReady = () => App.state?.socket;
  let timer = null;
  let secs = 30;

  const refreshBoards = async () => {
    if (!App.state.roomCode) return;
    const data = await fetch(`/api/leaderboard?room=${App.state.roomCode}`).then(r => r.json());
    const render = (el, arr) => {
      el.innerHTML = arr.map((r, i) => `<li>#${i+1} ${r.player_name} — ${r.avg_score}% (${r.plays})</li>`).join('') || '<li>Henüz skor yok</li>';
    };
    render(document.getElementById('globalBoard'), data.global);
    render(document.getElementById('friendsBoard'), data.friends);

    const offline = JSON.parse(localStorage.getItem('offlineScores') || '[]');
    if (offline.length) {
      const g = document.getElementById('friendsBoard');
      g.innerHTML += `<li class="opacity-70">Offline: ${offline.map(x => x.score).join(', ')}</li>`;
    }
  };

  App.refreshBoards = refreshBoards;

  const startRound = () => {
    secs = 30;
    document.getElementById('status').textContent = `Durum: ${document.getElementById('category').value} düşün!`;
    clearInterval(timer);
    timer = setInterval(() => {
      secs -= 1;
      document.getElementById('timer').textContent = secs;
      if (secs <= 0) {
        clearInterval(timer);
        App.state.socket.emit('thought_data', {
          room_code: App.state.roomCode,
          emotion: App.currentEmotion,
          pupil: App.currentPupil,
          timing: Date.now() / 1000
        });
      }
    }, 1000);
  };

  const submitRound = () => {
    if (!App.state.roomCode) return;
    const category = document.getElementById('category').value;
    App.state.socket.emit('submit_round', { room_code: App.state.roomCode, category });
  };

  const bindUI = () => {
    document.getElementById('createBtn').onclick = () => {
      App.state.name = document.getElementById('playerName').value || 'Anon';
      App.createRoom();
    };
    document.getElementById('joinBtn').onclick = () => {
      App.state.name = document.getElementById('playerName').value || 'Anon';
      App.joinRoom('player');
    };
    document.getElementById('joinSpectatorBtn').onclick = () => {
      App.state.name = document.getElementById('playerName').value || 'Spectator';
      App.joinRoom('spectator');
    };
    document.getElementById('startRoundBtn').onclick = startRound;
    document.getElementById('submitRoundBtn').onclick = submitRound;

    document.querySelectorAll('.emoji-btn').forEach(btn => {
      btn.onclick = () => {
        if (!App.state.roomCode) return;
        App.state.socket.emit('reaction', { room_code: App.state.roomCode, emoji: btn.dataset.emoji });
      };
    });

    App.state.socket.on('round_result', data => {
      document.getElementById('score').textContent = `Telepati uyumu: %${data.group_score}`;
      document.getElementById('status').textContent = `${data.category} turu bitti!`;
      refreshBoards();

      const arr = JSON.parse(localStorage.getItem('offlineScores') || '[]');
      arr.push({ score: data.group_score, ts: Date.now() });
      localStorage.setItem('offlineScores', JSON.stringify(arr.slice(-20)));

      const png = App.exportEEG();
      const shareText = encodeURIComponent(`Telepati testimiz %${data.group_score} çıktı! #ZihinOkumaOyunu`);
      const a = document.createElement('a');
      a.href = `https://www.tiktok.com/upload?caption=${shareText}`;
      a.target = '_blank';
      a.textContent = 'TikTok Paylaş';
      a.className = 'underline text-green-300 ml-2';
      const box = document.getElementById('score');
      box.appendChild(a);

      const dl = document.createElement('a');
      dl.href = png;
      dl.download = `eeg-${Date.now()}.png`;
      dl.textContent = ' EEG PNG indir';
      dl.className = 'underline text-cyan-300 ml-2';
      box.appendChild(dl);
    });

    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js');
  };

  window.addEventListener('DOMContentLoaded', async () => {
    if (!socketReady()) return;
    bindUI();
    await App.setupWebcam();
    App.startEmotionLoop();
    App.startEEG();
    refreshBoards();
  });
})();
