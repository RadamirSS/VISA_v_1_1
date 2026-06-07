from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import get_settings
from bot.keyboards.main import main_menu_keyboard, simple_keyboard
from bot.models import OrderStatus, PaymentStatus, User
from bot.repositories.orders import OrderRepository
from bot.repositories.promos import PromoRepository
from bot.repositories.users import UserRepository
from bot.services.config_loader import (
    find_consulates_by_country,
    find_country_by_name,
    load_consulates,
    load_countries,
    load_price_tiers,
)
from bot.services.notifications import build_manager_contact_notification, build_new_order_notification, notify_admins
from bot.services.order_factory import OrderInput, create_applicant, create_order, create_payment
from bot.services.payment_provider import MockPaymentProvider
from bot.services.pricing import calculate_total, render_price_summary
from bot.services.promo import normalize_code, validate_promo
from bot.states.order import AppointmentRequestState
from bot.texts.common import SENSITIVE_NOTE

router = Router()
settings = get_settings()
user_repository = UserRepository(settings.database_url)
order_repository = OrderRepository(settings.database_url)
promo_repository = PromoRepository(settings.database_url)
payment_provider = MockPaymentProvider()

SPECIAL_COUNTRIES = {"Другая страна", "Не знаю, нужна консультация"}
PURPOSE_OPTIONS = [
    "Туризм",
    "Бизнес",
    "Посещение родственников/друзей",
    "Учеба / мероприятие",
    "Медицинская цель",
    "Другое / уточнить с менеджером",
]


def _countries():
    return load_countries(settings.repo_root)


def _consulates():
    return load_consulates(settings.repo_root)


def _price_tiers():
    return load_price_tiers(settings.repo_root)


def _country_keyboard():
    names = [country.name_ru for country in _countries()]
    return simple_keyboard(names[:3], names[3:], ["Другая страна", "Не знаю, нужна консультация"])


def _purpose_keyboard():
    return simple_keyboard(PURPOSE_OPTIONS[:2], PURPOSE_OPTIONS[2:4], PURPOSE_OPTIONS[4:])


def _price_keyboard():
    tiers = _price_tiers()
    return simple_keyboard(
        [f"⚡ {tiers[0].label_ru}"],
        [f"🔥 {tiers[1].label_ru}"],
        [f"📅 {tiers[2].label_ru}"],
        [f"🗓 {tiers[3].label_ru}"],
        [f"🌿 {tiers[4].label_ru}"],
    )


def _applicant_count_keyboard():
    return simple_keyboard(["1 заявитель", "2 заявителя"], ["3 заявителя", "4 заявителя"], ["5+", "Ввести вручную"])


def _promo_question_keyboard():
    return simple_keyboard(["Да, ввести промокод"], ["Нет, продолжить к оплате"])


def _summary_keyboard():
    return simple_keyboard(["✅ Подтвердить заявку"], ["🎟 Ввести другой промокод", "✏️ Изменить данные"], ["❌ Отмена"])


def _payment_keyboard():
    return simple_keyboard(["💳 Оплатить"], ["🎟 Ввести промокод"], ["💬 Я оплатил менеджеру наличными"], ["❌ Отмена"])


def _payment_confirmation_keyboard():
    return simple_keyboard(["✅ Подтвердить mock-оплату"], ["❌ Отмена"])


def _skip_keyboard():
    return simple_keyboard(["Пропустить"])


def _ensure_registered(message: Message) -> User | None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user is None or not user_repository.is_registered(user):
        return None
    return user


async def _start_consultation_order(message: Message, user: User, selected_country: str) -> None:
    sequence = order_repository.next_sequence()
    order = create_order(
        OrderInput(
            user_id=user.id,
            country_code="CONSULT",
            country_name_ru=selected_country,
            submission_city="Консультация с менеджером",
            provider="manual_consultation",
            visa_purpose="Нужна консультация",
            time_window_code="consultation",
            applicants_count=1,
            base_price_rub=0,
            additional_applicants_price_rub=0,
            discount_rub=0,
            total_price_rub=0,
            promo_code=None,
            payment_status=PaymentStatus.NOT_REQUIRED.value,
            order_status=OrderStatus.REQUIRES_MANAGER_REVIEW.value,
            requires_manager_review=True,
            manager_note="Консультационный запрос без полной booking-flow логики",
        ),
        sequence=sequence,
    )
    applicant = create_applicant(
        order_id=order.id,
        last_name=user.last_name or "",
        first_name=user.first_name or "",
        patronymic=user.patronymic,
        birth_date=user.birth_date or "Не указано",
        citizenship=user.citizenship or "Россия",
        current_location=user.current_location,
        relationship=None,
    )
    order_repository.create_order(order, [applicant], None, actor_type="user", actor_id=str(message.from_user.id))
    await notify_admins(message.bot, settings, build_new_order_notification(order))
    await message.answer(
        f"Мы создали консультационный запрос.\nНомер заявки: {order.public_number}\n"
        "Менеджер уточнит страну подачи и возможный следующий шаг вручную.",
        reply_markup=main_menu_keyboard(),
    )


def _render_summary(data: dict[str, Any]) -> str:
    promo_text = data.get("promo_code") or "нет"
    payment_text = data.get("payment_status_label") or "требуется оплата"
    price_text = render_price_summary(
        data["base_price_rub"],
        data["additional_applicants_price_rub"],
        data["discount_rub"],
        data["total_price_rub"],
    )
    return (
        f"Страна: {data['country_name_ru']}\n"
        f"Город подачи: {data['submission_city']}\n"
        f"Цель: {data['visa_purpose']}\n"
        f"Срок поиска: {data['time_window_label']}\n"
        f"Заявителей: {data['applicants_count']}\n"
        "Стоимость:\n"
        f"{price_text}\n"
        f"Промокод: {promo_text}\n"
        f"Статус оплаты: {payment_text}"
    )


def _build_order_payload(state_data: dict[str, Any], payment_status: str, order_status: str, manager_note: str | None = None) -> tuple[Any, Any]:
    sequence = order_repository.next_sequence()
    order = create_order(
        OrderInput(
            user_id=state_data["user_id"],
            country_code=state_data["country_code"],
            country_name_ru=state_data["country_name_ru"],
            submission_city=state_data["submission_city"],
            provider=state_data["provider"],
            visa_purpose=state_data["visa_purpose"],
            time_window_code=state_data["time_window_code"],
            applicants_count=state_data["applicants_count"],
            base_price_rub=state_data["base_price_rub"],
            additional_applicants_price_rub=state_data["additional_applicants_price_rub"],
            discount_rub=state_data["discount_rub"],
            total_price_rub=state_data["total_price_rub"],
            promo_code=state_data.get("promo_code"),
            payment_status=payment_status,
            order_status=order_status,
            requires_manager_review=state_data["requires_manager_review"],
            user_comment=state_data.get("user_comment"),
            manager_note=manager_note,
        ),
        sequence=sequence,
    )
    applicants = [
        create_applicant(
            order_id=order.id,
            last_name=item["last_name"],
            first_name=item["first_name"],
            patronymic=item.get("patronymic"),
            birth_date=item["birth_date"],
            citizenship=item["citizenship"],
            current_location=item.get("current_location"),
            relationship=item.get("relationship"),
            passport_number_encrypted=item.get("passport_number_encrypted"),
            passport_expiry_date=item.get("passport_expiry_date"),
        )
        for item in state_data["applicants"]
    ]
    return order, applicants


async def _finalize_order(message: Message, state: FSMContext, payment_status: str, order_status: str, payment_provider_name: str = "mock", provider_payment_id: str | None = None, paid_at: str | None = None, manager_note: str | None = None) -> None:
    data = await state.get_data()
    order, applicants = _build_order_payload(data, payment_status, order_status, manager_note)
    payment = None
    if payment_status != PaymentStatus.NOT_REQUIRED.value:
        payment = create_payment(
            order_id=order.id,
            provider=payment_provider_name,
            amount_rub=data["total_price_rub"],
            status=payment_status,
            provider_payment_id=provider_payment_id,
            paid_at=paid_at,
        )
    order_repository.create_order(order, applicants, payment, actor_type="user", actor_id=str(message.from_user.id))
    if data.get("promo_code"):
        promo_repository.increment_used_count(data["promo_code"])
    await notify_admins(message.bot, settings, build_new_order_notification(order))
    await state.clear()
    await message.answer(
        "Заявка создана.\n"
        f"Номер заявки: {order.public_number}\n"
        f"Страна: {order.country_name_ru}\n"
        f"Город подачи: {order.submission_city}\n"
        f"Срок поиска: {data['time_window_label']}\n"
        f"Статус: {order.payment_status}, {order.order_status}.\n"
        "Мы не гарантируем наличие свободных слотов. Менеджер начнет обработку и сообщит о следующих шагах.",
        reply_markup=main_menu_keyboard(),
    )


async def _prompt_next_applicant(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    current_index = data.get("current_applicant_index", 0)
    applicants_count = data["applicants_count"]
    if current_index >= applicants_count:
        await state.set_state(AppointmentRequestState.promo_question)
        await message.answer("У вас есть промокод от менеджера?", reply_markup=_promo_question_keyboard())
        return
    await state.set_state(AppointmentRequestState.applicant_last_name)
    await message.answer(f"Заявитель {current_index + 1} из {applicants_count}. Укажите фамилию.")


@router.message(F.text == "📝 Создать заявку на запись")
async def create_order_entry(message: Message, state: FSMContext) -> None:
    user = _ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    await state.clear()
    await state.update_data(user_id=user.id)
    await state.set_state(AppointmentRequestState.country)
    await message.answer(
        "Начинаем создание заявки. Сначала выберите страну, затем город подачи, цель поездки и желаемое окно поиска.\n\n"
        f"{SENSITIVE_NOTE}",
        reply_markup=_country_keyboard(),
    )


@router.message(F.text == "👤 Связаться с менеджером")
async def contact_manager(message: Message) -> None:
    await notify_admins(message.bot, settings, build_manager_contact_notification(message.from_user.id, message.from_user.username))
    await message.answer("Менеджер получит запрос на связь и свяжется с вами вручную.", reply_markup=main_menu_keyboard())


@router.message(F.text == "🎟 Ввести промокод")
async def promo_info(message: Message) -> None:
    await message.answer("Промокод применяется во время создания заявки. Если у вас уже есть код, начните новую заявку через «📝 Создать заявку на запись».")


@router.message(F.text == "💳 Оплата")
async def payment_info(message: Message) -> None:
    orders = order_repository.list_user_orders(message.from_user.id)
    pending = [item for item in orders if item["payment_status"] == PaymentStatus.PENDING.value]
    if not pending:
        await message.answer("Отдельных неоплаченных заявок сейчас нет. Оплата или подтверждение наличными доступны в сценарии создания заявки.")
        return
    await message.answer("\n\n".join(f"{item['public_number']} — {item['payment_status']} / {item['order_status']}" for item in pending))


@router.message(AppointmentRequestState.country)
async def order_country(message: Message, state: FSMContext) -> None:
    selected = message.text.strip()
    user = _ensure_registered(message)
    if user is None:
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    if selected in SPECIAL_COUNTRIES:
        await _start_consultation_order(message, user, selected)
        await state.clear()
        return
    country = find_country_by_name(_countries(), selected)
    if country is None:
        await message.answer("Выберите страну из списка.", reply_markup=_country_keyboard())
        return
    consulates = find_consulates_by_country(_consulates(), country.code)
    if not consulates:
        await _start_consultation_order(message, user, selected)
        await state.clear()
        return
    await state.update_data(country_code=country.code, country_name_ru=country.name_ru)
    await state.set_state(AppointmentRequestState.city)
    rows = [[f"{item.city} — {item.provider}"] for item in consulates]
    await message.answer("Выберите город подачи и визовый центр.", reply_markup=simple_keyboard(*rows))


@router.message(AppointmentRequestState.city)
async def order_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    consulates = find_consulates_by_country(_consulates(), data["country_code"])
    selected = next((item for item in consulates if f"{item.city} — {item.provider}" == message.text.strip()), None)
    if selected is None:
        rows = [[f"{item.city} — {item.provider}"] for item in consulates]
        await message.answer("Выберите город подачи из списка.", reply_markup=simple_keyboard(*rows))
        return
    await state.update_data(submission_city=selected.city, provider=selected.provider)
    await state.set_state(AppointmentRequestState.purpose)
    if selected.verification_status == "needs_verification":
        await message.answer("Доступность этого города менеджер уточнит перед началом работы.")
    await message.answer("Выберите цель поездки.", reply_markup=_purpose_keyboard())


@router.message(AppointmentRequestState.purpose)
async def order_purpose(message: Message, state: FSMContext) -> None:
    if message.text.strip() not in PURPOSE_OPTIONS:
        await message.answer("Выберите цель поездки кнопкой из списка.", reply_markup=_purpose_keyboard())
        return
    await state.update_data(visa_purpose=message.text.strip())
    await state.set_state(AppointmentRequestState.time_window)
    tier_lines = [f"{prefix} {tier.label_ru}\n{tier.description_ru}\n{tier.price_rub} ₽" for prefix, tier in zip(["⚡", "🔥", "📅", "🗓", "🌿"], _price_tiers(), strict=False)]
    await message.answer("Выберите желаемое окно поиска:\n\n" + "\n\n".join(tier_lines), reply_markup=_price_keyboard())


@router.message(AppointmentRequestState.time_window)
async def order_time_window(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    label = raw.split(" ", 1)[1] if " " in raw else raw
    tier = next((item for item in _price_tiers() if item.label_ru == label), None)
    if tier is None:
        await message.answer("Выберите окно поиска из списка.", reply_markup=_price_keyboard())
        return
    await state.update_data(
        time_window_code=tier.code,
        time_window_label=tier.label_ru,
        base_price_rub=tier.price_rub,
        additional_applicant_fee_rub=tier.additional_applicant_price_rub,
    )
    await state.set_state(AppointmentRequestState.applicants_count)
    await message.answer("Сколько заявителей будет в заявке?", reply_markup=_applicant_count_keyboard())


@router.message(AppointmentRequestState.applicants_count)
async def order_applicants_count(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    if raw == "Ввести вручную":
        await state.set_state(AppointmentRequestState.applicants_manual_count)
        await message.answer("Введите количество заявителей числом.")
        return
    mapping = {
        "1 заявитель": 1,
        "2 заявителя": 2,
        "3 заявителя": 3,
        "4 заявителя": 4,
        "5+": 5,
    }
    if raw not in mapping:
        await message.answer("Выберите количество заявителей кнопкой.", reply_markup=_applicant_count_keyboard())
        return
    applicants_count = mapping[raw]
    calc = calculate_total(
        base_price_rub=(await state.get_data())["base_price_rub"],
        applicants_count=applicants_count,
        additional_applicant_fee_rub=(await state.get_data())["additional_applicant_fee_rub"],
    )
    await state.update_data(
        applicants_count=applicants_count,
        base_price_rub=calc.base_price_rub,
        additional_applicants_price_rub=calc.additional_applicants_price_rub,
        discount_rub=calc.discount_rub,
        total_price_rub=calc.total_price_rub,
        requires_manager_review=calc.requires_manager_review,
        applicants=[],
        current_applicant_index=0,
    )
    await _prompt_next_applicant(message, state)


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
    calc = calculate_total(
        base_price_rub=(await state.get_data())["base_price_rub"],
        applicants_count=applicants_count,
        additional_applicant_fee_rub=(await state.get_data())["additional_applicant_fee_rub"],
    )
    await state.update_data(
        applicants_count=applicants_count,
        base_price_rub=calc.base_price_rub,
        additional_applicants_price_rub=calc.additional_applicants_price_rub,
        discount_rub=calc.discount_rub,
        total_price_rub=calc.total_price_rub,
        requires_manager_review=calc.requires_manager_review,
        applicants=[],
        current_applicant_index=0,
    )
    await _prompt_next_applicant(message, state)


@router.message(AppointmentRequestState.applicant_last_name)
async def applicant_last_name(message: Message, state: FSMContext) -> None:
    await state.update_data(current_applicant={"last_name": message.text.strip()})
    await state.set_state(AppointmentRequestState.applicant_first_name)
    await message.answer("Укажите имя заявителя.")


@router.message(AppointmentRequestState.applicant_first_name)
async def applicant_first_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["first_name"] = message.text.strip()
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_patronymic)
    await message.answer("Укажите отчество или нажмите «Пропустить».", reply_markup=_skip_keyboard())


@router.message(AppointmentRequestState.applicant_patronymic)
async def applicant_patronymic(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["patronymic"] = None if message.text == "Пропустить" else message.text.strip()
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_birth_date)
    await message.answer("Укажите дату рождения заявителя.")


@router.message(AppointmentRequestState.applicant_birth_date)
async def applicant_birth_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["birth_date"] = message.text.strip()
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_citizenship)
    await message.answer("Укажите гражданство заявителя.", reply_markup=simple_keyboard(["Россия"]))


@router.message(AppointmentRequestState.applicant_citizenship)
async def applicant_citizenship(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["citizenship"] = message.text.strip() or "Россия"
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_location)
    await message.answer("Укажите текущую локацию заявителя.")


@router.message(AppointmentRequestState.applicant_location)
async def applicant_location(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["current_location"] = message.text.strip()
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_relationship)
    await message.answer("Укажите отношение к основному заявителю или нажмите «Пропустить».", reply_markup=_skip_keyboard())


@router.message(AppointmentRequestState.applicant_relationship)
async def applicant_relationship(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["relationship"] = None if message.text == "Пропустить" else message.text.strip()
    await state.update_data(current_applicant=applicant)
    if settings.enable_sensitive_fields:
        await state.set_state(AppointmentRequestState.applicant_passport_number)
        await message.answer("Укажите номер паспорта или нажмите «Пропустить».", reply_markup=_skip_keyboard())
        return
    applicants = data["applicants"]
    applicants.append(applicant)
    await state.update_data(applicants=applicants, current_applicant_index=data["current_applicant_index"] + 1, current_applicant={})
    await _prompt_next_applicant(message, state)


@router.message(AppointmentRequestState.applicant_passport_number)
async def applicant_passport_number(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["passport_number_encrypted"] = None if message.text == "Пропустить" else message.text.strip()
    await state.update_data(current_applicant=applicant)
    await state.set_state(AppointmentRequestState.applicant_passport_expiry)
    await message.answer("Укажите дату окончания паспорта или нажмите «Пропустить».", reply_markup=_skip_keyboard())


@router.message(AppointmentRequestState.applicant_passport_expiry)
async def applicant_passport_expiry(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["passport_expiry_date"] = None if message.text == "Пропустить" else message.text.strip()
    applicants = data["applicants"]
    applicants.append(applicant)
    await state.update_data(applicants=applicants, current_applicant_index=data["current_applicant_index"] + 1, current_applicant={})
    await _prompt_next_applicant(message, state)


@router.message(AppointmentRequestState.promo_question)
async def promo_question(message: Message, state: FSMContext) -> None:
    if message.text == "Да, ввести промокод":
        await state.set_state(AppointmentRequestState.promo_entry)
        await message.answer("Введите промокод текстом.")
        return
    if message.text != "Нет, продолжить к оплате":
        await message.answer("Выберите один из вариантов.", reply_markup=_promo_question_keyboard())
        return
    data = await state.get_data()
    await state.update_data(payment_status_label="требуется оплата")
    await state.set_state(AppointmentRequestState.summary)
    await message.answer(_render_summary(data), reply_markup=_summary_keyboard())


@router.message(AppointmentRequestState.promo_entry)
async def promo_entry(message: Message, state: FSMContext) -> None:
    code = normalize_code(message.text)
    promo = promo_repository.get_by_code(code)
    data = await state.get_data()
    if promo is None:
        await message.answer("Промокод не найден. Попробуйте еще раз или выберите оплату.", reply_markup=_promo_question_keyboard())
        await state.set_state(AppointmentRequestState.promo_question)
        return
    result = validate_promo(promo, data["base_price_rub"] + data["additional_applicants_price_rub"], data["country_code"], data["time_window_code"])
    if not result.valid:
        await message.answer(result.error or "Промокод недействителен.")
        return
    calc = calculate_total(
        base_price_rub=data["base_price_rub"],
        applicants_count=data["applicants_count"],
        additional_applicant_fee_rub=data["additional_applicant_fee_rub"],
        discount_rub=result.discount_rub,
    )
    payment_status_label = "оплачено промокодом" if result.payment_status in {PaymentStatus.PAID.value, PaymentStatus.PAID_OFFLINE.value} else "требуется оплата"
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
    await message.answer(_render_summary(data), reply_markup=_summary_keyboard())


@router.message(AppointmentRequestState.summary)
async def summary_step(message: Message, state: FSMContext) -> None:
    if message.text == "🎟 Ввести другой промокод":
        await state.set_state(AppointmentRequestState.promo_entry)
        await message.answer("Введите новый промокод.")
        return
    if message.text == "✏️ Изменить данные":
        await state.clear()
        await state.set_state(AppointmentRequestState.country)
        await message.answer("Хорошо, начнем заново с выбора страны.", reply_markup=_country_keyboard())
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание заявки отменено.", reply_markup=main_menu_keyboard())
        return
    if message.text != "✅ Подтвердить заявку":
        data = await state.get_data()
        await message.answer(_render_summary(data), reply_markup=_summary_keyboard())
        return
    data = await state.get_data()
    promo_payment_status = data.get("promo_payment_status")
    if data["total_price_rub"] == 0 and promo_payment_status == PaymentStatus.PAID.value:
        order_status = OrderStatus.REQUIRES_MANAGER_REVIEW.value if data["requires_manager_review"] else OrderStatus.PAID_WAITING_BOOKING.value
        await _finalize_order(message, state, PaymentStatus.PAID.value, order_status, payment_provider_name="promo", provider_payment_id=data.get("promo_code"), paid_at=datetime.now(UTC).isoformat())
        return
    if data["total_price_rub"] == 0 and promo_payment_status == PaymentStatus.PAID_OFFLINE.value:
        order_status = OrderStatus.REQUIRES_MANAGER_REVIEW.value if data["requires_manager_review"] else OrderStatus.PAID_WAITING_BOOKING.value
        await _finalize_order(message, state, PaymentStatus.PAID_OFFLINE.value, order_status, payment_provider_name="promo", provider_payment_id=data.get("promo_code"), paid_at=datetime.now(UTC).isoformat())
        return
    await state.set_state(AppointmentRequestState.payment)
    await message.answer("Выберите способ оплаты или подтверждения.", reply_markup=_payment_keyboard())


@router.message(AppointmentRequestState.payment)
async def payment_step(message: Message, state: FSMContext) -> None:
    if message.text == "🎟 Ввести промокод":
        await state.set_state(AppointmentRequestState.promo_entry)
        await message.answer("Введите промокод.")
        return
    if message.text == "💬 Я оплатил менеджеру наличными":
        order_status = OrderStatus.AWAITING_MANAGER_CASH_CONFIRMATION.value
        if (await state.get_data())["requires_manager_review"]:
            order_status = OrderStatus.REQUIRES_MANAGER_REVIEW.value
        await _finalize_order(
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
            f"{response.message}\nНажмите «✅ Подтвердить mock-оплату», чтобы завершить заявку в режиме разработки.",
            reply_markup=_payment_confirmation_keyboard(),
        )
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание заявки отменено.", reply_markup=main_menu_keyboard())
        return
    await message.answer("Выберите действие из меню оплаты.", reply_markup=_payment_keyboard())


@router.message(AppointmentRequestState.payment_confirmation)
async def payment_confirmation(message: Message, state: FSMContext) -> None:
    if message.text != "✅ Подтвердить mock-оплату":
        await message.answer("Для завершения нажмите «✅ Подтвердить mock-оплату» или отмените сценарий.", reply_markup=_payment_confirmation_keyboard())
        return
    data = await state.get_data()
    check = await payment_provider.check_payment(data["provider_payment_id"])
    order_status = OrderStatus.REQUIRES_MANAGER_REVIEW.value if data["requires_manager_review"] else OrderStatus.PAID_WAITING_BOOKING.value
    await _finalize_order(
        message,
        state,
        PaymentStatus.PAID.value,
        order_status,
        payment_provider_name="mock",
        provider_payment_id=check.payment_id,
        paid_at=check.paid_at,
    )

