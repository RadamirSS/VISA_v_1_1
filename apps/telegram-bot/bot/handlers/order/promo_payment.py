from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.pricing import calculate_total
from bot.services.promo import normalize_code, validate_promo

from .shared import (
    AppointmentRequestState,
    OrderStatus,
    PaymentStatus,
    finalize_order,
    main_menu_keyboard,
    payment_confirmation_keyboard,
    payment_keyboard,
    payment_provider,
    promo_question_keyboard,
    promo_repository,
    render_summary,
    summary_keyboard,
)

router = Router()


@router.message(AppointmentRequestState.promo_question)
async def promo_question(message: Message, state: FSMContext) -> None:
    if message.text == "Да, ввести промокод":
        await state.set_state(AppointmentRequestState.promo_entry)
        await message.answer("Введите промокод текстом.")
        return
    if message.text != "Нет, продолжить к оплате":
        await message.answer("Выберите один из вариантов.", reply_markup=promo_question_keyboard())
        return
    data = await state.get_data()
    await state.update_data(payment_status_label="требуется оплата")
    await state.set_state(AppointmentRequestState.summary)
    await message.answer(render_summary(data), reply_markup=summary_keyboard())


@router.message(AppointmentRequestState.promo_entry)
async def promo_entry(message: Message, state: FSMContext) -> None:
    code = normalize_code(message.text)
    promo = promo_repository.get_by_code(code)
    data = await state.get_data()
    if promo is None:
        await message.answer(
            "Промокод не найден. Попробуйте еще раз или выберите оплату.",
            reply_markup=promo_question_keyboard(),
        )
        await state.set_state(AppointmentRequestState.promo_question)
        return
    result = validate_promo(
        promo,
        data["base_price_rub"] + data["additional_applicants_price_rub"],
        data["country_code"],
        data["time_window_code"],
    )
    if not result.valid:
        await message.answer(result.error or "Промокод недействителен.")
        return
    calc = calculate_total(
        base_price_rub=data["base_price_rub"],
        applicants_count=data["applicants_count"],
        additional_applicant_fee_rub=data["additional_applicant_fee_rub"],
        discount_rub=result.discount_rub,
    )
    payment_status_label = (
        "оплачено промокодом"
        if result.payment_status in {PaymentStatus.PAID.value, PaymentStatus.PAID_OFFLINE.value}
        else "требуется оплата"
    )
    await state.update_data(
        promo_code=result.normalized_code,
        promo_type=result.promo_type,
        discount_rub=calc.discount_rub,
        total_price_rub=calc.total_price_rub,
        payment_status_label=payment_status_label,
        promo_payment_status=result.payment_status,
    )
    data = await state.get_data()
    await state.set_state(AppointmentRequestState.summary)
    await message.answer(render_summary(data), reply_markup=summary_keyboard())


@router.message(AppointmentRequestState.payment)
async def payment_step(message: Message, state: FSMContext) -> None:
    if message.text == "🎟 Ввести промокод":
        await state.set_state(AppointmentRequestState.promo_entry)
        await message.answer("Введите промокод.")
        return
    if message.text == "💬 Я оплатил менеджеру наличными":
        data = await state.get_data()
        order_status = OrderStatus.AWAITING_MANAGER_CASH_CONFIRMATION.value
        if data["requires_manager_review"]:
            order_status = OrderStatus.REQUIRES_MANAGER_REVIEW.value
        await finalize_order(
            message,
            state,
            PaymentStatus.PENDING.value,
            order_status,
            payment_provider_name="offline_cash",
            manager_note="Ожидает подтверждения оплаты наличными менеджером.",
        )
        return
    if message.text == "💳 Оплатить":
        data = await state.get_data()
        response = await payment_provider.create_payment("draft", data["total_price_rub"])
        await state.update_data(provider_payment_id=response.payment_id)
        await state.set_state(AppointmentRequestState.payment_confirmation)
        await message.answer(
            f"{response.message}\nЭто тестовый сценарий: реального списания не происходит, карта и реальные реквизиты не нужны.\n"
            "Нажмите «✅ Подтвердить mock-оплату», чтобы завершить заявку в режиме разработки.",
            reply_markup=payment_confirmation_keyboard(),
        )
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание заявки отменено.", reply_markup=main_menu_keyboard())
        return
    await message.answer("Выберите действие из меню оплаты.", reply_markup=payment_keyboard())


@router.message(AppointmentRequestState.payment_confirmation)
async def payment_confirmation(message: Message, state: FSMContext) -> None:
    if message.text != "✅ Подтвердить mock-оплату":
        await message.answer(
            "Для завершения нажмите «✅ Подтвердить mock-оплату» или отмените сценарий.",
            reply_markup=payment_confirmation_keyboard(),
        )
        return
    data = await state.get_data()
    check = await payment_provider.check_payment(data["provider_payment_id"])
    order_status = (
        OrderStatus.REQUIRES_MANAGER_REVIEW.value
        if data["requires_manager_review"]
        else OrderStatus.PAID_WAITING_BOOKING.value
    )
    await finalize_order(
        message,
        state,
        PaymentStatus.PAID.value,
        order_status,
        payment_provider_name="mock",
        provider_payment_id=check.payment_id,
        paid_at=check.paid_at,
    )
