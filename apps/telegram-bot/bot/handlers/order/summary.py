from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .shared import (
    AppointmentRequestState,
    OrderStatus,
    PaymentStatus,
    country_keyboard,
    finalize_order,
    main_menu_keyboard,
    render_summary,
    summary_keyboard,
)

router = Router()


@router.message(AppointmentRequestState.summary)
async def summary_step(message: Message, state: FSMContext) -> None:
    if message.text == "🎟 Ввести другой промокод":
        data = await state.get_data()
        await message.answer(render_summary(data), reply_markup=summary_keyboard())
        return
    if message.text == "✏️ Изменить данные":
        await state.clear()
        await state.set_state(AppointmentRequestState.country)
        await message.answer("Хорошо, начнем заново с выбора страны.", reply_markup=country_keyboard())
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание заявки отменено.", reply_markup=main_menu_keyboard())
        return
    if message.text != "✅ Подтвердить заявку":
        data = await state.get_data()
        await message.answer(render_summary(data), reply_markup=summary_keyboard())
        return
    data = await state.get_data()
    order_status = (
        OrderStatus.REQUIRES_MANAGER_REVIEW.value
        if data["requires_manager_review"]
        else OrderStatus.PAID_WAITING_BOOKING.value
    )
    await finalize_order(
        message,
        state,
        PaymentStatus.PAID_OFFLINE.value,
        order_status,
        payment_provider_name="offline_manager",
        provider_payment_id=data.get("access_key_code"),
        manager_note="Оплата подтверждена агентством через ключ доступа.",
    )
