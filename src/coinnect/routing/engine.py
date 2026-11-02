"""
Route engine — finds cheapest/fastest paths between currencies.
Uses Dijkstra on a live currency graph built from exchange rates.
"""

import heapq
from dataclasses import dataclass
from datetime import datetime, UTC


@dataclass
class Step:
    step: int
    from_currency: str
    to_currency: str
    via: str
    fee_pct: float
    estimated_minutes: int
    instructions: str
    exchange_rate: float = 1.0
    min_amount: float = 0.01
    max_amount: float = 1_000_000.0


@dataclass
class Route:
    rank: int
    label: str
    total_cost_pct: float
    total_time_minutes: int
    you_send: float
    they_receive: float
    they_receive_currency: str
    steps: list[Step]


@dataclass
class QuoteResult:
    from_currency: str
    to_currency: str
    amount: float
    generated_at: datetime
    routes: list[Route]


@dataclass(slots=True)
class Edge:
    """A single conversion step between two currencies via an exchange."""
    from_currency: str
    to_currency: str
    via: str           # exchange name
    fee_pct: float     # total cost as percentage (fee + spread)
    estimated_minutes: int
    instructions: str = ""
    exchange_rate: float = 1.0  # units of to_currency per 1 from_currency
    min_amount: float = 0.01    # minimum send amount in from_currency
    max_amount: float = 1_000_000.0  # maximum send amount in from_currency


# Currencies a route may pass *through*. The ~6,000 altcoins on the exchanges stay
# usable as a route's source or destination, but exploring them as intermediates
# multiplied routing CPU by ~50x and never produced a route that was returned.
# Currencies of comprehensively sanctioned countries are left out on purpose.
CRYPTO_HUBS = frozenset({"USDT", "USDC", "DAI", "BTC", "ETH"})
FIAT_HUBS = frozenset("""
    AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP
    BYN BZD CAD CDF CHF CLP CNY COP CRC CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP
    GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD ISK JMD JOD JPY KES KGS KHR
    KMF KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK
    MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RWF SAR
    SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SZL THB TJS TMT TND TOP TRY TTD TWD TZS
    UAH UGX USD UYU UZS VES VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWL
""".split())
ROUTING_HUBS = CRYPTO_HUBS | FIAT_HUBS

# Pure data sources, not transfer services: they can bridge a multi-hop search
# but a route that uses one is never shown. CriptoYa's per-exchange feeds use the
# "(AR)" suffix and are aggregated price data too.
REFERENCE_PROVIDERS = frozenset({
    "Market rate", "ECB (reference)", "FloatRates", "x-rates.com (mid-market)",
    "Yadio (P2P)", "CoinGecko (market)",
    "BCB PTAX (BR)", "Banxico (MX)", "TRM (CO)", "TCMB (TR)", "NBP (PL)", "CNB (CZ)",
    "NBU (UA)", "NBG (GE)", "BOI (IL)", "BNR (RO)", "NRB (NP)",
    "Blue market (AR)", "Official (AR)", "Dolar Blue (AR)", "MEP (AR)", "CCL (AR)",
    "Parallel (LB)",
})


def is_reference_provider(via: str) -> bool:
    return via in REFERENCE_PROVIDERS or via.endswith(" (AR)")


def routable_edges(edges: list[Edge], start: str, end: str) -> list[Edge]:
    """Keep only edges whose currencies are hubs or this query's endpoints."""
    allowed = ROUTING_HUBS | {start, end}
    return [e for e in edges if e.from_currency in allowed and e.to_currency in allowed]


def build_graph(edges: list[Edge]) -> dict[str, list[Edge]]:
    """Build adjacency list from edges."""
    graph: dict[str, list[Edge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_currency, []).append(edge)
    return graph


def _dijkstra(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    optimize: str = "cost",  # "cost" or "time"
    max_routes: int = 5,
    max_steps: int = 4,
) -> list[tuple[float, float, list[Edge]]]:
    """Single Dijkstra run optimizing by cost or time."""
    tie_breaker = 0
    heap = [(0.0, tie_breaker, 0, start, amount, [])]
    results = []
    visited_states: dict[tuple, float] = {}
    iterations = 0
    max_iterations = 100_000  # safety cap: heap pops

    while heap and len(results) < max_routes and iterations < max_iterations:
        priority, _, steps, curr, curr_amount, path = heapq.heappop(heap)
        iterations += 1

        # K-shortest-paths: only prune exact duplicates (same currency, same
        # provider set, same step count). This lets different exchange combinations
        # through the same intermediate currency all get explored.
        providers_key = frozenset(e.via for e in path)
        state = (curr, providers_key)
        if state in visited_states and visited_states[state] <= priority:
            continue
        visited_states[state] = priority

        if curr == end and path:
            # Compound cost: 1 - product((1 - fee_i/100)) — per MRP spec
            product = 1.0
            for e in path:
                product *= (1 - e.fee_pct / 100)
            total_cost = (1 - product) * 100
            results.append((total_cost, curr_amount, path))
            continue

        if steps >= max_steps:
            continue

        for edge in graph.get(curr, []):
            # Skip if this exchange was already used in the path (no circular routes)
            if any(e.via == edge.via for e in path):
                continue
            new_amount = curr_amount * edge.exchange_rate * (1 - edge.fee_pct / 100)
            new_priority = priority + (edge.fee_pct if optimize == "cost" else edge.estimated_minutes)
            tie_breaker += 1
            heapq.heappush(heap, (
                new_priority,
                tie_breaker,
                steps + 1,
                edge.to_currency,
                new_amount,
                path + [edge],
            ))

    return results


def find_routes(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    max_routes: int = 30,
    max_steps: int = 4,
) -> list[tuple[float, float, list[Edge]]]:
    """
    Find diverse routes — collects ALL direct single-step routes, then uses
    Dijkstra for multi-step paths (cost and time optimized). Merges and deduplicates.
    Returns list of (total_cost_pct, amount_received, path).

    All direct routes are always included (so baseline providers like WU/MG
    always appear). The max_routes cap only trims multi-step combinations.
    """
    # 1. All direct routes (single-step, any provider) — ALL included, sorted by cost
    direct: list[tuple[float, float, list[Edge]]] = []
    for edge in graph.get(start, []):
        if edge.to_currency == end:
            received = amount * edge.exchange_rate * (1 - edge.fee_pct / 100)
            direct.append((edge.fee_pct, received, [edge]))
    direct.sort(key=lambda x: x[0])

    # 2. Multi-step routes via Dijkstra (max_steps >= 2)
    by_cost = _dijkstra(graph, start, end, amount, optimize="cost", max_routes=8, max_steps=max_steps)
    by_time = _dijkstra(graph, start, end, amount, optimize="time", max_routes=5, max_steps=max_steps)
    multi_step = [r for r in by_cost + by_time if len(r[2]) > 1]

    # 3. Merge, deduplicating by path signature
    #    Direct routes go first (all of them), then multi-step up to max_routes total
    seen: set[tuple] = set()
    merged = []
    for cost, received, path in direct:
        sig = tuple((e.from_currency, e.to_currency, e.via) for e in path)
        if sig not in seen:
            seen.add(sig)
            merged.append((cost, received, path))

    for cost, received, path in multi_step:
        if len(merged) >= max_routes:
            break
        sig = tuple((e.from_currency, e.to_currency, e.via) for e in path)
        if sig not in seen:
            seen.add(sig)
            merged.append((cost, received, path))

    return merged


def build_quote(
    edges: list[Edge],
    from_currency: str,
    to_currency: str,
    amount: float,
) -> QuoteResult:
    # Filter by both min and max amount (max_amount=0 means unlimited)
    valid_edges = [e for e in edges if amount >= e.min_amount and (e.max_amount == 0 or amount <= e.max_amount)]
    graph = build_graph(routable_edges(valid_edges, from_currency, to_currency))
    raw_routes = find_routes(graph, from_currency, to_currency, amount)

    if not raw_routes:
        return QuoteResult(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            generated_at=datetime.now(UTC),
            routes=[],
        )

    # Identify special routes
    cheapest_idx = min(range(len(raw_routes)), key=lambda i: raw_routes[i][0])
    fastest_idx = min(range(len(raw_routes)), key=lambda i: sum(e.estimated_minutes for e in raw_routes[i][2]))

    label_by_idx = {cheapest_idx: "Cheapest"}
    if fastest_idx != cheapest_idx:
        label_by_idx[fastest_idx] = "Fastest"

    # Rank every route by cost (ascending), labelling Cheapest/Fastest wherever
    # they land and the rest as Option N — keeps result.routes sorted by
    # total_cost_pct regardless of which routes are featured.
    sorted_indices = sorted(range(len(raw_routes)), key=lambda i: raw_routes[i][0])
    all_ordered = []
    option_n = 0
    for idx in sorted_indices:
        if idx in label_by_idx:
            all_ordered.append((idx, label_by_idx[idx]))
        else:
            option_n += 1
            all_ordered.append((idx, f"Option {option_n}"))

    routes = []
    for rank, (raw_idx, label) in enumerate(all_ordered, start=1):
        total_cost, received, path = raw_routes[raw_idx]
        total_minutes = sum(e.estimated_minutes for e in path)
        steps = [
            Step(
                step=j + 1,
                from_currency=e.from_currency,
                to_currency=e.to_currency,
                via=e.via,
                fee_pct=e.fee_pct,
                estimated_minutes=e.estimated_minutes,
                instructions=e.instructions or f"Convert {e.from_currency} to {e.to_currency} via {e.via}",
                exchange_rate=e.exchange_rate,
                min_amount=e.min_amount,
                max_amount=e.max_amount,
            )
            for j, e in enumerate(path)
        ]
        routes.append(Route(
            rank=rank,
            label=label,
            total_cost_pct=round(total_cost, 2),
            total_time_minutes=total_minutes,
            you_send=amount,
            they_receive=round(received, 2),
            they_receive_currency=to_currency,
            steps=steps,
        ))

    return QuoteResult(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        generated_at=datetime.now(UTC),
        routes=routes,
    )


def build_public_quote(
    edges: list[Edge],
    from_currency: str,
    to_currency: str,
    amount: float,
) -> tuple[QuoteResult, tuple[float, float | None] | None]:
    """The routes users see, plus the (min, max) amount range of the valid edges.

    CPU-bound: call it off the event loop.
    """
    real_edges = [e for e in edges if not is_reference_provider(e.via)]
    result = build_quote(edges, from_currency, to_currency, amount)
    # Second pass without reference bridges: pure crypto multi-hop routes
    # (Binance→Bitso etc.) get crowded out by cheaper reference paths in the first.
    result_real = build_quote(real_edges, from_currency, to_currency, amount)

    seen = set()
    merged = []
    for route in result.routes + result_real.routes:
        signature = tuple((s.from_currency, s.to_currency, s.via) for s in route.steps)
        if signature not in seen:
            seen.add(signature)
            merged.append(route)

    routes = [
        r for r in merged
        if r.they_receive > 0 and not any(is_reference_provider(s.via) for s in r.steps)
    ]
    routes.sort(key=lambda r: r.total_cost_pct)
    if routes:
        routes[0].label = "Cheapest"
        fastest = min(routes, key=lambda r: r.total_time_minutes)
        if fastest != routes[0]:
            fastest.label = "Fastest"
        for i, route in enumerate(routes):
            route.rank = i + 1
            if route.label not in ("Cheapest", "Fastest"):
                route.label = f"Option {i + 1}"
    result.routes = routes

    valid = [e for e in edges if amount >= e.min_amount and (e.max_amount == 0 or amount <= e.max_amount)]
    amount_range = None
    if valid:
        positive_maxes = [e.max_amount for e in valid if e.max_amount > 0]
        amount_range = (min(e.min_amount for e in valid), max(positive_maxes) if positive_maxes else None)
    return result, amount_range
