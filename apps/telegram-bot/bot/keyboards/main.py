from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


def main_menu_keyboard(miniapp_url: str | None = None) -> ReplyKeyboardMarkup:
    cabinet_button = (
        KeyboardButton(text="📋 Открыть личный кабинет", web_app=WebAppInfo(url=miniapp_url))
        if miniapp_url
        else KeyboardButton(text="📋 Открыть личный кабинет")
    )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Ввести ключ доступа")],
            [cabinet_button],
            [KeyboardButton(text="📝 Создать заявку на запись")],
            [KeyboardButton(text="📌 Мои заявки"), KeyboardButton(text="❓ Как это работает")],
            [KeyboardButton(text="👤 Связаться с менеджером")],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Новые заявки"), KeyboardButton(text="🔎 Найти заявку")],
            [KeyboardButton(text="📅 Отправить даты"), KeyboardButton(text="✅ Подтвердить запись")],
            [KeyboardButton(text="📎 Документы по заявке")],
            [KeyboardButton(text="🔑 Создать ключ доступа"), KeyboardButton(text="📨 Запросы клиентов")],
            [KeyboardButton(text="🎟 Создать промокод"), KeyboardButton(text="🔄 Изменить статус заявки")],
            [KeyboardButton(text="✅ Подтвердить оплату наличными"), KeyboardButton(text="📊 Статистика")],
        ],
        resize_keyboard=True,
    )


def simple_keyboard(*rows: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item) for item in row] for row in rows],
        resize_keyboard=True,
    )
