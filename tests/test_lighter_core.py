"""Regressions for the 2026-11 performance and safety pass."""

import asyncio
import gzip
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from coinnect.routing.engine import Edge, build_public_quote, build_quote, routable_edges


def _edge(a, b, via, fee=0.1, rate=1.0):
    return Edge(a, b, via, fee, 10, exchange_rate=rate)


# ── Routing ──────────────────────────────────────────────────────────────────

def test_altcoins_are_not_routing_intermediates():
    edges = [
        _edge("USD", "SOMEALT", "A"), _edge("SOMEALT", "MXN", "B"),
        _edge("USD", "USDT", "A"), _edge("USDT", "MXN", "B"),
    ]
    paths = [[s.to_currency for s in r.steps] for r in build_quote(edges, "USD", "MXN", 100).routes]
    assert ["USDT", "MXN"] in paths
    assert ["SOMEALT", "MXN"] not in paths


def test_altcoin_endpoints_still_route():
    edges = [_edge("SOMEALT", "USDT", "A"), _edge("USDT", "MXN", "B")]
    routes = build_quote(edges, "SOMEALT", "MXN", 100).routes
    assert [[s.to_currency for s in r.steps] for r in routes] == [["USDT", "MXN"]]


def test_routable_edges_keeps_hubs_and_endpoints_only():
    edges = [_edge("USD", "EUR", "A"), _edge("USD", "ZZZ", "A"), _edge("ZZZ", "QQQ", "A")]
    assert [e.to_currency for e in routable_edges(edges, "USD", "ZZZ")] == ["EUR", "ZZZ"]


def test_public_quote_hides_reference_providers():
    edges = [_edge("USD", "MXN", "Banxico (MX)", fee=0.0), _edge("USD", "MXN", "Wise", fee=0.5)]
    result, amount_range = build_public_quote(edges, "USD", "MXN", 100)
    assert [s.via for r in result.routes for s in r.steps] == ["Wise"]
    assert result.routes[0].label == "Cheapest"
    assert amount_range is not None


def test_edges_use_slots_to_stay_small():
    assert not hasattr(_edge("USD", "EUR", "A"), "__dict__")


# ── CCXT ─────────────────────────────────────────────────────────────────────

def test_derivative_contracts_are_not_edges(monkeypatch):
    from coinnect.exchanges import ccxt_adapter

    class Fake:
        session = None
        timeout = 1000

        def __init__(self, config):
            pass

        async def fetch_tickers(self):
            quote = {"bid": 99.0, "ask": 100.0}
            return {"BTC/USDT": quote, "BTC/USDT:USDT": quote, "BTC/USD:BTC-261225": quote}

        async def close(self):
            pass

    edges = asyncio.run(ccxt_adapter.fetch_edges_from_exchange("fake", {"class": Fake, "fee_pct": 0.1}))
    assert {(e.from_currency, e.to_currency) for e in edges} == {("BTC", "USDT"), ("USDT", "BTC")}


# ── API keys ─────────────────────────────────────────────────────────────────

@pytest.fixture
def keys_db(tmp_path, monkeypatch):
    from coinnect.db import keys

    monkeypatch.setattr(keys, "DB_PATH", tmp_path / "k.db")
    for store in (keys._key_tier_cache, keys._day_counts, keys._hour_counts):
        store.clear()
    keys.init_keys_db()
    return keys


def test_keys_are_hashed_at_rest(keys_db):
    key = keys_db.create_key(label="t")
    with sqlite3.connect(keys_db.DB_PATH) as conn:
        stored = conn.execute("SELECT api_key FROM api_keys").fetchone()[0]
    assert stored != key and stored.startswith("sha256:")
    assert key not in keys_db._key_tier_cache
    assert keys_db.get_key_tier(key) == "free"
    assert keys_db.check_rate_limit(key)[0] is True
    assert keys_db.get_key_tier("cn_wrong") is None


def test_plaintext_keys_migrate_and_keep_working(keys_db):
    with sqlite3.connect(keys_db.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO api_keys (api_key, tier, created_at) VALUES ('cn_legacy', 'agent', '2026-01-01')"
        )
    keys_db._key_tier_cache.clear()
    keys_db.init_keys_db()
    keys_db.init_keys_db()  # idempotent: must not double-hash
    with sqlite3.connect(keys_db.DB_PATH) as conn:
        rows = [r[0] for r in conn.execute("SELECT api_key FROM api_keys")]
    assert "cn_legacy" not in rows
    assert keys_db.get_key_tier("cn_legacy") == "agent"


# ── Client IP ────────────────────────────────────────────────────────────────

def _request(peer="172.18.0.1", **headers):
    normalized = {k.replace("_", "-").lower(): v for k, v in headers.items()}
    return SimpleNamespace(headers=normalized, client=SimpleNamespace(host=peer))


def test_cf_header_trusted_only_from_cloudflare():
    from coinnect.net import client_ip

    via_cf = _request(x_forwarded_for="104.16.0.9", cf_connecting_ip="8.8.8.8")
    assert client_ip(via_cf) == "8.8.8.8"


def test_forged_cf_header_from_direct_hit_is_ignored():
    from coinnect.net import client_ip

    forged = _request(x_forwarded_for="203.0.113.7", cf_connecting_ip="8.8.8.8")
    assert client_ip(forged) == "203.0.113.7"


def test_forwarded_chain_uses_last_hop_not_client_supplied_first():
    from coinnect.net import client_ip

    assert client_ip(_request(x_forwarded_for="1.1.1.1, 203.0.113.7")) == "203.0.113.7"


def test_client_ip_falls_back_to_socket_peer():
    from coinnect.net import client_ip

    assert client_ip(_request(peer="192.168.122.1")) == "192.168.122.1"


def test_invalid_cf_header_is_ignored():
    from coinnect.net import client_ip

    assert client_ip(_request(x_forwarded_for="104.16.0.9", cf_connecting_ip="not-an-ip")) == "104.16.0.9"


# ── History compaction ───────────────────────────────────────────────────────

@pytest.fixture
def history_db(tmp_path, monkeypatch):
    from coinnect.db import history

    monkeypatch.setattr(history, "DB_PATH", tmp_path / "h.db")
    monkeypatch.setattr(history, "ARCHIVE_DIR", tmp_path / "archive")
    history.init_db()
    return history


def _insert(history, when: datetime, pair=("USD", "MXN")):
    with history._connect() as conn:
        conn.execute(
            """INSERT INTO rate_snapshots (captured_at, from_currency, to_currency, amount,
               best_cost_pct, best_time_min, they_receive, best_via, routes_json)
               VALUES (?,?,?,500,0.1,10,9000,'A','[]')""",
            (when.isoformat(), *pair),
        )


def test_compaction_thins_old_rows_and_archives_everything_removed(history_db):
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    old = now - timedelta(days=10)
    for minute in (0, 3, 6):
        _insert(history_db, old.replace(minute=minute))
    expired = now - timedelta(days=40)
    _insert(history_db, expired)
    _insert(history_db, now - timedelta(days=1))
    _insert(history_db, now - timedelta(days=1, minutes=-3))

    assert history_db.compact_history(now=now) == 3

    with history_db._connect() as conn:
        kept = [r[0] for r in conn.execute("SELECT captured_at FROM rate_snapshots ORDER BY captured_at")]
    assert kept[0] == old.replace(minute=0).isoformat()  # first row of the hour survives
    assert len(kept) == 3  # 1 thinned hour + 2 recent rows untouched

    archived = []
    for path in sorted(history_db.ARCHIVE_DIR.glob("*.jsonl.gz")):
        with gzip.open(path, "rt") as fh:
            archived += [json.loads(line) for line in fh]
    assert {r["captured_at"] for r in archived} == {
        old.replace(minute=3).isoformat(), old.replace(minute=6).isoformat(), expired.isoformat(),
    }
    assert history_db.compact_history(now=now) == 0  # idempotent


def test_later_compactions_keep_earlier_archives(history_db):
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    day = now - timedelta(days=10)
    _insert(history_db, day.replace(minute=0))
    _insert(history_db, day.replace(minute=5))
    history_db.compact_history(now=now)
    _insert(history_db, day.replace(minute=9))
    history_db.compact_history(now=now)
    rows = []
    for path in history_db.ARCHIVE_DIR.glob("*.jsonl.gz"):
        with gzip.open(path, "rt") as fh:
            rows += fh.readlines()
    assert len(rows) == 2


# ── Adapters ─────────────────────────────────────────────────────────────────

class _Resp:
    def __init__(self, text="", payload=None):
        self.text = text
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _fake_client(monkeypatch, module, resp, seen):
    class Client:
        def __init__(self, *a, **k):
            seen.setdefault("kwargs", k)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, **k):
            seen.setdefault("urls", []).append(url)
            return resp

    monkeypatch.setattr(module.httpx, "AsyncClient", Client)


BNR_XML = """<?xml version="1.0" encoding="utf-8"?>
<DataSet xmlns="https://www.bnr.ro/xsd"><Body><Cube date="2026-11-02">
<Rate currency="EUR">5.0800</Rate><Rate currency="USD">4.4000</Rate><Rate currency="HUF" multiplier="100">1.3000</Rate>
</Cube></Body></DataSet>"""


def test_bnr_uses_new_host_and_namespace(monkeypatch):
    from coinnect.exchanges import direct_api_adapter as d

    seen = {}
    _fake_client(monkeypatch, d, _Resp(text=BNR_XML), seen)
    d._bnr_cache.update({"edges": [], "ts": 0.0})
    edges = asyncio.run(d.get_bnr_edges())
    d._bnr_cache.update({"edges": [], "ts": 0.0})
    assert seen["urls"] == ["https://curs.bnr.ro/nbrfxrates.xml"]
    assert {e.from_currency for e in edges} == {"USD", "EUR"}
    assert {e.to_currency for e in edges} == {"RON"}


def test_frankfurter_uses_current_host(monkeypatch):
    from coinnect.exchanges import direct_api_adapter as d

    seen = {}
    _fake_client(monkeypatch, d, _Resp(payload={"rates": {"MXN": 18.0}}), seen)
    d._frankfurter_cache.update({"edges": [], "ts": 0.0})
    edges = asyncio.run(d.get_frankfurter_edges())
    d._frankfurter_cache.update({"edges": [], "ts": 0.0})
    assert seen["urls"] and all(u.startswith("https://api.frankfurter.dev/v1/") for u in seen["urls"])
    assert edges


def test_nrb_trusts_its_missing_intermediate_without_disabling_verification():
    import ssl

    from coinnect.exchanges.direct_api_adapter import _nrb_ssl_context

    ctx = _nrb_ssl_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_nrb_parser_reads_current_payload_shape():
    from coinnect.exchanges.direct_api_adapter import _nrb_usd_rate

    payload = {"data": {"payload": [{"date": "2026-10-31", "rates": [
        {"currency": {"iso3": "INR", "name": "Indian Rupee", "unit": 100}, "buy": "160.00", "sell": "160.15"},
        {"currency": {"iso3": "USD", "name": "U.S. Dollar", "unit": 1}, "buy": "142.10", "sell": "142.70"},
    ]}]}}
    assert _nrb_usd_rate(payload) == 142.70
    assert _nrb_usd_rate({"data": {"payload": []}}) is None


def test_quote_cache_key_matches_int_and_float_amounts():
    from coinnect.main import quote_cache_key

    assert quote_cache_key("USD", "MXN", 500) == quote_cache_key("USD", "MXN", 500.0)


def test_failed_archive_leaves_rows_in_the_table(history_db, monkeypatch):
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    day = now - timedelta(days=10)
    _insert(history_db, day.replace(minute=0))
    _insert(history_db, day.replace(minute=5))

    def fail(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(history_db.os, "replace", fail)
    with pytest.raises(OSError):
        history_db.compact_history(now=now)
    with history_db._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM rate_snapshots").fetchone()[0] == 2
    assert not list(history_db.ARCHIVE_DIR.glob("*.jsonl.gz"))


def test_hour_straddling_the_cutoff_keeps_its_first_old_row(history_db):
    """A newer row in the same hour must not make the old rows look thinnable."""
    now = datetime(2026, 11, 2, 12, 30, tzinfo=UTC)
    cutoff = now - timedelta(days=7)
    first_old = cutoff - timedelta(minutes=20)
    second_old = cutoff - timedelta(minutes=10)
    recent = cutoff + timedelta(minutes=5)
    for when in (first_old, second_old, recent):
        _insert(history_db, when)
    history_db.compact_history(now=now)
    with history_db._connect() as conn:
        kept = {r[0] for r in conn.execute("SELECT captured_at FROM rate_snapshots")}
    assert kept == {first_old.isoformat(), recent.isoformat()}


def test_interrupted_key_migration_rolls_back_and_retries(keys_db, monkeypatch):
    with sqlite3.connect(keys_db.DB_PATH) as conn:
        for key in ("cn_a", "cn_b"):
            conn.execute("INSERT INTO api_keys (api_key, tier, created_at) VALUES (?, 'free', '2026-01-01')", (key,))
    keys_db._key_tier_cache.clear()

    real_hash = keys_db._hash_key
    calls = []

    def dies_on_second(key):
        calls.append(key)
        if len(calls) == 2:
            raise RuntimeError("killed mid-migration")
        return real_hash(key)

    monkeypatch.setattr(keys_db, "_hash_key", dies_on_second)
    with pytest.raises(RuntimeError):
        keys_db.init_keys_db()
    with sqlite3.connect(keys_db.DB_PATH) as conn:
        assert {r[0] for r in conn.execute("SELECT api_key FROM api_keys")} == {"cn_a", "cn_b"}

    monkeypatch.setattr(keys_db, "_hash_key", real_hash)
    keys_db.init_keys_db()
    assert keys_db.get_key_tier("cn_a") == "free" and keys_db.get_key_tier("cn_b") == "free"
