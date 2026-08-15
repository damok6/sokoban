import threading
import time

WALL = '#'
GOAL = 'G'
BOX = '$'
BOX_ON_GOAL = '*'
SPAWN = '@'

PLAYER_COLORS = [
    '#e74c3c',
    '#3498db',
    '#2ecc71',
    '#f39c12',
    '#9b59b6',
    '#1abc9c',
]

LEVELS = [
    [
        "##############",
        "#............#",
        "#..$......$..#",
        "#..########..#",
        "#..########..#",
        "#............#",
        "#....GGGG....#",
        "#.@........@.#",
        "#............#",
        "#..$......$..#",
        "#............#",
        "##############",
    ],
]


class Game:
    def __init__(self, level=0):
        self.level_index = level
        rows = LEVELS[level]
        self.width = max(len(r) for r in rows)
        self.height = len(rows)
        self.walls = set()
        self.goals = set()
        self.init_boxes = set()
        self.spawns = []
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == WALL:
                    self.walls.add((x, y))
                elif ch == GOAL:
                    self.goals.add((x, y))
                elif ch == BOX:
                    self.init_boxes.add((x, y))
                elif ch == BOX_ON_GOAL:
                    self.init_boxes.add((x, y))
                    self.goals.add((x, y))
                elif ch == SPAWN:
                    self.spawns.append((x, y))

        self.players = {}
        self.player_order = []
        self.won = False
        self.lock = threading.Lock()
        self.PLAYER_TIMEOUT = 15
        self.events = []
        self.event_seq = 0
        self.reset()

    def emit(self, message):
        self.event_seq += 1
        self.events.append({'seq': self.event_seq, 'text': message})
        if len(self.events) > 50:
            self.events = self.events[-50:]

    def reset(self):
        with self.lock:
            self.boxes = set(self.init_boxes)
            self.won = False
            for pid, p in self.players.items():
                p['pos'] = list(p['spawn'])

    def register(self, pid):
        with self.lock:
            if pid in self.players:
                self.players[pid]['last_seen'] = time.time()
                return self.players[pid]
            idx = len(self.player_order)
            if idx >= len(self.spawns):
                return None
            spawn = self.spawns[idx]
            player = {
                'id': pid,
                'color': PLAYER_COLORS[idx % len(PLAYER_COLORS)],
                'spawn': list(spawn),
                'pos': list(spawn),
                'last_seen': time.time(),
            }
            self.players[pid] = player
            self.player_order.append(pid)
            self.emit(f"Player {player['color']} joined the game")
            return player

    def touch(self, pid):
        with self.lock:
            p = self.players.get(pid)
            if p is not None:
                p['last_seen'] = time.time()

    def reap_stale(self):
        now = time.time()
        with self.lock:
            stale = [pid for pid, p in self.players.items()
                     if now - p['last_seen'] > self.PLAYER_TIMEOUT]
            for pid in stale:
                self.emit(f"Player {self.players[pid]['color']} was removed (inactive)")
                del self.players[pid]
                self.player_order.remove(pid)
            return len(stale)

    def occupied_by_player(self, pos):
        return any(p['pos'] is not None and tuple(p['pos']) == pos
                   for p in self.players.values())

    def move(self, pid, dx, dy):
        with self.lock:
            if self.won:
                return False
            p = self.players.get(pid)
            if p is None or p['pos'] is None:
                return False
            x, y = p['pos']
            nx, ny = x + dx, y + dy
            target = (nx, ny)
            if target in self.walls:
                return False
            if target in self.boxes:
                bx, by = nx + dx, ny + dy
                behind = (bx, by)
                if (behind in self.walls or behind in self.boxes
                        or self.occupied_by_player(behind)):
                    return False
                self.boxes.discard(target)
                self.boxes.add(behind)
            elif self.occupied_by_player(target):
                return False
            p['pos'] = [nx, ny]
            if self.boxes and self.boxes <= self.goals:
                self.won = True
            return True

    def state(self):
        with self.lock:
            return {
                'width': self.width,
                'height': self.height,
                'walls': [list(p) for p in sorted(self.walls)],
                'goals': [list(p) for p in sorted(self.goals)],
                'boxes': [list(p) for p in sorted(self.boxes)],
                'players': [{
                    'id': pid,
                    'color': p['color'],
                    'x': p['pos'][0],
                    'y': p['pos'][1],
                } for pid, p in self.players.items() if p['pos'] is not None],
                'won': self.won,
                'max_players': len(self.spawns),
                'events': list(self.events),
            }
