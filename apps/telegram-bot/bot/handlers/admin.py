from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: message.text == "📥 Новые заявки")
async def list_new_orders(message: Message) -> None:
    await message.answer("Здесь будет список новых заявок в формате менеджерского обзора.")


@router.message(lambda message: message.text == "🎟 Создать промокод")
async def create_promo_entry(message: Message) -> None:
    await message.answer("Здесь запускается рабочий сценарий менеджера для создания промокода.")
