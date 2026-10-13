"""The bot token travels in the Telegram URL path; httpx must not log it at INFO."""
import logging

import pytest

pytest.importorskip("telegram")


def test_httpx_request_urls_not_logged_at_info():
    import coinnect.telegram_bot  # noqa: F401  (configures logging on import)

    # Check the logger's own level: under pytest the root logger already has
    # handlers, so basicConfig(level=INFO) is a no-op and isEnabledFor would pass
    # even without the fix.
    for name in ("httpx", "httpcore"):
        assert logging.getLogger(name).level >= logging.WARNING
