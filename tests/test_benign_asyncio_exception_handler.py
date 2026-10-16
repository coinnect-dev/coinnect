"""Regression: uvloop's SSL-handshake Future noise must not reach GlitchTip as an error.

Outbound HTTPS calls (forex/exchange adapters) that get reset mid-TLS-handshake
leave an internal uvloop Future whose exception nobody retrieves. asyncio's
default exception handler logs that via the 'asyncio' logger at ERROR, and
Sentry's logging integration (event_level=ERROR) reports it as a real bug even
though there's no app frame involved — single-frame stacktrace entirely inside
uvloop/sslproto.pyx. GlitchTip auto-ine#6 (2026-10-16).
"""

import asyncio
import logging

from coinnect import main


def test_benign_future_exception_demoted_to_warning(caplog):
    loop = asyncio.new_event_loop()
    try:
        context = {
            "message": "Future exception was never retrieved",
            "exception": ConnectionResetError(),
            "future": object(),
        }
        with caplog.at_level(logging.WARNING, logger="coinnect.main"):
            main._benign_asyncio_exception_handler(loop, context)
        assert any(r.levelno == logging.WARNING for r in caplog.records)
        assert not any(r.levelno >= logging.ERROR for r in caplog.records)
    finally:
        loop.close()


def test_other_exceptions_still_reach_default_handler():
    loop = asyncio.new_event_loop()
    try:
        seen = []
        loop.default_exception_handler = seen.append
        context = {
            "message": "Future exception was never retrieved",
            "exception": ValueError("real bug, do not swallow"),
        }
        main._benign_asyncio_exception_handler(loop, context)
        assert seen == [context]
    finally:
        loop.close()


def test_other_messages_still_reach_default_handler():
    loop = asyncio.new_event_loop()
    try:
        seen = []
        loop.default_exception_handler = seen.append
        context = {
            "message": "Task exception was never retrieved",
            "exception": ConnectionResetError(),
        }
        main._benign_asyncio_exception_handler(loop, context)
        assert seen == [context]
    finally:
        loop.close()
