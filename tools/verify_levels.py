import sys
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, '/home/damian/opencode-workspace/sokoban-worktree')
sys.path.insert(0, '/tmp/opencode')
from check_levels import parse, flood_fill, bfs_solve_1p, bfs_solve_2p
from game import LEVELS

for idx, rows in enumerate(LEVELS):
    w = max(len(r) for r in rows)
    bad = [i for i, r in enumerate(rows) if len(r) != w]
    ww, hh, walls, goals, boxes, spawns = parse(rows)
    print(f"--- L{idx} ({ww}x{hh}) boxes={len(boxes)} goals={len(goals)} spawns={len(spawns)}" +
          (f" width-errs={bad}" if bad else ""))
    if len(boxes) != len(goals):
        print("  FAIL: boxes != goals")
        continue
    floor = {(x, y) for x in range(ww) for y in range(hh) if (x, y) not in walls}
    ok = True
    for i, sp in enumerate(spawns):
        disc = floor - flood_fill(walls, sp, ww, hh)
        if disc:
            print(f"  FAIL spawn{i} unreachable: {sorted(disc)[:8]}")
            ok = False
    if not ok:
        continue
    d1 = bfs_solve_1p(walls, goals, boxes, spawns[0], width=ww, height=hh)
    d1b = bfs_solve_1p(walls, goals, boxes, spawns[1], width=ww, height=hh)
    print(f"  1p from spawn0: {d1}")
    print(f"  1p from spawn1: {d1b}")
    d2 = bfs_solve_2p(walls, goals, boxes, spawns, width=ww, height=hh)
    print(f"  2p: {d2}")
    if idx == 0:
        verdict = "1p-solvable intro" if d1 is not None else "WARN not 1p solvable"
    elif d1 is None and d1b is None and d2 is not None:
        verdict = "COOP-FORCED OK"
    elif d2 is None:
        verdict = "FAIL: 2p unsolvable"
    else:
        verdict = "not coop-forced"
    print(f"  {verdict}")
