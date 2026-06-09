from pathlib import Path

from bot.config import Settings
from bot.services.access import is_admin


def make_settings(admin_ids: list[int]) -> Settings:
    return Settings(
        bot_token="x",
        bot_admin_ids=admin_ids,
        database_url="sqlite+aiosqlite:///./test.db",
        payment_provider="mock",
        payment_provider_token="",
        booking_api_base_url="",
        booking_api_token="",
        enable_sensitive_fields=False,
        sensitive_data_encryption_key="",
        default_currency="RUB",
        root_dir=Path("."),
        repo_root=Path("."),
    )


def test_admin_id_returns_true():
    assert is_admin(1, make_settings([1, 2])) is True


def test_non_admin_id_returns_false():
    assert is_admin(999, make_settings([1, 2])) is False


def test_empty_admin_list_denies_access():
    assert is_admin(1, make_settings([])) is False
