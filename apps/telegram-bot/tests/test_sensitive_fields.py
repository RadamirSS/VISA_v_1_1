from __future__ import annotations

from bot.config import get_settings
from bot.services.sensitive_fields import (
    PASSPORT_DATA_GUARD_WARNING,
    sensitive_fields_enabled,
    sensitive_fields_warning,
)


def test_sensitive_fields_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_SENSITIVE_FIELDS", raising=False)
    monkeypatch.delenv("SENSITIVE_DATA_ENCRYPTION_KEY", raising=False)
    settings = get_settings()
    assert settings.enable_sensitive_fields is False
    assert sensitive_fields_enabled(settings) is False


def test_passport_collection_blocked_without_encryption_key(monkeypatch):
    monkeypatch.setenv("ENABLE_SENSITIVE_FIELDS", "true")
    monkeypatch.delenv("SENSITIVE_DATA_ENCRYPTION_KEY", raising=False)
    settings = get_settings()
    assert settings.enable_sensitive_fields is True
    assert sensitive_fields_enabled(settings) is False
    assert sensitive_fields_warning(settings) == PASSPORT_DATA_GUARD_WARNING
