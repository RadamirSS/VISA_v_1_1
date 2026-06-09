from __future__ import annotations

from bot.config import get_settings
from bot.services.sensitive_fields import (
    PASSPORT_DATA_GUARD_WARNING,
    PASSPORT_DATA_UNAVAILABLE_TEXT,
    sensitive_fields_enabled,
    sensitive_fields_warning,
    telegram_sensitive_collection_enabled,
)


def test_sensitive_fields_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_SENSITIVE_FIELDS", raising=False)
    monkeypatch.delenv("SENSITIVE_DATA_ENCRYPTION_KEY", raising=False)
    settings = get_settings()
    assert settings.enable_sensitive_fields is False
    assert sensitive_fields_enabled(settings) is False
    assert telegram_sensitive_collection_enabled(settings) is False
    assert sensitive_fields_warning(settings) == PASSPORT_DATA_UNAVAILABLE_TEXT


def test_passport_collection_remains_disabled_with_flags_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_SENSITIVE_FIELDS", "true")
    monkeypatch.setenv("SENSITIVE_DATA_ENCRYPTION_KEY", "placeholder-key")
    settings = get_settings()
    assert settings.enable_sensitive_fields is True
    assert sensitive_fields_enabled(settings) is False
    assert telegram_sensitive_collection_enabled(settings) is False
    assert sensitive_fields_warning(settings) == PASSPORT_DATA_GUARD_WARNING
