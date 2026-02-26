window.Multiplayer = (() => {
  const socket = io();
  let roomCode = null;

  socket.on('connect', () => console.log('socket connected'));
  socket.on('room_state', (room) => renderRoom(room));
  socket.on('live_progress', payload => {
    const info = document.getElementById('roomInfo');
    if (!info) return;
    info.innerHTML = payload.players.map(p => `${p.username}: <b>${p.score.toFixed(1)}</b>`).join('<br>');
  });
  socket.on('match_started', ({ roomCode: code }) => {
    notify(`Maç başladı: ${code}`);
  });
  socket.on('match_finished', (payload) => {
    notify(`Kazanan: ${payload.winner}`);
  });

  function notify(text) {
    const info = document.getElementById('roomInfo');
    if (info) info.innerHTML = `${text}<br>${info.innerHTML}`;
  }

  function renderRoom(room) {
    roomCode = room.roomCode;
    const info = document.getElementById('roomInfo');
    if (!info) return;
    const rows = room.players.map(p => `${p.ready ? '✅' : '⏳'} ${p.username} (${p.score.toFixed(1)})`);
    info.innerHTML = `Oda: <b>${room.roomCode}</b> [${room.status}]<br>${rows.join('<br>')}`;
  }

  async function createRoom(username, country, lang) {
    const res = await fetch('/api/create_room', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, country, lang })
    });
    const data = await res.json();
    if (data.ok) {
      roomCode = data.roomCode;
      socket.emit('join_room', { roomCode, username });
    }
    return data;
  }

  async function joinRoom(username, code, country, lang) {
    const roomCode = code.toUpperCase();
    const res = await fetch('/api/join_room', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, roomCode, country, lang })
    });
    const data = await res.json();
    if (data.ok) socket.emit('join_room', { roomCode, username });
    return data;
  }

  function ready(username) {
    if (!roomCode) return;
    socket.emit('player_ready', { roomCode, username });
  }

  function progress(username, score) {
    if (!roomCode) return;
    socket.emit('match_progress', { roomCode, username, score });
  }

  function finish(username, finalScore, avgReactionMs) {
    if (!roomCode) return;
    socket.emit('finish_match', { roomCode, username, finalScore, avgReactionMs });
  }

  return { createRoom, joinRoom, ready, progress, finish };
})();
