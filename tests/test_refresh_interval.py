"""The 5-minute refresh (REFRESH_INTERVAL_S) and everything that depends on it."""
import time

from fastapi.testclient import TestClient

from coinnect import REFRESH_INTERVAL_S


def test_interval_is_five_minutes():
    assert REFRESH_INTERVAL_S == 300


def test_seo_cache_follows_refresh():
    from coinnect import seo_pages
    assert seo_pages.CACHE_TTL == REFRESH_INTERVAL_S


def test_fast_adapter_ttls_refetch_every_refresh():
    """A per-refresh source must not be served from its own cache on the next
    refresh: the loop sleeps REFRESH_INTERVAL_S after each refresh, so a TTL <=
    the interval always refetches. TTLs above it (ECB, central banks, Wise) are
    slower sources on purpose."""
    from coinnect.exchanges import ccxt_adapter, direct_api_adapter
    assert ccxt_adapter.CACHE_TTL_SECONDS <= REFRESH_INTERVAL_S
    fast = {k: v for k, v in vars(direct_api_adapter).items()
            if k.endswith("_TTL") and isinstance(v, int) and v <= 300}
    assert fast and all(v <= REFRESH_INTERVAL_S for v in fast.values())


def test_instant_quote_survives_a_full_cycle(monkeypatch):
    """Cached quotes stay servable for one interval plus the refresh's own run
    time; with the old 300 s cut-off and a 300 s interval they would go 204
    for part of every cycle."""
    import coinnect.main as m
    from coinnect.routing.engine import QuoteResult
    from datetime import datetime, UTC
    key = m.quote_cache_key("USD", "MXN", 100.0)
    result = QuoteResult("USD", "MXN", 100.0, datetime.now(UTC), [])
    client = TestClient(m.app)
    now = time.monotonic()
    m._quote_cache[key] = {"result": result, "ts": now - (REFRESH_INTERVAL_S + 60)}
    assert client.get("/v1/quote/instant", params={"from": "USD", "to": "MXN", "amount": 100}).status_code == 200
    m._quote_cache[key] = {"result": result, "ts": now - (REFRESH_INTERVAL_S + 180)}
    assert client.get("/v1/quote/instant", params={"from": "USD", "to": "MXN", "amount": 100}).status_code == 204
    m._quote_cache.pop(key, None)
