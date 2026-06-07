from __future__ import annotations

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
