from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .shared import (
    AppointmentRequestState,
    build_manager_contact_notification,
    country_keyboard,
    ensure_registered,
    get_user_access_key,
    main_menu_keyboard,
    notify_admins,
    order_repository,
    order_start_text,
    settings,
    support_request_repository,
    user_has_valid_access_key,
)

router = Router()


@router.message(F.text == "📝 Создать заявку на запись")
async def create_order_entry(message: Message, state: FSMContext) -> None:
    user = ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    if not user_has_valid_access_key(message.from_user.id):
        await message.answer(
            "Создание заявки доступно после ввода ключа доступа от менеджера. Если вы уже оплатили услугу, запросите ключ у менеджера."
        )
        return
    access_key = get_user_access_key(message.from_user.id)
    await state.clear()
    await state.update_data(
        user_id=user.id,
        access_key_code=access_key.code if access_key else None,
        access_key_id=access_key.id if access_key else None,
        service_type=access_key.service_type if access_key else "appointment_request",
    )
    await state.set_state(AppointmentRequestState.country)
    await message.answer(order_start_text(), reply_markup=country_keyboard())


@router.message(F.text == "👤 Связаться с менеджером")
async def contact_manager(message: Message) -> None:
    user = ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    support_request = support_request_repository.create(
        user_id=user.id,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        message="Клиент запросил связь с менеджером.",
    )
    await notify_admins(
        message.bot,
        settings,
        build_manager_contact_notification(message.from_user.id, message.from_user.username)
        + f"\nЗапрос: {support_request.id}",
    )
    await message.answer(
        "Запрос отправлен менеджеру. Он свяжется с вами в Telegram или через этот бот.",
        reply_markup=main_menu_keyboard(),
    )
