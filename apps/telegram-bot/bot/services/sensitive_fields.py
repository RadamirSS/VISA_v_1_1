from __future__ import annotations

from bot.config import Settings

PASSPORT_DATA_UNAVAILABLE_TEXT = (
    "Паспортные данные менеджер запросит отдельно через защищенный канал, если они понадобятся."
)
PASSPORT_DATA_GUARD_WARNING = (
    "Сбор паспортных данных в боте отключен: не настроен ключ шифрования для чувствительных данных. "
    "Менеджер запросит их отдельно через защищенный канал, если это потребуется."
)


def sensitive_fields_enabled(settings: Settings) -> bool:
    return settings.enable_sensitive_fields and bool(settings.sensitive_data_encryption_key.strip())


def sensitive_fields_warning(settings: Settings) -> str:
    if settings.enable_sensitive_fields and not settings.sensitive_data_encryption_key.strip():
        return PASSPORT_DATA_GUARD_WARNING
    return PASSPORT_DATA_UNAVAILABLE_TEXT
