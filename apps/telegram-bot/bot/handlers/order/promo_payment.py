from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .shared import AppointmentRequestState

router = Router()


@router.message(AppointmentRequestState.promo_entry)
async def promo_entry(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Промокоды не используются как основной способ доступа. Оплата проходит через менеджера агентства, а доступ к заявке открывается ключом доступа."
    )
