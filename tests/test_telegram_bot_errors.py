"""Transient Telegram network errors are a WARNING, not an ERROR with traceback."""
import asyncio
import logging
from types import SimpleNamespace

import pytest

pytest.importorskip("telegram")

from telegram.error import BadRequest, NetworkError, TimedOut  # noqa: E402

from coinnect.telegram_bot import on_error  # noqa: E402


def _run(err):
    asyncio.run(on_error(None, SimpleNamespace(error=err)))


@pytest.mark.parametrize("err", [NetworkError("httpx.ReadError: "), TimedOut()])
def test_network_errors_are_warnings(err, caplog):
    with caplog.at_level(logging.DEBUG, logger="coinnect.telegram"):
        _run(err)
    levels = [r.levelno for r in caplog.records]
    assert levels == [logging.WARNING]
    assert caplog.records[0].exc_info is None


def test_other_errors_stay_errors_with_traceback(caplog):
    with caplog.at_level(logging.DEBUG, logger="coinnect.telegram"):
        _run(BadRequest("Message is not modified"))
    assert [r.levelno for r in caplog.records] == [logging.ERROR]
    assert caplog.records[0].exc_info is not None


def test_non_telegram_errors_stay_errors(caplog):
    with caplog.at_level(logging.DEBUG, logger="coinnect.telegram"):
        _run(KeyError("from_currency"))
    assert [r.levelno for r in caplog.records] == [logging.ERROR]
