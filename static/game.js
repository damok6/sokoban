const TILE = 48;
const DIRS = {
  ArrowUp: 'up', KeyW: 'up',
  ArrowDown: 'down', KeyS: 'down',
  ArrowLeft: 'left', KeyA: 'left',
  ArrowRight: 'right', KeyD: 'right',
};

let canvas = document.getElementById('board');
let ctx = canvas.getContext('2d');
let myId = null;
let state = null;
let queue = [];

function el(id) { return document.getElementById(id); }

let seenEventSeq = 0;

function notify(message, type = 'info') {
  const box = document.createElement('div');
  box.className = 'toast ' + type;
  box.textContent = message;
  el('toasts').appendChild(box);
  setTimeout(() => {
    box.style.transition = 'opacity 0.4s';
    box.style.opacity = '0';
    setTimeout(() => box.remove(), 400);
  }, 4000);
}

async function register() {
  if (myId) return;
  const res = await fetch('/api/register', { method: 'POST' });
  if (res.status === 409) {
    el('status').textContent = 'Game is full. Waiting for a free slot\u2026';
    notify('Game is full. Waiting for a free slot\u2026', 'warn');
    return;
  }
  if (!res.ok) {
    el('status').textContent = 'Could not join. Retrying\u2026';
    notify('Could not join the game. Retrying\u2026', 'error');
    return;
  }
  const data = await res.json();
  myId = data.player_id;
  el('status').textContent = 'Connected.';
}

async function poll() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) throw new Error('state ' + res.status);
    state = await res.json();
    for (const ev of state.events || []) {
      if (ev.seq > seenEventSeq) {
        seenEventSeq = ev.seq;
        notify(ev.text, ev.text.includes('removed') ? 'warn' : 'info');
      }
    }
    render();
  } catch (_) { /* server not reachable yet */ }
}

async function flushMoves() {
  if (!queue.length) return;
  const dir = queue.shift();
  await fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dir }),
  });
}

const isTouch = window.matchMedia('(pointer: coarse), (max-width: 640px)').matches;

function fit() {
  if (!state) return;
  const reserved = isTouch ? 240 : 120; // header + dpad (mobile) or header + padding (desktop)
  const availW = window.innerWidth - 16;
  const availH = window.innerHeight - reserved;
  const scale = Math.max(0.1, Math.min(availW / (state.width * TILE),
                                        availH / (state.height * TILE), 1.4));
  canvas.style.width = (state.width * TILE * scale) + 'px';
  canvas.style.height = (state.height * TILE * scale) + 'px';
  canvas.style.transformOrigin = 'top left';
}

async function undo() {
  if (!myId) return;
  const res = await fetch('/api/undo', { method: 'POST' });
  const data = await res.json();
  if (data && data.ok) {
    notify('Move undone', 'info');
  } else {
    notify('Nothing to undo', 'warn');
  }
}

function updateUndoButton() {
  const mine = state && state.players.find(p => p.id === myId);
  const btn = el('undo');
  if (mine && mine.can_undo) {
    btn.disabled = false;
  } else {
    btn.disabled = true;
  }
}

function render() {
  const w = state.width * TILE;
  const h = state.height * TILE;
  if (canvas.width !== w) canvas.width = w;
  if (canvas.height !== h) canvas.height = h;
  fit();

  ctx.fillStyle = '#10131a';
  ctx.fillRect(0, 0, w, h);

  // floor + goals
  const isWall = new Set(state.walls.map(([x, y]) => x + ',' + y));
  const isGoal = new Set(state.goals.map(([x, y]) => x + ',' + y));
  const isBox = new Set(state.boxes.map(([x, y]) => x + ',' + y));

  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      const key = x + ',' + y;
      if (isWall.has(key)) {
        ctx.fillStyle = '#3b4252';
        ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
        ctx.strokeStyle = '#4c566a';
        ctx.lineWidth = 2;
        ctx.strokeRect(x * TILE + 1, y * TILE + 1, TILE - 2, TILE - 2);
        continue;
      }
      ctx.fillStyle = '#232833';
      ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
      if (isGoal.has(key)) {
        ctx.strokeStyle = '#ebcb8b';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x * TILE + TILE / 2, y * TILE + TILE / 2, 12, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x * TILE + TILE / 2, y * TILE + TILE / 2, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#ebcb8b';
        ctx.fill();
      }
    }
  }

  // boxes
  for (const [x, y] of state.boxes) {
    const px = x * TILE, py = y * TILE;
    ctx.fillStyle = '#b48ead';
    ctx.beginPath();
    ctx.roundRect(px + 5, py + 5, TILE - 10, TILE - 10, 8);
    ctx.fill();
    ctx.strokeStyle = '#8a6280';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(px + 5, py + 5, TILE - 10, TILE - 10, 8);
    ctx.stroke();
    if (isGoal.has(x + ',' + y)) {
      ctx.strokeStyle = '#ebcb8b';
      ctx.beginPath();
      ctx.moveTo(px + 16, py + 14);
      ctx.lineTo(px + 32, py + 14);
      ctx.stroke();
    }
  }

  // players
  for (const p of state.players) {
    const px = p.x * TILE, py = p.y * TILE;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(px + TILE / 2, py + TILE / 2, 15, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.35)';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#10131a';
    ctx.font = 'bold 14px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(p.id === myId ? 'You' : 'P', px + TILE / 2, py + TILE / 2 + 1);
  }

  renderPanel();
  if (state.level !== undefined) {
    el('level').value = String(state.level);
  }
}

function renderPanel() {
  const status = el('status');
  if (state.won) {
    status.innerHTML = '<span id="win-banner">&#127881; You win!</span>';
  } else {
    const placed = state.goals.filter(([x, y]) =>
      state.boxes.some(([bx, by]) => bx === x && by === y)).length;
    status.textContent = `Boxes placed: ${placed} / ${state.goals.length}`;
  }

  const youEl = el('you');
  youEl.innerHTML = '<h2>You</h2>';
  const mine = state.players.find(p => p.id === myId);
  if (mine) {
    youEl.innerHTML += `<div class="player-row you"><span class="swatch" style="background:${mine.color}"></span><span class="name">You</span></div>`;
  } else {
    youEl.innerHTML += '<div class="player-row"><span class="name">Spectator</span></div>';
  }

  const playersEl = el('players');
  playersEl.innerHTML = '<h2>Players</h2>';
  if (!state.players.length) playersEl.innerHTML += '<div class="player-row">Nobody yet</div>';
  for (const p of state.players) {
    playersEl.innerHTML +=
      `<div class="player-row"><span class="swatch" style="background:${p.color}"></span><span class="name">${p.id === myId ? 'You' : 'Player ' + state.players.indexOf(p)}</span></div>`;
  }
  updateUndoButton();
}

async function tick() {
  if (!myId) await register();
  await flushMoves();
  await poll();
  setTimeout(tick, 90);
}

window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.code === 'KeyZ') {
    e.preventDefault();
    undo();
    return;
  }
  const dir = DIRS[e.code];
  if (!dir) return;
  e.preventDefault();
  queue.push(dir);
});

let swipeStart = null;
const SWIPE_THRESHOLD = 30;

function dirFromDelta(dx, dy) {
  if (Math.abs(dx) < SWIPE_THRESHOLD && Math.abs(dy) < SWIPE_THRESHOLD) return null;
  if (Math.abs(dx) > Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}

canvas.addEventListener('pointerdown', (e) => {
  swipeStart = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('pointermove', (e) => {
  if (!swipeStart) return;
  const dx = e.clientX - swipeStart.x;
  const dy = e.clientY - swipeStart.y;
  if (Math.abs(dx) < SWIPE_THRESHOLD && Math.abs(dy) < SWIPE_THRESHOLD) return;
  const dir = dirFromDelta(dx, dy);
  if (dir) {
    queue.push(dir);
    swipeStart = { x: e.clientX, y: e.clientY };
  }
});

canvas.addEventListener('pointerup', () => { swipeStart = null; });
canvas.addEventListener('pointerleave', () => { swipeStart = null; });
canvas.addEventListener('pointercancel', () => { swipeStart = null; });

for (const btn of document.querySelectorAll('#dpad button')) {
  const dir = btn.dataset.dir;
  btn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    queue.push(dir);
    btn.classList.add('pressed');
  });
  btn.addEventListener('pointerup', () => btn.classList.remove('pressed'));
  btn.addEventListener('pointerleave', () => btn.classList.remove('pressed'));
  btn.addEventListener('pointercancel', () => btn.classList.remove('pressed'));
}

document.getElementById('reset').addEventListener('click', async () => {
  await fetch('/api/reset', { method: 'POST' });
  poll();
});

document.getElementById('level').addEventListener('change', async (e) => {
  await fetch('/api/level', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ level: Number(e.target.value) }),
  });
  poll();
});

document.getElementById('undo').addEventListener('click', () => undo());

window.addEventListener('resize', () => { if (state) render(); });
window.addEventListener('orientationchange', () => { if (state) render(); });

register().then(() => tick());
