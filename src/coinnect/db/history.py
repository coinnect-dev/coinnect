"""
Rate history — SQLite store for corridor snapshots.

Captured every 3 minutes by the background task.
Used for sparkline charts and trend analysis.
"""

import asyncio
import gzip
import json
import logging
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, UTC
from pathlib import Path

logger = logging.getLogger(__name__)

# data/history.db relative to repo root
_REPO_ROOT = Path(__file__).parent.parent.parent.parent  # src/coinnect/db -> repo root
DB_PATH = _REPO_ROOT / "data" / "history.db"
# Rows leaving the live table are kept here as gzipped JSONL, one file per month and run.
ARCHIVE_DIR = _REPO_ROOT / "data" / "archive"

# Key corridors captured on every refresh
TRACKED_CORRIDORS = [
    ("USD", "MXN", 500),
    ("USD", "BRL", 500),
    ("USD", "ARS", 500),
    ("USD", "NGN", 500),
    ("USD", "KES", 500),
    ("USD", "GHS", 500),
    ("USD", "PHP", 500),
    ("USD", "INR", 500),
    ("USD", "IDR", 500),
    ("BTC", "USD", 1),
    ("BTC", "MXN", 1),
    ("BTC", "NGN", 1),
    ("ETH", "USD", 1),
    ("USDC", "MXN", 500),
    ("USDC", "NGN", 500),
    # Inverse corridors for dual-chart
    ("MXN", "USD", 5000),
    ("BRL", "USD", 2000),
    ("NGN", "USD", 500000),
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("PRAGMA auto_vacuum=INCREMENTAL")  # takes effect on new DBs or after VACUUM
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS rate_snapshots (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at    TEXT    NOT NULL,
                from_currency  TEXT    NOT NULL,
                to_currency    TEXT    NOT NULL,
                amount         REAL    NOT NULL,
                best_cost_pct  REAL    NOT NULL,
                best_time_min  INTEGER NOT NULL,
                they_receive   REAL    NOT NULL,
                best_via       TEXT    NOT NULL,
                routes_json    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_corridor_time
                ON rate_snapshots(from_currency, to_currency, captured_at);
            CREATE INDEX IF NOT EXISTS idx_captured_at
                ON rate_snapshots(captured_at);
        """)
    logger.info(f"History DB ready at {DB_PATH}")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _write_snapshot(from_currency: str, to_currency: str, amount: float, routes: list) -> None:
    best = routes[0]
    via = "+".join(dict.fromkeys(s.via for s in best.steps))
    conn = _connect()
    try:
        conn.execute("""
            INSERT INTO rate_snapshots
                (captured_at, from_currency, to_currency, amount,
                 best_cost_pct, best_time_min, they_receive, best_via, routes_json)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now(UTC).isoformat(),
            from_currency,
            to_currency,
            amount,
            best.total_cost_pct,
            best.total_time_minutes,
            best.they_receive,
            via,
            json.dumps([{
                "rank": r.rank,
                "label": r.label,
                "total_cost_pct": r.total_cost_pct,
                "total_time_minutes": r.total_time_minutes,
                "they_receive": r.they_receive,
                "via": "+".join(dict.fromkeys(s.via for s in r.steps)),
            } for r in routes[:5]])
        ))
        conn.commit()
    finally:
        conn.close()


async def record_snapshot(from_currency: str, to_currency: str, amount: float, routes: list) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write_snapshot, from_currency, to_currency, amount, routes)


def _normalize_ts(col: str) -> str:
    """SQLite expression to normalize ISO timestamps to comparable format.

    Stored timestamps have 'T' separator and '+00:00' suffix which breaks
    SQLite string comparisons against datetime('now'). We strip to 19 chars
    and replace 'T' with a space to match SQLite's datetime() output format.
    """
    return f"replace(substr({col}, 1, 19), 'T', ' ')"


def get_history(from_currency: str, to_currency: str, minutes_back: int = 10080) -> list[dict]:
    """Return time-series of best route for a corridor. minutes_back default = 7 days."""
    conn = _connect()
    ts = _normalize_ts("captured_at")
    try:
        rows = conn.execute(f"""
            SELECT captured_at, best_cost_pct, they_receive, best_via, best_time_min
            FROM rate_snapshots
            WHERE from_currency = ?
              AND to_currency   = ?
              AND {ts} >= datetime('now', ? || ' minutes')
            ORDER BY captured_at ASC
        """, (from_currency, to_currency, f"-{minutes_back}")).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats(from_currency: str, to_currency: str, minutes_back: int = 10080) -> dict:
    """Return min/max/avg fee for a corridor over the last N minutes."""
    conn = _connect()
    ts = _normalize_ts("captured_at")
    try:
        row = conn.execute(f"""
            SELECT
                COUNT(*)            AS points,
                MIN(best_cost_pct)  AS min_fee,
                MAX(best_cost_pct)  AS max_fee,
                AVG(best_cost_pct)  AS avg_fee,
                MIN(they_receive)   AS min_receive,
                MAX(they_receive)   AS max_receive
            FROM rate_snapshots
            WHERE from_currency = ?
              AND to_currency   = ?
              AND {ts} >= datetime('now', ? || ' minutes')
        """, (from_currency, to_currency, f"-{minutes_back}")).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_provider_history(from_currency: str, to_currency: str, minutes_back: int = 10080) -> dict:
    """
    For each snapshot, extract per-provider cost_pct from routes_json.
    Returns {provider_via: [{captured_at, cost_pct}]} for up to the top 6 providers seen.
    """
    conn = _connect()
    ts = _normalize_ts("captured_at")
    try:
        rows = conn.execute(f"""
            SELECT captured_at, routes_json
            FROM rate_snapshots
            WHERE from_currency = ?
              AND to_currency   = ?
              AND {ts} >= datetime('now', ? || ' minutes')
            ORDER BY captured_at ASC
        """, (from_currency, to_currency, f"-{minutes_back}")).fetchall()
    finally:
        conn.close()

    # Build per-provider series — keep only the cheapest route per provider per snapshot
    series: dict[str, list[dict]] = {}
    for row in rows:
        try:
            routes = json.loads(row["routes_json"])
        except Exception:
            continue
        # Deduplicate: for each base provider name, keep only cheapest route
        best_by_provider: dict[str, dict] = {}
        for r in routes:
            via = r.get("via", "")
            if not via:
                continue
            # Normalize: "Binance+Binance" and "Binance" both map to "Binance"
            base_provider = via.split("+")[0].strip()
            existing = best_by_provider.get(base_provider)
            if existing is None or r.get("total_cost_pct", 99) < existing.get("total_cost_pct", 99):
                best_by_provider[base_provider] = r

        for base_provider, r in best_by_provider.items():
            if base_provider not in series:
                series[base_provider] = []
            series[base_provider].append({
                "captured_at": row["captured_at"],
                "cost_pct": r.get("total_cost_pct", 0),
                "they_receive": r.get("they_receive", 0),
            })

    # Keep only providers with enough data points, sort by avg cost
    MIN_POINTS = 3
    filtered = {v: pts for v, pts in series.items() if len(pts) >= MIN_POINTS}
    sorted_vias = sorted(filtered, key=lambda v: sum(p["cost_pct"] for p in filtered[v]) / len(filtered[v]))
    return {v: filtered[v] for v in sorted_vias[:8]}


def get_snapshot_by_id(snapshot_id: int) -> dict | None:
    """Return a single snapshot row including full routes_json."""
    conn = _connect()
    try:
        row = conn.execute(
            """SELECT id, captured_at, from_currency, to_currency, amount,
                      best_cost_pct, best_time_min, they_receive, best_via, routes_json
               FROM rate_snapshots WHERE id = ?""",
            (snapshot_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["routes"] = json.loads(d.pop("routes_json"))
        except Exception:
            d["routes"] = []
        return d
    finally:
        conn.close()


def _archive_rows(rows: list[sqlite3.Row]) -> None:
    """Write rows to one new file per month, atomically, so a crash can't corrupt an archive."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_month[row["captured_at"][:7]].append(dict(row))
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    for month, month_rows in by_month.items():
        final = ARCHIVE_DIR / f"rate_snapshots-{month}-{run}.jsonl.gz"
        temp = final.with_suffix(".tmp")
        with gzip.open(temp, "wt") as fh:
            for row in month_rows:
                fh.write(json.dumps(row) + "\n")
        with open(temp, "rb") as fh:
            os.fsync(fh.fileno())
        os.replace(temp, final)


def compact_history(
    hourly_after_days: int = 7,
    keep_days: int = 30,
    now: datetime | None = None,
) -> int:
    """Thin rows older than a week to one per corridor-hour, drop the live table's
    rows past keep_days, and archive everything removed. Returns rows removed.
    """
    now = now or datetime.now(UTC)
    hourly_cutoff = (now - timedelta(days=hourly_after_days)).isoformat()
    keep_cutoff = (now - timedelta(days=keep_days)).isoformat()
    conn = _connect()
    try:
        rows = conn.execute("""
            SELECT * FROM rate_snapshots
            WHERE captured_at < :hourly
              AND (captured_at < :keep OR id NOT IN (
                  SELECT MIN(id) FROM rate_snapshots
                  WHERE captured_at < :hourly
                  GROUP BY from_currency, to_currency, amount, substr(captured_at, 1, 13)
              ))
        """, {"hourly": hourly_cutoff, "keep": keep_cutoff}).fetchall()
        if not rows:
            return 0
        # Archive first: a crash here can only duplicate archive rows, never lose them.
        _archive_rows(rows)
        conn.executemany("DELETE FROM rate_snapshots WHERE id = ?", ((r["id"],) for r in rows))
        conn.commit()
        conn.execute("PRAGMA incremental_vacuum").fetchall()  # only runs as rows are fetched
        return len(rows)
    finally:
        conn.close()
