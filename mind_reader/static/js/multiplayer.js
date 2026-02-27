window.App = window.App || {};
(() => {
  const socket = io();
  const peers = {};
  const videoGrid = document.getElementById('videoGrid');

  App.state = {
    socket,
    peers,
    mySid: null,
    roomCode: null,
    role: 'player',
    name: 'Anon',
    localStream: null,
    players: []
  };

  App.addVideo = (sid, stream, label) => {
    let card = document.getElementById(`card-${sid}`);
    if (!card) {
      card = document.createElement('div');
      card.className = 'video-card';
      card.id = `card-${sid}`;
      card.innerHTML = `<video autoplay playsinline></video><div class="video-label"></div>`;
      videoGrid.appendChild(card);
    }
    card.querySelector('video').srcObject = stream;
    card.querySelector('.video-label').textContent = label;
  };

  App.rebuildPlayers = (players) => {
    App.state.players = players;
    players.forEach(p => {
      if (p.sid !== App.state.mySid && App.state.localStream && !peers[p.sid] && App.state.role === 'player') {
        const peer = new SimplePeer({ initiator: true, trickle: false, stream: App.state.localStream });
        peer.on('signal', signal => socket.emit('signal', { target: p.sid, signal }));
        peer.on('stream', stream => App.addVideo(p.sid, stream, p.name));
        peers[p.sid] = peer;
      }
    });
  };

  socket.on('joined', data => {
    App.state.mySid = data.sid;
    App.state.roomCode = data.room_code;
    document.getElementById('status').textContent = `Durum: ${data.room_code} odasına katıldın (${data.role})`;
  });

  socket.on('join_error', d => alert(d.message));

  socket.on('room_state', data => {
    App.rebuildPlayers(data.players);
    App.refreshBoards();
  });

  socket.on('signal', ({ from, signal }) => {
    if (!peers[from]) {
      const peer = new SimplePeer({ initiator: false, trickle: false, stream: App.state.localStream || undefined });
      peer.on('signal', s => socket.emit('signal', { target: from, signal: s }));
      peer.on('stream', stream => {
        const info = App.state.players.find(p => p.sid === from);
        App.addVideo(from, stream, info?.name || 'Oyuncu');
      });
      peers[from] = peer;
    }
    peers[from].signal(signal);
  });

  socket.on('reaction', ({ from, emoji }) => {
    const card = document.getElementById(`card-${from}`) || document.getElementById(`card-${App.state.mySid}`);
    if (!card) return;
    const bubble = document.createElement('div');
    bubble.className = 'reaction-bubble';
    bubble.textContent = emoji;
    card.appendChild(bubble);
    setTimeout(() => bubble.remove(), 900);
  });

  App.joinRoom = (role='player') => {
    const room_code = document.getElementById('roomCode').value.trim().toUpperCase();
    if (!room_code) return alert('Oda kodu gir');
    App.state.role = role;
    socket.emit('join_room', { room_code, name: App.state.name, role });
  };

  App.createRoom = async () => {
    const resp = await fetch('/api/create_room', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: App.state.name })
    });
    const data = await resp.json();
    document.getElementById('roomCode').value = data.room_code;
    App.joinRoom('player');
  };
})();
