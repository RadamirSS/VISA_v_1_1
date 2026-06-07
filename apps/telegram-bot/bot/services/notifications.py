from __future__ import annotations

from aiogram import Bot

from bot.config import Settings
from bot.models import BookingOrder


def build_new_order_notification(order: BookingOrder) -> str:
    return (
        f"Новая заявка #{order.public_number}\n"
        f"Страна: {order.country_name_ru}\n"
        f"Город подачи: {order.submission_city}\n"
        f"Окно поиска: {order.time_window_code}\n"
        f"Оплата: {order.payment_status}\n"
        f"Статус: {order.order_status}"
    )


def build_manager_contact_notification(telegram_id: int, username: str | None) -> str:
    lines = [
        "Клиент запросил связь с менеджером.",
        f"Telegram ID: {telegram_id}",
    ]
    if username:
        lines.append(f"Username: @{username}")
    return "\n".join(lines)


async def notify_admins(bot: Bot, settings: Settings, text: str) -> None:
    for admin_id in settings.bot_admin_ids:
        await bot.send_message(admin_id, text)
