from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен, продолжить", callback_data="consent:accept")],
            [InlineKeyboardButton(text="❓ Подробнее", callback_data="consent:details")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="consent:cancel")],
        ]
    )


def admin_order_actions_keyboard(public_number: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Взять в работу", callback_data=f"admin:take:{public_number}")],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"admin:status:{public_number}")],
            [InlineKeyboardButton(text="💳 Подтвердить оплату наличными", callback_data=f"admin:cash:{public_number}")],
            [InlineKeyboardButton(text="✉️ Написать клиенту шаблонное сообщение", callback_data=f"admin:message:{public_number}")],
            [InlineKeyboardButton(text="❌ Отменить заявку", callback_data=f"admin:cancel:{public_number}")],
        ]
    )


def admin_status_keyboard(public_number: str) -> InlineKeyboardMarkup:
    statuses = [
        ("paid_waiting_booking", "Ожидает обработки"),
        ("sent_to_booking_provider", "Передана в обработку"),
        ("slot_found", "Слот найден"),
        ("slot_confirmation_pending", "Ждет подтверждения"),
        ("booked", "Записано"),
        ("needs_user_action", "Нужно действие клиента"),
        ("failed", "Неуспешно"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"admin:setstatus:{public_number}:{value}")]
            for value, label in statuses
        ]
    )
