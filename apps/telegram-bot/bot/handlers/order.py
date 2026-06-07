from aiogram import Router
from aiogram.types import Message

from bot.keyboards.main import main_menu_keyboard
from bot.texts.common import SENSITIVE_NOTE

router = Router()


@router.message(lambda message: message.text == "📝 Создать заявку на запись")
async def create_order_entry(message: Message) -> None:
    await message.answer(
        "Начинаем создание заявки. Сначала выберите страну, затем город подачи, цель поездки и желаемое окно поиска записи.\n\n"
        f"{SENSITIVE_NOTE}",
        reply_markup=main_menu_keyboard(),
    )


@router.message(lambda message: message.text == "❓ Как это работает")
async def how_it_works(message: Message) -> None:
    await message.answer(
        "Мы создадим заявку на поиск записи. Доступность слотов зависит от внешних систем. "
        "Финальное подтверждение записи появится после обработки менеджером или будущим booking API."
    )


@router.message(lambda message: message.text == "👤 Связаться с менеджером")
async def contact_manager(message: Message) -> None:
    await message.answer("Менеджер получит уведомление о запросе на связь. До подключения реальных уведомлений используйте согласованный рабочий контакт.")
