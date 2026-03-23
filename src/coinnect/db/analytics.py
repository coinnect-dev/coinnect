"""
Analytics, provider config, and suggestions — all in one SQLite store.

search_log      → every /v1/quote call (for human + bot usage stats)
provider_config → enable/disable individual providers from the backoffice
suggestions     → community-submitted provider suggestions
suggestion_votes→ one vote per device fingerprint per suggestion
"""

import logging
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = _REPO_ROOT / "data" / "history.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ── Init ────────────────────────────────────────────────────────────────────

def init_analytics_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS search_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency   TEXT NOT NULL,
                amount        REAL NOT NULL,
                routes_found  INTEGER NOT NULL DEFAULT 0,
                api_key_prefix TEXT DEFAULT NULL,
                user_agent    TEXT DEFAULT NULL,
                source        TEXT DEFAULT 'web'
            );
            CREATE INDEX IF NOT EXISTS idx_search_ts
                ON search_log(ts);
            CREATE INDEX IF NOT EXISTS idx_search_corridor
                ON search_log(from_currency, to_currency);

            CREATE TABLE IF NOT EXISTS provider_config (
                name        TEXT PRIMARY KEY,
                enabled     INTEGER NOT NULL DEFAULT 1,
                paused_note TEXT DEFAULT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS suggestions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                url          TEXT DEFAULT NULL,
                note         TEXT DEFAULT NULL,
                fingerprint  TEXT NOT NULL,
                votes        INTEGER NOT NULL DEFAULT 1,
                status       TEXT NOT NULL DEFAULT 'open',
                admin_note   TEXT DEFAULT NULL,
                created_at   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                suggestion_id INTEGER NOT NULL,
                fingerprint   TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                PRIMARY KEY (suggestion_id, fingerprint)
            );

            CREATE TABLE IF NOT EXISTS rate_reports (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ts              TEXT NOT NULL,
                from_currency   TEXT NOT NULL,
                to_currency     TEXT NOT NULL,
                provider        TEXT NOT NULL,
                reported_rate   REAL NOT NULL,
                reported_fee_pct REAL,
                amount          REAL,
                source          TEXT DEFAULT 'web',
                fingerprint     TEXT,
                api_key_prefix  TEXT,
                verified        INTEGER DEFAULT 0,
                created_at      TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_rate_reports_corridor
                ON rate_reports(from_currency, to_currency, provider);
            CREATE INDEX IF NOT EXISTS idx_rate_reports_ts
                ON rate_reports(ts);

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                provider TEXT NOT NULL,
                reward_usd REAL NOT NULL DEFAULT 0.001,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                claimed_by TEXT,
                claimed_at TEXT,
                report_id INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_quests_status ON quests(status);
        """)
    logger.info("Analytics DB tables ready")


# ── Search logging ──────────────────────────────────────────────────────────

def log_search(
    from_currency: str,
    to_currency: str,
    amount: float,
    routes_found: int,
    api_key: str | None = None,
    user_agent: str | None = None,
    source: str = "web",
) -> None:
    """Fire-and-forget — called from background task, never blocks the response."""
    try:
        with _connect() as conn:
            conn.execute("""
                INSERT INTO search_log
                    (ts, from_currency, to_currency, amount, routes_found,
                     api_key_prefix, user_agent, source)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                datetime.now(UTC).isoformat(),
                from_currency, to_currency, amount, routes_found,
                (api_key[:8] if api_key else None),
                (user_agent[:200] if user_agent else None),
                source,
            ))
    except Exception as e:
        logger.debug(f"search_log insert failed: {e}")


# ── Provider config ─────────────────────────────────────────────────────────

_provider_cache: dict[str, bool] = {}   # name → enabled, warmed on startup
_provider_cache_loaded = False


def _load_provider_cache() -> None:
    global _provider_cache_loaded
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT name, enabled FROM provider_config").fetchall()
            for r in rows:
                _provider_cache[r["name"]] = bool(r["enabled"])
        _provider_cache_loaded = True
    except Exception as e:
        logger.warning(f"Provider config cache load failed: {e}")


def is_provider_enabled(name: str) -> bool:
    if not _provider_cache_loaded:
        _load_provider_cache()
    return _provider_cache.get(name, True)   # default: enabled


def set_provider_enabled(name: str, enabled: bool, note: str | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO provider_config (name, enabled, paused_note, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET
                enabled=excluded.enabled,
                paused_note=excluded.paused_note,
                updated_at=excluded.updated_at
        """, (name, 1 if enabled else 0, note, now))
    _provider_cache[name] = enabled
    logger.info(f"Provider '{name}' {'enabled' if enabled else 'disabled'}: {note}")


def get_all_provider_configs() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name, enabled, paused_note, updated_at FROM provider_config ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


# ── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return dashboard stats for the admin backoffice."""
    conn = _connect()
    try:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        # Today's searches
        searches_today = conn.execute(
            "SELECT COUNT(*) FROM search_log WHERE substr(ts,1,10)=?", (today,)
        ).fetchone()[0]
        # API key searches today
        api_searches_today = conn.execute(
            "SELECT COUNT(*) FROM search_log WHERE substr(ts,1,10)=? AND api_key_prefix IS NOT NULL",
            (today,)
        ).fetchone()[0]
        # Total searches
        searches_total = conn.execute("SELECT COUNT(*) FROM search_log").fetchone()[0]
        # Top corridors today
        top_corridors = conn.execute("""
            SELECT from_currency||'/'||to_currency AS corridor, COUNT(*) AS cnt
            FROM search_log WHERE substr(ts,1,10)=?
            GROUP BY corridor ORDER BY cnt DESC LIMIT 10
        """, (today,)).fetchall()
        # Searches last 7 days (daily buckets)
        daily = conn.execute("""
            SELECT substr(ts,1,10) AS day, COUNT(*) AS cnt
            FROM search_log
            WHERE ts >= datetime('now', '-7 days')
            GROUP BY day ORDER BY day ASC
        """).fetchall()
        # Active API keys (same DB file)
        keys_total = conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
        # Unique humans helped (web searches, unique user_agent)
        humans_helped = conn.execute(
            "SELECT COUNT(DISTINCT user_agent) FROM search_log WHERE source='web' AND user_agent IS NOT NULL"
        ).fetchone()[0]
        # Unique bots helped (API searches, unique api_key_prefix)
        bots_helped = conn.execute(
            "SELECT COUNT(DISTINCT api_key_prefix) FROM search_log WHERE api_key_prefix IS NOT NULL"
        ).fetchone()[0]
        return {
            "searches_today": searches_today,
            "api_searches_today": api_searches_today,
            "web_searches_today": searches_today - api_searches_today,
            "searches_total": searches_total,
            "keys_total": keys_total,
            "humans_helped": humans_helped,
            "bots_helped": bots_helped,
            "top_corridors": [dict(r) for r in top_corridors],
            "daily_searches": [dict(r) for r in daily],
            "date": today,
        }
    finally:
        conn.close()


def get_recent_searches(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT ts, from_currency, to_currency, amount, routes_found,
                   api_key_prefix, source
            FROM search_log ORDER BY ts DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Suggestions ─────────────────────────────────────────────────────────────

def create_suggestion(name: str, url: str | None, note: str | None, fingerprint: str) -> dict:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO suggestions (name, url, note, fingerprint, votes, created_at)
            VALUES (?,?,?,?,1,?)
        """, (name, url, note, fingerprint, now))
        sid = cur.lastrowid
        conn.execute(
            "INSERT INTO suggestion_votes (suggestion_id, fingerprint, created_at) VALUES (?,?,?)",
            (sid, fingerprint, now)
        )
    return {"id": sid, "name": name, "votes": 1}


def upvote_suggestion(suggestion_id: int, fingerprint: str) -> dict:
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        # Check already voted
        existing = conn.execute(
            "SELECT 1 FROM suggestion_votes WHERE suggestion_id=? AND fingerprint=?",
            (suggestion_id, fingerprint)
        ).fetchone()
        if existing:
            return {"error": "already_voted"}
        conn.execute(
            "INSERT INTO suggestion_votes (suggestion_id, fingerprint, created_at) VALUES (?,?,?)",
            (suggestion_id, fingerprint, now)
        )
        conn.execute(
            "UPDATE suggestions SET votes=votes+1 WHERE id=?", (suggestion_id,)
        )
        row = conn.execute("SELECT votes FROM suggestions WHERE id=?", (suggestion_id,)).fetchone()
        return {"id": suggestion_id, "votes": row["votes"] if row else 0}


def get_suggestions(status: str = "open") -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, name, url, note, votes, status, admin_note, created_at
            FROM suggestions WHERE status=?
            ORDER BY votes DESC, created_at DESC
        """, (status,)).fetchall()
        return [dict(r) for r in rows]


def set_suggestion_status(suggestion_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE suggestions SET status=? WHERE id=?", (status, suggestion_id))


def set_suggestion_admin_note(suggestion_id: int, note: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE suggestions SET admin_note=? WHERE id=?", (note, suggestion_id))


# ── Rate reports ───────────────────────────────────────────────────────────

def save_rate_report(
    from_c: str,
    to_c: str,
    provider: str,
    rate: float,
    fee_pct: float | None = None,
    amount: float | None = None,
    source: str = "web",
    fingerprint: str | None = None,
    api_key: str | None = None,
) -> int:
    """Save a community-reported rate observation. Returns the report id."""
    now = datetime.now(UTC).isoformat()
    try:
        with _connect() as conn:
            cur = conn.execute("""
                INSERT INTO rate_reports
                    (ts, from_currency, to_currency, provider, reported_rate,
                     reported_fee_pct, amount, source, fingerprint, api_key_prefix, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                now, from_c.upper(), to_c.upper(), provider, rate,
                fee_pct, amount, source, fingerprint,
                (api_key[:8] if api_key else None), now,
            ))
            return cur.lastrowid
    except Exception as e:
        logger.debug(f"rate_report insert failed: {e}")
        return 0


def get_rate_reports(
    from_c: str, to_c: str, provider: str, hours_back: int = 24
) -> list[dict]:
    """Return recent rate reports for a specific corridor/provider."""
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, ts, from_currency, to_currency, provider,
                   reported_rate, reported_fee_pct, amount, source, verified
            FROM rate_reports
            WHERE from_currency=? AND to_currency=? AND provider=?
              AND ts >= datetime('now', ?)
            ORDER BY ts DESC
        """, (from_c.upper(), to_c.upper(), provider, f"-{hours_back} hours")).fetchall()
        return [dict(r) for r in rows]


# ── Quests (bounty board) ──────────────────────────────────────────────────

LIVE_PROVIDERS = {
    'Binance', 'Kraken', 'Coinbase', 'OKX', 'Bybit', 'KuCoin', 'Gate', 'Bitget',
    'MEXC', 'HTX', 'Crypto.com', 'Luno', 'Bitstamp', 'Gemini', 'Bithumb', 'Bitflyer',
    'BtcTurk', 'IndependentReserve', 'WhiteBIT', 'Exmo', 'Wise', 'Buda', 'VALR',
    'CoinDCX', 'WazirX', 'SatoshiTango', 'Bitso',
}


def generate_quests() -> int:
    """
    Create quests for corridors with high search demand but only estimated providers.
    Looks at top 10 corridors from search_log (last 24h), finds ESTIMATED providers,
    creates quests where none exist. Max 20 open quests at a time.
    Returns count of quests created.
    """
    now = datetime.now(UTC).isoformat()
    created = 0
    with _connect() as conn:
        # Check current open quest count
        open_count = conn.execute(
            "SELECT COUNT(*) FROM quests WHERE status='open'"
        ).fetchone()[0]
        if open_count >= 20:
            return 0

        # Top 10 corridors by search volume in last 24h
        top = conn.execute("""
            SELECT from_currency, to_currency, COUNT(*) AS cnt
            FROM search_log
            WHERE ts >= datetime('now', '-24 hours')
            GROUP BY from_currency, to_currency
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()

        # For each corridor, look at rate_snapshots to find providers
        for row in top:
            if open_count + created >= 20:
                break
            from_c, to_c = row["from_currency"], row["to_currency"]

            # Get providers from recent snapshots' routes_json
            snaps = conn.execute("""
                SELECT routes_json FROM rate_snapshots
                WHERE from_currency=? AND to_currency=?
                ORDER BY captured_at DESC LIMIT 1
            """, (from_c, to_c)).fetchone()
            if not snaps:
                continue

            import json as _json
            try:
                routes = _json.loads(snaps["routes_json"])
            except Exception:
                continue

            for route in routes:
                if open_count + created >= 20:
                    break
                via = route.get("via", "")
                # Extract base provider name (first in chain)
                provider = via.split("+")[0].strip() if via else ""
                if not provider or provider in LIVE_PROVIDERS:
                    continue

                # Check if open quest already exists for this corridor+provider
                existing = conn.execute("""
                    SELECT 1 FROM quests
                    WHERE from_currency=? AND to_currency=? AND provider=? AND status='open'
                """, (from_c, to_c, provider)).fetchone()
                if existing:
                    continue

                conn.execute("""
                    INSERT INTO quests (from_currency, to_currency, provider, reward_usd, status, created_at)
                    VALUES (?,?,?,0.001,'open',?)
                """, (from_c, to_c, provider, now))
                created += 1

    if created:
        logger.info(f"Generated {created} new quests")
    return created


def get_open_quests(limit: int = 20) -> list[dict]:
    """Return open quests for the bounty board."""
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, from_currency, to_currency, provider, reward_usd, created_at
            FROM quests
            WHERE status='open'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def claim_quest(quest_id: int, report_id: int, claimer: str) -> bool:
    """Mark a quest as claimed, linking it to a rate report. Returns True on success."""
    now = datetime.now(UTC).isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM quests WHERE id=? AND status='open'", (quest_id,)
        ).fetchone()
        if not row:
            return False
        conn.execute("""
            UPDATE quests SET status='claimed', claimed_by=?, claimed_at=?, report_id=?
            WHERE id=?
        """, (claimer, now, report_id, quest_id))
        return True


def get_calibration_data() -> list[dict]:
    """
    Aggregate rate reports: avg reported_rate per provider/corridor
    over the last 24 hours. Used by admin to compare against estimates.
    """
    with _connect() as conn:
        rows = conn.execute("""
            SELECT from_currency, to_currency, provider,
                   COUNT(*) as report_count,
                   ROUND(AVG(reported_rate), 6) as avg_reported_rate,
                   ROUND(MIN(reported_rate), 6) as min_reported_rate,
                   ROUND(MAX(reported_rate), 6) as max_reported_rate,
                   ROUND(AVG(reported_fee_pct), 4) as avg_reported_fee_pct,
                   MAX(ts) as latest_report
            FROM rate_reports
            WHERE ts >= datetime('now', '-24 hours')
            GROUP BY from_currency, to_currency, provider
            ORDER BY report_count DESC
        """).fetchall()
        return [dict(r) for r in rows]
