from pathlib import Path

from bot.config import Settings
from bot.services.access import is_admin


def test_admin_guard_allows_only_configured_ids():
    settings = Settings(
        bot_token="x",
        bot_admin_ids=[1, 2],
        database_url="sqlite+aiosqlite:///./test.db",
        payment_provider="mock",
        payment_provider_token="",
        booking_api_base_url="",
        booking_api_token="",
        enable_sensitive_fields=False,
        default_currency="RUB",
        root_dir=Path("."),
        repo_root=Path("."),
    )
    assert is_admin(1, settings) is True
    assert is_admin(999, settings) is False
