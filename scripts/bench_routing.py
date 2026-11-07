#!/usr/bin/env python3
"""Compare the routing engine at a git ref with the working tree, on real edges.

    python scripts/bench_routing.py --capture edges.pkl     # fetch live edges once (no snapshots written)
    python scripts/bench_routing.py --edges edges.pkl --old-ref origin/main~1

Prints how many corridor/amount cases differ (raw quote, public quote, amount
range) and the CPU of one refresh's routing (TRACKED_CORRIDORS) for both,
median of N interleaved runs.
"""
from __future__ import annotations

import argparse, asyncio, dataclasses, importlib.util, pickle, random, statistics, subprocess, sys, tempfile, time
from pathlib import Path


def capture(path: str) -> None:
    import coinnect.main as m

    async def noop(*a, **k):
        return None
    m.record_snapshot = noop

    async def run():
        n = await m._refresh_once(force=True)
        pickle.dump(m._edges_store["edges"], open(path, "wb"))
        print(f"captured {n} edges to {path}")
    asyncio.run(run())


def load_old(ref: str):
    src = subprocess.run(["git", "show", f"{ref}:src/coinnect/routing/engine.py"],
                         capture_output=True, text=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp()) / "engine_old.py"
    tmp.write_text(src)
    spec = importlib.util.spec_from_file_location("engine_old", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm(q):
    d = dataclasses.asdict(q)
    d.pop("generated_at")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture")
    ap.add_argument("--edges")
    ap.add_argument("--old-ref", default="origin/main")
    ap.add_argument("--cases", type=int, default=150)
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    if a.capture:
        capture(a.capture)
        return 0
    import coinnect.main as m
    import coinnect.routing.engine as new
    old = load_old(a.old_ref)
    edges = pickle.load(open(a.edges, "rb"))
    cases = list(m.TRACKED_CORRIDORS)
    cur = sorted({e.from_currency for e in edges} & new.ROUTING_HUBS)
    rnd = random.Random(11)
    cases += [(rnd.choice(cur), rnd.choice(cur), rnd.choice([10, 100, 500, 1000, 5000, 20000])) for _ in range(a.cases)]
    bad = 0
    for f, t, amt in cases:
        o_raw = old.build_quote(edges, f, t, amt)
        o_pub, o_rng = old.build_public_quote(edges, f, t, amt)
        n_raw, n_pub, n_rng = new.build_raw_and_public_quote(edges, f, t, amt)
        bad += norm(o_raw) != norm(n_raw) or norm(o_pub) != norm(n_pub) or o_rng != n_rng
    print(f"edges={len(edges)} cases={len(cases)} differing={bad}")

    def old_refresh():
        for f, t, amt in m.TRACKED_CORRIDORS:
            old.build_quote(edges, f, t, amt)
            old.build_public_quote(edges, f, t, amt)

    def new_refresh():
        for f, t, amt in m.TRACKED_CORRIDORS:
            new.build_raw_and_public_quote(edges, f, t, amt)

    times = {"old": [], "new": []}
    for _ in range(a.runs):
        for name, fn in (("old", old_refresh), ("new", new_refresh)):
            t0 = time.process_time(); fn(); times[name].append(time.process_time() - t0)
    for k, v in times.items():
        print(f"{k}: routing per refresh median {statistics.median(v):.3f} s CPU")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
