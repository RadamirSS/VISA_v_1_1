from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import get_settings
from bot.repositories.orders import OrderRepository
from bot.services.trust_display import order_status_label, payment_status_label

router = Router()
settings = get_settings()
order_repository = OrderRepository(settings.database_url)


def _render_orders(orders: list[dict]) -> str:
    return "\n\n".join(
        (
            f"{order['public_number']}\n"
            f"Страна: {order['country_name_ru']}\n"
            f"Город: {order['submission_city']}\n"
            f"Окно: {order['time_window_code']}\n"
            f"Оплата: {payment_status_label(order['payment_status'])}\n"
            f"Статус: {order_status_label(order['order_status'])}\n"
            f"Создано: {order['created_at'][:10]}"
        )
        for order in orders
    )


@router.message(Command("status"))
@router.message(F.text == "📌 Мои заявки")
async def status_handler(message: Message) -> None:
    orders = order_repository.list_user_orders(message.from_user.id)
    if not orders:
        await message.answer(
            "У вас пока нет сохраненных заявок. Создать новую можно через кнопку «📝 Создать заявку на запись»."
        )
        return
    await message.answer(_render_orders(orders))
