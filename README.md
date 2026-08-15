# Sokoban Co-op

A 2-player cooperative Sokoban game played over the LAN in your web browser.
Two people open the same URL on their own devices (phone, tablet, laptop —
any modern browser works), get assigned a player character based on their IP
address, and work together to push all the boxes onto the goal tiles.

Everyone shares the same board. There are no per-player boxes: any player can
push any box, and you all win together when every box is on a goal.

## How it works

- A Python **Flask server** keeps the authoritative game state (walls, goals,
  boxes, player positions) in memory.
- Browsers **poll** the server (`GET /api/state`) roughly every 90 ms and send
  moves (`POST /api/move`). No websockets needed.
- **Players are identified by IP address.** The first time a device calls
  `POST /api/register`, the server assigns it a color and a spawn point. The
  same device always gets the same player. The board supports up to two
  players (one spawn each), and the level defines how many can join.
- Inactive players are **reaped after ~15 seconds** with no requests, freeing
  their slot, and everyone gets a toast notification when players join or
  leave.
- A small event log is shipped inside the state payload so clients can show
  notifications ("Player #e74c3c joined the game", "Game is full…", etc.).

### Controls

- **Swipe** on the board (mobile), **arrow keys** or **WASD** (desktop), or the
  on-screen **D-pad** (touch screens).
- **Undo** your own last move(s) with the Undo button or **Ctrl+Z**. Each
  player keeps their own undo history, so you can only undo moves *you* made
  (including pushes — the box moves back too).
- The board auto-scales to fit the viewport; on phones the side panel is
  hidden and the D-pad is pinned to the bottom.
- **Reset** and **Undo** buttons are in the top-right header.

## Getting it running on your own computer

### 1. Install Miniconda (if needed)

```bash
# Linux
curl -sL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda3
export PATH=$HOME/miniconda3/bin:$PATH
```

Newer conda versions require you to accept the channel Terms of Service
before they will create an environment:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

### 2. Create the environment and install deps

```bash
conda create -y -n sokoban python=3.11
conda activate sokoban
pip install -r requirements.txt   # just Flask
```

### 3. Run the server

```bash
./restart.sh        # or: python server.py
```

The server binds `0.0.0.0:8000` and prints its LAN address, e.g.
`Running on http://192.168.1.9:8000`. Both players open that URL on their own
devices on the same network.

## Gotchas we hit along the way

These are the real bugs/traps we encountered while building this, so you don't
have to rediscover them:

- **Flask static paths are `/static/…`.** The page loaded but stayed stuck on
  "Connecting…" because `style.css`/`game.js` were linked as relative paths
  and returned 404. They must be referenced as `/static/game.js` etc.
- **`canvas` used before assignment.** The swipe handlers referenced the
  `canvas` variable, which was only assigned at the bottom of `game.js` — the
  script threw an error and never called `register()`. Assign the canvas
  element up top.
- **`touch-action: none` vs. scrolling.** A full-screen canvas with
  `touch-action: none` blocks the page scroll, so on phones you couldn't reach
  the buttons (and swipes got eaten by the scroll gesture). Fix: scale the
  board to fit the viewport so nothing needs scrolling, pin the D-pad to the
  bottom, and hide the side panel on small screens.
- **"Game is full" with no way back.** Test players (or anyone whose tab closed
  without a graceful exit) permanently occupy spawn slots. Since the server
  keys players by IP and never removed them, a new phone got a 409 forever.
  Fixed by reaping players after ~15 s of inactivity and making the client
  auto-retry registration until a slot frees.
- **Deadlock from a non-reentrant lock.** `reap_stale()` (and `register()`)
  called `emit()` while holding the game lock, and `emit()` tried to acquire
  the same `threading.Lock` again — the server silently hung. `emit()` must
  not take the lock (callers already hold it).
- **`pkill -f` matches itself.** Killing the old server with
  `pkill -f "server.py"` matched the *shell command's own command line*, so it
  killed the restart shell instead. Use a more specific pattern or a helper
  script (`restart.sh`) that targets the exact python path.
- **`gh repo create --push` can't overwrite `origin`.** We already had
  `origin` pointing at a local bare repo. Create the GitHub repo, then add it
  as a second remote (`git remote add github <url>`) and push explicitly. Also
  run `gh auth setup-git` so plain `git push` can authenticate via the GitHub
  CLI token.

## Roadmap: more levels for deeper co-op

The current single level is deliberately small (two spawns, four boxes, four
goals) to learn the controls. The level format in `game.py` (`LEVELS`) is a
simple text grid — any new puzzle is just a few strings. Symbols:

| Char | Meaning |
|------|---------|
| `#`  | wall    |
| `G`  | goal    |
| `$`  | box     |
| `*`  | box already on a goal |
| `@`  | player spawn |

Planned level ideas that push the cooperative angle:

- **Chokepoints**: narrow corridors only one player can pass at a time, forcing
  turns and communication.
- **Staged goals**: goals behind one-way doors, so the pair must prep boxes in
  the right order.
- **Asymmetric spawns**: players start in separate, mirror-symmetric rooms
  that both must funnel boxes into a shared center.
- **More spawns**: bump `max_players` for 3–4 players on bigger boards.

Each level should keep `# boxes == # goals` and at least one spawn per
expected player, otherwise the game is un-winnable or players get locked out —
two things our validator checks and the reaper handles gracefully.
