from pathlib import Path

from bot.config import Settings
from bot.services.sensitive_fields import telegram_sensitive_collection_enabled


def test_applicant_flow_never_collects_passport_in_telegram():
    settings = Settings(
        bot_token="x",
        bot_admin_ids=[],
        database_url="sqlite+aiosqlite:///./test.db",
        payment_provider="mock",
        payment_provider_token="",
        booking_api_base_url="",
        booking_api_token="",
        enable_sensitive_fields=True,
        sensitive_data_encryption_key="configured-but-unused",
        default_currency="RUB",
        root_dir=Path("."),
        repo_root=Path("."),
    )
    assert telegram_sensitive_collection_enabled(settings) is False
