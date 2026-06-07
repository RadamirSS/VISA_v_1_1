from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать заявку на запись")],
            [KeyboardButton(text="📌 Мои заявки"), KeyboardButton(text="🎟 Ввести промокод")],
            [KeyboardButton(text="💳 Оплата"), KeyboardButton(text="❓ Как это работает")],
            [KeyboardButton(text="👤 Связаться с менеджером")],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Новые заявки"), KeyboardButton(text="🔎 Найти заявку")],
            [KeyboardButton(text="🎟 Создать промокод"), KeyboardButton(text="✅ Подтвердить оплату наличными")],
            [KeyboardButton(text="🔄 Изменить статус заявки"), KeyboardButton(text="📊 Статистика")],
        ],
        resize_keyboard=True,
    )
