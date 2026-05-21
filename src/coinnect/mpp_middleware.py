"""
MPP (Machine Payment Protocol) middleware for Coinnect.

Standard: https://mpp.dev — IETF draft-ietf-httpauth-payment.
Replaces the old x402 middleware (broken against current SDK and Base-only).

Behavior on /v1/quote:
1. No Authorization header → forward to handler (free tier rate-limiting still
   applies downstream). If downstream returns 429, upgrade to 402 with both
   challenges so the agent knows it can pay to bypass.
2. Authorization present → parse Credential, route to the Mpp instance matching
   `credential.challenge.method` ("tempo" or "stripe"). On verify success,
   forward request and attach Payment-Receipt + status headers. On failure,
   fall through to free tier (silent log).

Methods accepted:
- Tempo USDC at MPP_TEMPO_PRICE_USDC (default $0.0001/req). Always on if
  TEMPO_RECIPIENT is set.
- Stripe cards at MPP_STRIPE_PRICE_USD (default $1.00/req). On only if both
  STRIPE_BN_ID and STRIPE_SECRET_KEY are set (BN is the Stripe Business
  Network profile id).

Required env vars:
- MPP_SECRET_KEY: HMAC secret for challenge signing. Generate with `openssl
  rand -hex 32`. If unset, middleware no-ops.
- TEMPO_RECIPIENT: EVM address that receives Tempo USDC.
- MPP_TEMPO_TESTNET: "1" to use Moderato testnet (chain 42431), else mainnet
  (chain 4217). Default mainnet.

Optional:
- MPP_TEMPO_PRICE_USDC (default "0.0001")
- MPP_STRIPE_PRICE_USD (default "1.00")
- STRIPE_BN_ID, STRIPE_SECRET_KEY (both required to enable Stripe)
- MPP_REALM (default "coinnect.bot")
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

PAID_ROUTES = {"/v1/quote"}


class MPPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._initialized = False
        self._tempo_server = None
        self._stripe_server = None
        self._realm = os.environ.get("MPP_REALM", "coinnect.bot")
        self._tempo_price = os.environ.get("MPP_TEMPO_PRICE_USDC", "0.0001")
        self._stripe_price = os.environ.get("MPP_STRIPE_PRICE_USD", "1.00")
        self._tempo_chain_id = (
            42431 if os.environ.get("MPP_TEMPO_TESTNET") == "1" else 4217
        )

    def _init(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        secret_key = os.environ.get("MPP_SECRET_KEY")
        if not secret_key:
            print("mpp: MPP_SECRET_KEY not set — payment disabled, free tier only", flush=True)
            logger.info("mpp: MPP_SECRET_KEY not set — payment disabled, free tier only")
            return

        tempo_recipient = os.environ.get("TEMPO_RECIPIENT")
        if tempo_recipient:
            try:
                from mpp.server import Mpp
                from mpp.methods.tempo import ChargeIntent as TempoCharge
                from mpp.methods.tempo import tempo

                self._tempo_server = Mpp.create(
                    method=tempo(
                        intents={"charge": TempoCharge()},
                        recipient=tempo_recipient,
                        chain_id=self._tempo_chain_id,
                    ),
                    realm=self._realm,
                    secret_key=secret_key,
                )
                msg = (
                    f"mpp: Tempo enabled — {self._tempo_price} USDC/req on chain "
                    f"{self._tempo_chain_id} to {tempo_recipient}"
                )
                print(msg, flush=True)
                logger.info(msg)
            except Exception as e:
                print(f"mpp: Tempo init failed — {e!r}", flush=True)
                logger.warning(f"mpp: Tempo init failed — {e}")

        bn_id = os.environ.get("STRIPE_BN_ID")
        sk = os.environ.get("STRIPE_SECRET_KEY")
        if bn_id and sk:
            try:
                from mpp.server import Mpp
                from mpp.methods.stripe import ChargeIntent as StripeCharge
                from mpp.methods.stripe import stripe

                self._stripe_server = Mpp.create(
                    method=stripe(
                        intents={"charge": StripeCharge(secret_key=sk)},
                        network_id=bn_id,
                        payment_method_types=["card"],
                        currency="usd",
                        decimals=2,
                    ),
                    realm=self._realm,
                    secret_key=secret_key,
                )
                logger.info(
                    f"mpp: Stripe enabled — ${self._stripe_price}/req via BN {bn_id}"
                )
            except Exception as e:
                logger.warning(f"mpp: Stripe init failed — {e}")

        if not (self._tempo_server or self._stripe_server):
            logger.info("mpp: no method enabled — payment disabled, free tier only")

    async def _build_challenges(self) -> list[str]:
        """Return list of WWW-Authenticate values, one per enabled method."""
        from mpp._parsing import format_www_authenticate

        out: list[str] = []
        if self._tempo_server is not None:
            chal = await self._tempo_server.charge(
                authorization=None,
                amount=self._tempo_price,
                description="Coinnect quote: USDC micropayment",
            )
            out.append(format_www_authenticate(chal, self._realm))
        if self._stripe_server is not None:
            chal = await self._stripe_server.charge(
                authorization=None,
                amount=self._stripe_price,
                description="Coinnect quote: card payment",
            )
            out.append(format_www_authenticate(chal, self._realm))
        return out

    def _route_for_method(self, method: str) -> tuple[Any, str] | None:
        if method == "tempo" and self._tempo_server is not None:
            return self._tempo_server, self._tempo_price
        if method == "stripe" and self._stripe_server is not None:
            return self._stripe_server, self._stripe_price
        return None

    async def dispatch(self, request: Request, call_next):
        self._init()

        if request.url.path not in PAID_ROUTES:
            return await call_next(request)

        if not (self._tempo_server or self._stripe_server):
            return await call_next(request)

        auth = request.headers.get("Authorization")

        if auth and auth.lower().startswith("payment "):
            try:
                from mpp._parsing import parse_authorization

                credential = parse_authorization(auth)
                routed = self._route_for_method(credential.challenge.method)
                if routed is not None:
                    server, amount = routed
                    result = await server.charge(authorization=auth, amount=amount)
                    if isinstance(result, tuple):
                        _, receipt = result
                        request.state.mpp_paid = True
                        request.state.mpp_method = credential.challenge.method
                        response = await call_next(request)
                        try:
                            from mpp._parsing import format_payment_receipt

                            response.headers["Payment-Receipt"] = format_payment_receipt(receipt)
                        except Exception:
                            pass
                        response.headers["X-Payment-Status"] = "paid"
                        response.headers["X-Payment-Method"] = credential.challenge.method
                        response.headers["X-Payment-Amount"] = amount
                        return response
                    else:
                        logger.debug("mpp: verify failed, falling through to free tier")
            except Exception as e:
                logger.debug(f"mpp: parse/verify error — {e}")

        response = await call_next(request)

        if response.status_code == 429:
            try:
                challenges = await self._build_challenges()
                if challenges:
                    info_parts = []
                    if self._tempo_server is not None:
                        info_parts.append(f"tempo (${self._tempo_price} USDC)")
                    if self._stripe_server is not None:
                        info_parts.append(f"stripe (${self._stripe_price} USD)")
                    return Response(
                        status_code=402,
                        content=b'{"error":"payment_required","detail":"Free tier exhausted. Pay per request via MPP to bypass rate limits."}',
                        media_type="application/json",
                        headers={
                            "WWW-Authenticate": ", ".join(challenges),
                            "X-Payment-Info": "Pay via MPP: " + " or ".join(info_parts),
                        },
                    )
            except Exception as e:
                logger.warning(f"mpp: failed to build 402 challenges — {e}")

        return response
