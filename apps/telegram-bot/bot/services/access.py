from __future__ import annotations

from bot.config import Settings


def is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.bot_admin_ids
