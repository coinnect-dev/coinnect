"""
Wise API adapter — fiat-to-fiat corridors.
Uses Wise's public price comparison endpoint (no auth required for quotes).
"""

import logging
import httpx
from coinnect.routing.engine import Edge

logger = logging.getLogger(__name__)

# Wise public comparison endpoint (no auth required)
WISE_COMPARE_URL = "https://wise.com/gb/send-money/compare"

# Fee + spread estimates per corridor — sourced from wise.com/pricing (updated manually)
# Format: (from, to, fee_pct, estimated_minutes)
WISE_CORRIDORS: list[tuple] = [
    # Latin America
    ("USD", "MXN",  2.30, 60),
    ("USD", "ARS",  4.20, 60),
    ("USD", "BRL",  2.80, 60),
    ("USD", "COP",  2.60, 60),
    ("USD", "PEN",  2.90, 60),
    # Africa
    ("USD", "NGN",  3.10, 120),
    ("USD", "KES",  3.00, 120),
    ("USD", "GHS",  3.50, 120),
    ("USD", "TZS",  3.20, 120),
    ("USD", "UGX",  3.40, 120),
    # Asia
    ("USD", "PHP",  2.10, 60),
    ("USD", "INR",  1.80, 60),
    ("USD", "BDT",  2.50, 120),
    ("USD", "PKR",  2.80, 120),
    ("USD", "LKR",  2.60, 120),
    ("USD", "NPR",  2.90, 120),
    ("USD", "IDR",  2.20, 60),
    ("USD", "VND",  2.40, 60),
    ("USD", "THB",  2.00, 60),
    # Europe/Fiat
    ("EUR", "USD",  1.90, 60),
    ("GBP", "USD",  1.80, 60),
    ("EUR", "MXN",  2.50, 60),
    ("EUR", "PHP",  2.30, 60),
    ("EUR", "INR",  2.00, 60),
    ("SGD", "PHP",  1.90, 60),
    ("SGD", "INR",  1.80, 60),
    ("SGD", "BDT",  2.30, 120),
    ("AUD", "PHP",  2.20, 60),
    ("AUD", "INR",  2.00, 60),
    ("CAD", "PHP",  2.30, 60),
]

# Western Union / MoneyGram — approximate fees for comparison baseline
TRADITIONAL_CORRIDORS: list[tuple] = [
    # (from, to, service, fee_pct, minutes)
    ("USD", "MXN",  "Western Union", 5.50, 10),
    ("USD", "MXN",  "MoneyGram",     5.20, 10),
    ("USD", "NGN",  "Western Union", 6.80, 30),
    ("USD", "PHP",  "Western Union", 4.80, 10),
    ("USD", "PHP",  "MoneyGram",     4.50, 10),
    ("USD", "INR",  "Western Union", 4.50, 10),
    ("USD", "IDR",  "Western Union", 5.00, 30),
    ("USD", "VND",  "Western Union", 5.20, 30),
    ("USD", "BDT",  "Western Union", 5.50, 30),
    ("USD", "PKR",  "Western Union", 5.80, 30),
    ("USD", "ARS",  "Western Union", 7.20, 30),
    ("USD", "BRL",  "Western Union", 5.80, 30),
]


async def get_wise_edges() -> list[Edge]:
    """Return Wise fiat corridor edges using known fee schedule."""
    edges = []
    for from_, to_, fee, minutes in WISE_CORRIDORS:
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via="Wise",
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send {from_} via Wise — recipient gets {to_} in ~{minutes//60 or 1}h",
        ))
    return edges


async def get_traditional_edges() -> list[Edge]:
    """Return traditional remittance edges as comparison baseline."""
    edges = []
    for from_, to_, service, fee, minutes in TRADITIONAL_CORRIDORS:
        edges.append(Edge(
            from_currency=from_,
            to_currency=to_,
            via=service,
            fee_pct=fee,
            estimated_minutes=minutes,
            instructions=f"Send via {service} — fees approx {fee}% of amount",
        ))
    return edges
