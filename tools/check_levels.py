import sys
sys.stdout.reconfigure(line_buffering=True)
import heapq
from collections import deque

WALL = '#'
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def parse(rows):
    width = max(len(r) for r in rows)
    height = len(rows)
    walls, goals, boxes, spawns = set(), set(), set(), []
    for y, row in enumerate(rows):
        if len(row) != width:
            raise SystemExit(f"row {y} width {len(row)} != {width}")
        for x, ch in enumerate(row):
            if ch == WALL:
                walls.add((x, y))
            elif ch == 'G':
                goals.add((x, y))
            elif ch == '$':
                boxes.add((x, y))
            elif ch == '*':
                boxes.add((x, y)); goals.add((x, y))
            elif ch == '@':
                spawns.append((x, y))
    return width, height, walls, goals, boxes, spawns


def flood_fill(walls, start, width, height):
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if 0 <= n[0] < width and 0 <= n[1] < height and n not in walls and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


def _reachable_from(pos, boxes_set, blocked, walls):
    seen = {pos}
    q = deque([pos])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n in walls or n in boxes_set or n in blocked or n in seen:
                continue
            seen.add(n)
            q.append(n)
    return seen


def bfs_solve_1p(walls, goals, start_boxes, start_pos, limit=5_000_000, width=99, height=99):
    start = (start_pos, frozenset(start_boxes))
    seen = {start}
    q = deque([(start, 0)])
    nodes = 0
    while q:
        (pos, boxes), depth = q.popleft()
        nodes += 1
        if nodes > limit:
            return None
        if boxes and boxes <= goals:
            return depth
        x, y = pos
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            t = (nx, ny)
            if t in walls or not (0 <= nx < width and 0 <= ny < height):
                continue
            b = (nx + dx, ny + dy)
            if t in boxes:
                if b in walls or b in boxes or not (0 <= b[0] < width and 0 <= b[1] < height):
                    continue
                nboxes = boxes - {t} | {b}
            else:
                nboxes = boxes
            nxt = (t, frozenset(nboxes))
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, depth + 1))
    return None


def bfs_solve_2p(walls, goals, start_boxes, spawns, limit=50_000_000, width=99, height=99):
    """Push-based A* for two players. State = (sorted player positions, boxes),
    recorded only right after a push. Movement to a push position is BFS on the
    fly, so walking-around moves don't blow up the state space."""
    goals_list = list(goals)
    boxes0 = frozenset(start_boxes)

    def h(boxes):
        return sum(min(abs(b[0] - g[0]) + abs(b[1] - g[1]) for g in goals_list)
                   for b in boxes)

    start = (tuple(sorted(spawns)), boxes0)
    gscore = {start: 0}
    pq = [(h(boxes0), 0, start)]
    nodes = 0
    while pq:
        f, g, st = heapq.heappop(pq)
        nodes += 1
        if nodes > limit:
            return None
        (pa, pb), bs = st
        if bs and bs <= goals:
            return g
        for pusher, other in ((pa, pb), (pb, pa)):
            reach = _reachable_from(pusher, bs, {other}, walls)
            for bx, by in bs:
                for dx, dy in DIRS:
                    stand = (bx - dx, by - dy)
                    dest = (bx + dx, by + dy)
                    if stand not in reach:
                        continue
                    if dest in walls or dest in bs or dest == other:
                        continue
                    nbs = bs - {(bx, by)} | {dest}
                    npa, npb = (bx, by), other
                    if npa > npb:
                        npa, npb = npb, npa
                    nxt = (tuple(sorted((npa, npb))), frozenset(nbs))
                    ng = g + 1
                    if ng < gscore.get(nxt, 10**9):
                        gscore[nxt] = ng
                        heapq.heappush(pq, (ng + h(nbs), ng, nxt))
    return None
