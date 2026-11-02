"""Regression: a failed load_markets must not leak an aiohttp session.

bybit loads markets with an asyncio.gather of several requests; when one fails
the siblings keep running and reopen the session after our close(), logged as
"Unclosed client session".
"""

import asyncio

import aiohttp
import pytest

from coinnect.exchanges import ccxt_adapter


class FakeExchange:
    """Mimics ccxt's lazy session handling (open() on every fetch)."""

    instances: list["FakeExchange"] = []

    def __init__(self, config):
        self.session = None
        self.timeout = 1000  # ms — keeps the reaper window short
        self.sessions: list[aiohttp.ClientSession] = []
        self.ok = config.get("ok", False)
        FakeExchange.instances.append(self)

    def open(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self.sessions.append(self.session)

    async def close(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def _sibling_request(self):
        await asyncio.sleep(0.2)  # still in flight when the gather fails
        self.open()

    async def fetch_tickers(self):
        self.open()
        if self.ok:
            return {}
        failing = asyncio.sleep(0.05, result=None)

        async def fail():
            await failing
            raise RuntimeError("instruments-info?category=spot failed")

        await asyncio.gather(fail(), self._sibling_request())


@pytest.mark.asyncio
async def test_failed_fetch_does_not_leak_session():
    FakeExchange.instances.clear()
    edges = await ccxt_adapter.fetch_edges_from_exchange(
        "bybit", {"class": FakeExchange, "fee_pct": 0.1}
    )
    assert edges == []
    ex = FakeExchange.instances[0]
    # Let the straggler reopen the session and the reaper close it.
    for task in list(ccxt_adapter._reapers):
        await task
    assert len(ex.sessions) == 2, "straggler should have reopened a session"
    assert all(s.closed for s in ex.sessions)
    assert ex.session is None


@pytest.mark.asyncio
async def test_successful_fetch_schedules_no_reaper():
    FakeExchange.instances.clear()

    class OkExchange(FakeExchange):
        def __init__(self, config):
            super().__init__({**config, "ok": True})

    await ccxt_adapter.fetch_edges_from_exchange("fake", {"class": OkExchange, "fee_pct": 0.1})
    assert not ccxt_adapter._reapers
    assert all(s.closed for s in FakeExchange.instances[0].sessions)


@pytest.mark.asyncio
async def test_shutdown_reapers_closes_pending_session():
    FakeExchange.instances.clear()
    await ccxt_adapter.fetch_edges_from_exchange(
        "bybit", {"class": FakeExchange, "fee_pct": 0.1}
    )
    ex = FakeExchange.instances[0]
    await asyncio.sleep(0.3)  # straggler reopened; reaper hasn't ticked yet
    assert ex.session is not None
    await ccxt_adapter.shutdown_reapers()
    assert not ccxt_adapter._reapers
    assert all(s.closed for s in ex.sessions)
