"""
Route engine — finds cheapest/fastest paths between currencies.
Uses Dijkstra on a live currency graph built from exchange rates.
"""

import heapq
from dataclasses import dataclass, field
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


@dataclass
class Edge:
    """A single conversion step between two currencies via an exchange."""
    from_currency: str
    to_currency: str
    via: str           # exchange name
    fee_pct: float     # total cost as percentage (fee + spread)
    estimated_minutes: int
    instructions: str = ""


def build_graph(edges: list[Edge]) -> dict[str, list[Edge]]:
    """Build adjacency list from edges."""
    graph: dict[str, list[Edge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_currency, []).append(edge)
    return graph


def find_routes(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    max_routes: int = 8,
    max_steps: int = 3,
) -> list[tuple[float, float, list[Edge]]]:
    """
    Dijkstra to find cheapest routes.
    Returns list of (total_cost_pct, amount_received, path).
    """
    counter = 0  # tie-breaker so heap never compares Edge objects
    # heap: (total_cost, counter, steps_count, current, amount, path)
    heap = [(0.0, counter, 0, start, amount, [])]
    results = []
    visited_states: dict[tuple, float] = {}

    while heap and len(results) < max_routes:
        cost, _, steps, curr, curr_amount, path = heapq.heappop(heap)

        state = (curr, steps)
        if state in visited_states and visited_states[state] <= cost:
            continue
        visited_states[state] = cost

        if curr == end and path:
            results.append((cost, curr_amount, path))
            continue

        if steps >= max_steps:
            continue

        for edge in graph.get(curr, []):
            new_amount = curr_amount * (1 - edge.fee_pct / 100)
            new_cost = cost + edge.fee_pct
            counter += 1
            heapq.heappush(heap, (
                new_cost,
                counter,
                steps + 1,
                edge.to_currency,
                new_amount,
                path + [edge],
            ))

    return results


def build_quote(
    edges: list[Edge],
    from_currency: str,
    to_currency: str,
    amount: float,
) -> QuoteResult:
    graph = build_graph(edges)
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

    # Balanced: best normalized cost*0.6 + time*0.4 score, excluding already-labeled
    max_cost = max(r[0] for r in raw_routes) or 1
    max_time = max(sum(e.estimated_minutes for e in r[2]) for r in raw_routes) or 1

    def balance_score(i):
        cost_n = raw_routes[i][0] / max_cost
        time_n = sum(e.estimated_minutes for e in raw_routes[i][2]) / max_time
        return cost_n * 0.6 + time_n * 0.4

    used = {cheapest_idx, fastest_idx}
    remaining = [i for i in range(len(raw_routes)) if i not in used]
    balanced_idx = min(remaining, key=balance_score) if remaining else cheapest_idx

    # Assign labels: featured first, then extras
    featured_order = []
    for idx in [cheapest_idx, balanced_idx, fastest_idx]:
        if idx not in [x[0] for x in featured_order]:
            featured_order.append((idx, ["Cheapest", "Balanced", "Fastest"][len(featured_order)]))

    extra_indices = [i for i in range(len(raw_routes)) if i not in {x[0] for x in featured_order}]
    all_ordered = featured_order + [(i, f"Option {j+4}") for j, i in enumerate(extra_indices)]

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
