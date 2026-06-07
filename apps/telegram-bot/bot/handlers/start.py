from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.main import admin_menu_keyboard, main_menu_keyboard
from bot.texts.common import PRIVACY_NOTE

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Этот бот помогает создать заявку на поиск записи в визовый центр или консульство.\n\n"
        f"{PRIVACY_NOTE}\n\n"
        "Чтобы продолжить, подтвердите согласие на обработку данных и следуйте шагам меню.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    await message.answer("Главное меню", reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — начать работу\n"
        "/menu — открыть главное меню\n"
        "/status — проверить статус заявок\n"
        "/cancel — прервать текущий шаг\n"
        "/admin — меню менеджера для разрешенных аккаунтов"
    )


@router.message(Command("status"))
async def status_handler(message: Message) -> None:
    await message.answer("Здесь будет краткий статус ваших заявок и шагов обработки.")


@router.message(Command("cancel"))
async def cancel_handler(message: Message) -> None:
    await message.answer("Текущий сценарий остановлен. Можно вернуться в меню командой /menu.")


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer("Меню менеджера", reply_markup=admin_menu_keyboard())
