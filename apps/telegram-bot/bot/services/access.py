from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from bot.config import Settings

ADMIN_DENIED_TEXT = "У вас нет доступа к менеджерскому меню."


def is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.bot_admin_ids


async def deny_admin_message(message: Message) -> None:
    await message.answer(ADMIN_DENIED_TEXT)


async def deny_admin_callback(callback: CallbackQuery) -> None:
    await callback.answer(ADMIN_DENIED_TEXT, show_alert=True)
