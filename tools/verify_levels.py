"""
tools/verify_levels.py - Proves every level is beatable.

Runs the REAL game logic (level.py / player.py / deception.py) headless and
uses a best-first search over held-key inputs to find a winning input
sequence for each level, then replays that sequence from a fresh reset to
confirm it. No window is opened.

    python tools/verify_levels.py          # all levels
    python tools/verify_levels.py 7 12     # selected levels
"""
import heapq
import math
import os
import sys
import time
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import TILE, FIXED_STEP, MOVE_SPEED, SOLID_KINDS  # noqa: E402
from level import Level                                      # noqa: E402
from levels_data_pro import LEVELS                               # noqa: E402

# (left, right, jump)
ACTIONS = [(0, 1, 0), (0, 1, 1), (0, 0, 0), (0, 0, 1), (1, 0, 0), (1, 0, 1)]
FRAMES_PER_ACTION = 6


def distance_field(level):
    """BFS (in tiles) from the exit through empty cells: search heuristic."""
    ex, ey = level.data["exit_gate"]
    dist = {(ex, ey): 0}
    q = deque([(ex, ey)])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if n in dist or not (0 <= n[0] < level.cols and -3 <= n[1] < level.rows):
                continue
            if level.grid.get(n) in SOLID_KINDS:
                continue
            dist[n] = dist[(c, r)] + 1
            q.append(n)
    return dist


def time_modulus(level):
    """None  -> time does not matter for the physics,
    int   -> time only matters through periodic hazards (bucket modulo LCM),
    0     -> time matters absolutely (cycles, timed triggers)."""
    rc = level.data["rule_change"]
    if rc.get("cycle") or any(e["trigger"]["type"] == "time" or e.get("pre_glitch")
                              for e in rc.get("events", [])):
        return 0
    periods = [o["period"] for o in level.obstacles]
    periods += [t["period"] for t in level.traps if t.get("mode") != "proximity"]
    if not periods and not level.traps:
        return None
    m = 1
    for p in periods:
        m = math.lcm(m, int(round(p * 10)))
    return m


def state_key(s, timed):
    p, d = s.player, s.deception
    return (int(p.x // 4), int(p.y // 4), int(p.vx // 40), int(p.vy // 80),
            p.on_ground, p.jumping, s.prev_jump, d.signature(), tuple(d.fired),
            len(d.pending), d.cycle_step,
            tuple(t is not None for t in s.trap_triggers),
            int(s.motion_timer * 20),
            (0 if timed is None else
             int(s.t * 10) if timed == 0 else int(s.t * 10) % timed))


def solve(data, time_weight, max_nodes=150000, time_limit=120.0):
    level = Level(data)
    dist = distance_field(level)
    timed = time_modulus(level)

    def h(s):
        cx, cy = s.player.center
        return dist.get((int(cx // TILE), int(cy // TILE)), 999) * TILE / MOVE_SPEED

    root = level.state.clone()
    nodes = [(root, None, None)]           # (state, parent_index, action)
    heap = [(h(root), 0, 0)]
    seen = {state_key(root, timed)}
    counter = 0
    t0 = time.time()
    while heap:
        _, _, idx = heapq.heappop(heap)
        base = nodes[idx][0]
        for a in ACTIONS:
            level.state = base.clone()
            for _ in range(FRAMES_PER_ACTION):
                level.step(FIXED_STEP, *a)
                if level.state.dead or level.state.won:
                    break
            s = level.state
            if s.dead:
                continue
            if s.won:
                path = [a]
                i = idx
                while nodes[i][1] is not None:
                    path.append(nodes[i][2])
                    i = nodes[i][1]
                return path[::-1], len(nodes)
            k = state_key(s, timed)
            if k in seen:
                continue
            seen.add(k)
            nodes.append((s, idx, a))
            counter += 1
            heapq.heappush(heap, (h(s) + time_weight * s.t, counter, len(nodes) - 1))
        if len(nodes) > max_nodes or time.time() - t0 > time_limit:
            break
    return None, len(nodes)


def replay(data, path, trace=None):
    level = Level(data)
    for a in path:
        for _ in range(FRAMES_PER_ACTION):
            level.step(FIXED_STEP, *a)
            if trace is not None:
                trace.append(level.player.center)
            if level.state.dead:
                return False, level.state.t
            if level.state.won:
                return True, level.state.t
    return False, level.state.t


def main():
    wanted = {int(a) for a in sys.argv[1:]} or {d["id"] for d in LEVELS}
    ok_all = True
    for data in LEVELS:
        if data["id"] not in wanted:
            continue
        t0 = time.time()
        # greedy first (fast); fall back to a more patient, time-aware search
        path, n = solve(data, 0.02, max_nodes=60000)
        if path is None:
            path, n = solve(data, 1.0)
        if path is None:
            ok_all = False
            print("Level %2d %-18s  NOT SOLVED  (%d nodes, %.1fs)" %
                  (data["id"], data["title"], n, time.time() - t0))
            continue
        won, t = replay(data, path)
        ok_all &= won
        print("Level %2d %-18s  %s  in-game time %5.2fs  (%d nodes, %.1fs)" %
              (data["id"], data["title"], "PASS" if won else "REPLAY FAIL", t, n,
               time.time() - t0))
    print("ALL LEVELS BEATABLE" if ok_all else "SOME LEVELS FAILED")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
