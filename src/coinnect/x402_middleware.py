"""
x402 micropayment middleware for Coinnect.

Enables pay-per-request access to /v1/quote via USDC on Base L2.
Agents pay $0.002 per request for unlimited access (no rate limits).

Usage: add x402_middleware to the FastAPI app in main.py.
Requires: ALCHEMY_BASE_KEY env var for Base L2 RPC.
"""

import os
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Config
COINNECT_WALLET = "0xf0813041b9b017a88f28B8600E73a695E2B02e0A"
PRICE_PER_REQUEST = "0.002"  # USDC ($0.002 per quote)
BASE_NETWORK = "eip155:8453"  # Base L2 CAIP-2 identifier
ALCHEMY_KEY = os.environ.get("ALCHEMY_BASE_KEY", "")

# Routes that require payment (only /v1/quote for now)
PAID_ROUTES = {"/v1/quote"}


class X402Middleware(BaseHTTPMiddleware):
    """
    Middleware that adds x402 payment option to protected routes.

    Flow:
    1. Request comes in for /v1/quote
    2. If request has valid X-Payment header → verify payment → serve response
    3. If request has API key → use normal rate limiting (free tier)
    4. If request is anonymous AND over rate limit → return 402 with payment instructions
    5. If request is anonymous AND under rate limit → serve normally (free tier)

    x402 is an ADDITIONAL option, not a replacement for the free tier.
    """

    def __init__(self, app):
        super().__init__(app)
        self._server = None
        self._initialized = False

    async def _init_server(self):
        """Lazy-initialize the x402 server (only if ALCHEMY_KEY is set)."""
        if self._initialized:
            return
        self._initialized = True

        if not ALCHEMY_KEY:
            logger.info("x402: ALCHEMY_BASE_KEY not set — micropayments disabled")
            return

        try:
            from x402 import x402ResourceServer, ResourceConfig

            self._server = x402ResourceServer()
            self._resource_config = ResourceConfig(
                scheme="exact",
                payTo=COINNECT_WALLET,
                price=PRICE_PER_REQUEST,
                network=BASE_NETWORK,
                maxTimeoutSeconds=300,
            )
            logger.info(f"x402: Micropayments enabled — {PRICE_PER_REQUEST} USDC/request on Base L2")
        except Exception as e:
            logger.warning(f"x402: Failed to initialize — {e}")
            self._server = None

    async def dispatch(self, request: Request, call_next):
        await self._init_server()

        # Only apply to paid routes
        if request.url.path not in PAID_ROUTES:
            return await call_next(request)

        # If x402 is not initialized, pass through normally
        if not self._server:
            return await call_next(request)

        # Check for x402 payment header
        payment_header = request.headers.get("X-Payment")

        if payment_header:
            # Verify payment
            try:
                rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"
                verify_result = await self._server.verify(
                    payment_header,
                    self._resource_config,
                    rpc_url=rpc_url,
                )
                if verify_result.valid:
                    # Payment verified — serve without rate limits
                    response = await call_next(request)
                    response.headers["X-Payment-Status"] = "paid"
                    response.headers["X-Payment-Amount"] = PRICE_PER_REQUEST

                    # Settle the payment
                    try:
                        await self._server.settle(
                            payment_header,
                            self._resource_config,
                            rpc_url=rpc_url,
                        )
                    except Exception as e:
                        logger.warning(f"x402: Settlement failed — {e}")

                    return response
                else:
                    logger.debug("x402: Payment verification failed")
            except Exception as e:
                logger.debug(f"x402: Payment error — {e}")

        # No payment — continue with normal flow (free tier + rate limiting)
        response = await call_next(request)

        # If rate limited (429), add x402 payment option in headers
        if response.status_code == 429:
            response.headers["X-Payment-Required"] = (
                f'{{"scheme":"exact","payTo":"{COINNECT_WALLET}",'
                f'"price":"{PRICE_PER_REQUEST}","network":"{BASE_NETWORK}",'
                f'"description":"Coinnect quote — unlimited access via USDC micropayment"}}'
            )
            response.headers["X-Payment-Info"] = "Pay $0.002 USDC on Base L2 for unlimited access"

        return response
