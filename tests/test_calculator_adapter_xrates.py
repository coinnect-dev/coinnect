"""Regression test for the x-rates.com adapter.

Bug (coinnect k-04-fx-recon, item 6fd3cd3a): the adapter's regex fallback
chain matched the *input* echo (`ccOutputTxt">1.00`) instead of the real
converted rate (`ccOutputRslt">18.48<span class="ccOutputTrail">9505</span>`),
so every one of its 15,809 quotes came back as rate=1.0 (receive == amount).
"""

import httpx
import pytest

from coinnect.exchanges.calculator_adapter import _fetch_xrate

# Trimmed real markup captured from x-rates.com/calculator/?from=USD&to=MXN&amount=1
# on 2026-10-16.
XRATES_HTML = """
<div class="ccOutputBx">
 <span class="ccOutputTxt">1.00 USD =</span>
 <span class="ccOutputRslt">18.48<span class="ccOutputTrail">9505</span><span class="ccOutputCode"> MXN</span></span>
</div>
"""


def _mock_client(html: str, status: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_fetch_xrate_parses_real_result_not_input_echo():
    async with _mock_client(XRATES_HTML) as client:
        edge = await _fetch_xrate(client, "USD", "MXN")

    assert edge is not None
    assert edge.exchange_rate == pytest.approx(18.489505)
    assert edge.exchange_rate != 1.0


@pytest.mark.asyncio
async def test_fetch_xrate_returns_none_on_non_200():
    async with _mock_client("", status=503) as client:
        edge = await _fetch_xrate(client, "USD", "MXN")

    assert edge is None


@pytest.mark.asyncio
async def test_fetch_xrate_returns_none_when_markup_unrecognized():
    async with _mock_client("<html>no rate here</html>") as client:
        edge = await _fetch_xrate(client, "USD", "MXN")

    assert edge is None
