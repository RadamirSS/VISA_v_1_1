from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.pricing import calculate_total

from .shared import (
    AppointmentRequestState,
    PURPOSE_OPTIONS,
    SPECIAL_COUNTRIES,
    applicant_count_keyboard,
    consulates,
    countries,
    country_keyboard,
    find_consulates_by_country,
    find_country_by_name,
    price_keyboard,
    price_tiers,
    prompt_next_applicant,
    purpose_keyboard,
    simple_keyboard,
    start_consultation_order,
    ensure_registered,
    validate_access_key,
    get_user_access_key,
)

router = Router()


@router.message(AppointmentRequestState.country)
async def order_country(message: Message, state: FSMContext) -> None:
    selected = message.text.strip()
    user = ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    if selected in SPECIAL_COUNTRIES:
        await start_consultation_order(message, user, selected)
        await state.clear()
        return
    country = find_country_by_name(countries(), selected)
    if country is None:
        await message.answer("Выберите страну из списка.", reply_markup=country_keyboard())
        return
    access_key = get_user_access_key(message.from_user.id)
    validation = validate_access_key(access_key, message.from_user.id, country_code=country.code)
    if not validation.valid:
        await message.answer(validation.error or "Ключ доступа не подходит для выбранной страны.")
        return
    matched_consulates = find_consulates_by_country(consulates(), country.code)
    if not matched_consulates:
        await start_consultation_order(message, user, selected)
        await state.clear()
        return
    await state.update_data(country_code=country.code, country_name_ru=country.name_ru)
    await state.set_state(AppointmentRequestState.city)
    rows = [[f"{item.city} — {item.provider}"] for item in matched_consulates]
    await message.answer("Выберите город подачи и визовый центр.", reply_markup=simple_keyboard(*rows))


@router.message(AppointmentRequestState.city)
async def order_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    matched_consulates = find_consulates_by_country(consulates(), data["country_code"])
    selected = next((item for item in matched_consulates if f"{item.city} — {item.provider}" == message.text.strip()), None)
    if selected is None:
        rows = [[f"{item.city} — {item.provider}"] for item in matched_consulates]
        await message.answer("Выберите город подачи из списка.", reply_markup=simple_keyboard(*rows))
        return
    await state.update_data(submission_city=selected.city, provider=selected.provider)
    await state.set_state(AppointmentRequestState.purpose)
    if selected.verification_status == "needs_verification":
        await message.answer("Доступность этого города менеджер уточнит перед началом работы.")
    await message.answer("Выберите цель поездки.", reply_markup=purpose_keyboard())


@router.message(AppointmentRequestState.purpose)
async def order_purpose(message: Message, state: FSMContext) -> None:
    if message.text.strip() not in PURPOSE_OPTIONS:
        await message.answer("Выберите цель поездки кнопкой из списка.", reply_markup=purpose_keyboard())
        return
    await state.update_data(visa_purpose=message.text.strip())
    await state.set_state(AppointmentRequestState.time_window)
    tier_lines = [
        f"{prefix} {tier.label_ru}\n{tier.description_ru}\n{tier.price_rub} ₽"
        for prefix, tier in zip(["⚡", "🔥", "📅", "🗓", "🌿"], price_tiers(), strict=False)
    ]
    await message.answer("Выберите желаемое окно поиска:\n\n" + "\n\n".join(tier_lines), reply_markup=price_keyboard())


@router.message(AppointmentRequestState.time_window)
async def order_time_window(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    label = raw.split(" ", 1)[1] if " " in raw else raw
    tier = next((item for item in price_tiers() if item.label_ru == label), None)
    if tier is None:
        await message.answer("Выберите окно поиска из списка.", reply_markup=price_keyboard())
        return
    await state.update_data(
        time_window_code=tier.code,
        time_window_label=tier.label_ru,
        base_price_rub=tier.price_rub,
        additional_applicant_fee_rub=tier.additional_applicant_price_rub,
    )
    await state.set_state(AppointmentRequestState.applicants_count)
    await message.answer("Сколько заявителей будет в заявке?", reply_markup=applicant_count_keyboard())


@router.message(AppointmentRequestState.applicants_count)
async def order_applicants_count(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    if raw == "Ввести вручную":
        await state.set_state(AppointmentRequestState.applicants_manual_count)
        await message.answer("Введите количество заявителей числом.")
        return
    mapping = {"1 заявитель": 1, "2 заявителя": 2, "3 заявителя": 3, "4 заявителя": 4, "5+": 5}
    if raw not in mapping:
        await message.answer("Выберите количество заявителей кнопкой.", reply_markup=applicant_count_keyboard())
        return
    applicants_count = mapping[raw]
    data = await state.get_data()
    calc = calculate_total(
        base_price_rub=data["base_price_rub"],
        applicants_count=applicants_count,
        additional_applicant_fee_rub=data["additional_applicant_fee_rub"],
    )
    access_key = get_user_access_key(message.from_user.id)
    requires_manager_review = calc.requires_manager_review or (
        access_key is not None and access_key.max_applicants is not None and applicants_count > access_key.max_applicants
    )
    await state.update_data(
        applicants_count=applicants_count,
        base_price_rub=calc.base_price_rub,
        additional_applicants_price_rub=calc.additional_applicants_price_rub,
        discount_rub=calc.discount_rub,
        total_price_rub=calc.total_price_rub,
        requires_manager_review=requires_manager_review,
        applicants=[],
        current_applicant_index=0,
    )
    await prompt_next_applicant(message, state)


@router.message(AppointmentRequestState.applicants_manual_count)
async def order_applicants_manual_count(message: Message, state: FSMContext) -> None:
    try:
        applicants_count = int(message.text.strip())
    except ValueError:
        await message.answer("Введите количество заявителей числом.")
        return
    if applicants_count < 1:
        await message.answer("Количество заявителей должно быть больше нуля.")
        return
    data = await state.get_data()
    calc = calculate_total(
        base_price_rub=data["base_price_rub"],
        applicants_count=applicants_count,
        additional_applicant_fee_rub=data["additional_applicant_fee_rub"],
    )
    access_key = get_user_access_key(message.from_user.id)
    requires_manager_review = calc.requires_manager_review or (
        access_key is not None and access_key.max_applicants is not None and applicants_count > access_key.max_applicants
    )
    await state.update_data(
        applicants_count=applicants_count,
        base_price_rub=calc.base_price_rub,
        additional_applicants_price_rub=calc.additional_applicants_price_rub,
        discount_rub=calc.discount_rub,
        total_price_rub=calc.total_price_rub,
        requires_manager_review=requires_manager_review,
        applicants=[],
        current_applicant_index=0,
    )
    await prompt_next_applicant(message, state)
