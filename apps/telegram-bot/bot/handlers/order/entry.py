from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .shared import (
    AppointmentRequestState,
    build_manager_contact_notification,
    country_keyboard,
    ensure_registered,
    main_menu_keyboard,
    notify_admins,
    order_repository,
    order_start_text,
    settings,
)

router = Router()


@router.message(F.text == "📝 Создать заявку на запись")
async def create_order_entry(message: Message, state: FSMContext) -> None:
    user = ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    await state.clear()
    await state.update_data(user_id=user.id)
    await state.set_state(AppointmentRequestState.country)
    await message.answer(order_start_text(), reply_markup=country_keyboard())


@router.message(F.text == "👤 Связаться с менеджером")
async def contact_manager(message: Message) -> None:
    await notify_admins(
        message.bot,
        settings,
        build_manager_contact_notification(message.from_user.id, message.from_user.username),
    )
    await message.answer("Менеджер получит запрос на связь и свяжется с вами вручную.", reply_markup=main_menu_keyboard())


@router.message(F.text == "🎟 Ввести промокод")
async def promo_info(message: Message) -> None:
    await message.answer("Промокод применяется во время создания заявки. Если у вас уже есть код, начните новую заявку через «📝 Создать заявку на запись».")


@router.message(F.text == "💳 Оплата")
async def payment_info(message: Message) -> None:
    orders = order_repository.list_user_orders(message.from_user.id)
    pending = [item for item in orders if item["payment_status"] == "pending"]
    if not pending:
        await message.answer("Отдельных неоплаченных заявок сейчас нет. Оплата или подтверждение наличными доступны в сценарии создания заявки.")
        return
    await message.answer("\n\n".join(f"{item['public_number']} — {item['payment_status']} / {item['order_status']}" for item in pending))
