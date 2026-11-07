"""build_raw_and_public_quote() must equal build_quote() + build_public_quote()."""
import dataclasses

from coinnect.routing.engine import (
    Edge, build_public_quote, build_quote, build_raw_and_public_quote,
)


def _edges():
    return [
        Edge("USD", "USDT", "Binance", 0.1, 10, exchange_rate=1.0),
        Edge("USDT", "MXN", "Bitso", 0.65, 15, exchange_rate=18.4),
        Edge("USD", "MXN", "Wise", 0.8, 60, exchange_rate=18.2),
        Edge("USD", "MXN", "Market rate", 0.0, 0, exchange_rate=18.5),
        Edge("USD", "EUR", "Kraken", 0.26, 10, exchange_rate=0.92),
        Edge("EUR", "MXN", "Wise", 0.5, 60, exchange_rate=19.9),
        Edge("USDT", "EUR", "Kraken", 0.3, 10, exchange_rate=0.92, min_amount=50),
        Edge("USD", "BTC", "Kraken", 0.4, 10, exchange_rate=0.00001, max_amount=1000),
        Edge("BTC", "MXN", "Bitso", 0.7, 15, exchange_rate=1_800_000),
    ]


def _norm(q):
    d = dataclasses.asdict(q)
    d.pop("generated_at")
    return d


def test_combined_equals_separate_calls():
    for amount in (10, 100, 500, 5000):
        raw, public, rng = build_raw_and_public_quote(_edges(), "USD", "MXN", amount)
        assert _norm(raw) == _norm(build_quote(_edges(), "USD", "MXN", amount))
        sep_public, sep_rng = build_public_quote(_edges(), "USD", "MXN", amount)
        assert _norm(public) == _norm(sep_public)
        assert rng == sep_rng
        # the raw result keeps reference routes; the public one drops them
        assert any(s.via == "Market rate" for r in raw.routes for s in r.steps)
        assert not any(s.via == "Market rate" for r in public.routes for s in r.steps)
