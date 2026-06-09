from __future__ import annotations

from bot.config import Settings

PASSPORT_DATA_UNAVAILABLE_TEXT = (
    "Паспортные данные и документы менеджер запросит отдельно через защищенный канал, если они понадобятся. "
    "В Telegram-боте паспортные данные не собираются."
)
PASSPORT_DATA_GUARD_WARNING = (
    "Сбор паспортных данных в Telegram отключен. Для production нужен отдельный защищенный backend/storage flow."
)


def telegram_sensitive_collection_enabled(settings: Settings) -> bool:
    del settings
    return False


def sensitive_fields_enabled(settings: Settings) -> bool:
    return telegram_sensitive_collection_enabled(settings)


def sensitive_fields_warning(settings: Settings) -> str:
    if settings.enable_sensitive_fields or settings.sensitive_data_encryption_key.strip():
        return PASSPORT_DATA_GUARD_WARNING
    return PASSPORT_DATA_UNAVAILABLE_TEXT
