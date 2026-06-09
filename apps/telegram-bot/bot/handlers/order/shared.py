from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import get_settings
from bot.keyboards.main import main_menu_keyboard, simple_keyboard
from bot.models import OrderStatus, PaymentStatus, User
from bot.repositories.access_keys import AccessKeyRepository
from bot.repositories.orders import OrderRepository
from bot.repositories.promos import PromoRepository
from bot.repositories.support_requests import SupportRequestRepository
from bot.repositories.users import UserRepository
from bot.services.access_keys import validate_access_key
from bot.services.config_loader import (
    find_consulates_by_country,
    find_country_by_name,
    load_consulates,
    load_countries,
    load_price_tiers,
)
from bot.services.trust_display import order_status_label, payment_status_label
from bot.services.notifications import (
    build_manager_contact_notification,
    build_new_order_notification,
    notify_admins,
)
from bot.services.order_factory import OrderInput, create_applicant, create_order, create_payment
from bot.services.payment_provider import MockPaymentProvider
from bot.services.pricing import calculate_total, render_price_summary
from bot.services.sensitive_fields import sensitive_fields_enabled, sensitive_fields_warning
from bot.states.order import AppointmentRequestState
from bot.texts.common import SENSITIVE_NOTE

settings = get_settings()
user_repository = UserRepository(settings.database_url)
order_repository = OrderRepository(settings.database_url)
promo_repository = PromoRepository(settings.database_url)
access_key_repository = AccessKeyRepository(settings.database_url)
support_request_repository = SupportRequestRepository(settings.database_url)
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


def countries():
    return load_countries(settings.repo_root)


def consulates():
    return load_consulates(settings.repo_root)


def price_tiers():
    return load_price_tiers(settings.repo_root)


def country_keyboard():
    names = [country.name_ru for country in countries()]
    return simple_keyboard(names[:3], names[3:], ["Другая страна", "Не знаю, нужна консультация"])


def purpose_keyboard():
    return simple_keyboard(PURPOSE_OPTIONS[:2], PURPOSE_OPTIONS[2:4], PURPOSE_OPTIONS[4:])


def price_keyboard():
    tiers = price_tiers()
    return simple_keyboard(
        [f"⚡ {tiers[0].label_ru}"],
        [f"🔥 {tiers[1].label_ru}"],
        [f"📅 {tiers[2].label_ru}"],
        [f"🗓 {tiers[3].label_ru}"],
        [f"🌿 {tiers[4].label_ru}"],
    )


def applicant_count_keyboard():
    return simple_keyboard(["1 заявитель", "2 заявителя"], ["3 заявителя", "4 заявителя"], ["5+", "Ввести вручную"])


def summary_keyboard():
    return simple_keyboard(["✅ Подтвердить заявку"], ["✏️ Изменить данные"], ["❌ Отмена"])


def skip_keyboard():
    return simple_keyboard(["Пропустить"])


def ensure_registered(message: Message) -> User | None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user is None or not user_repository.is_registered(user):
        return None
    return user


async def start_consultation_order(message: Message, user: User, selected_country: str) -> None:
    access_key = access_key_repository.get_active_for_telegram_user(message.from_user.id)
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
            access_key_code=access_key.code if access_key else None,
            access_key_id=access_key.id if access_key else None,
            payment_status=PaymentStatus.PAID_OFFLINE.value,
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
        reply_markup=main_menu_keyboard(settings.client_miniapp_url),
    )


def render_summary(data: dict[str, Any]) -> str:
    access_key_code = data.get("access_key_code") or "не активирован"
    payment_text = "вне бота / подтверждена агентством"
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
        f"Доступ: подтвержден ключом менеджера ({access_key_code})\n"
        f"Оплата: {payment_text}"
    )


def build_order_payload(
    state_data: dict[str, Any], payment_status: str, order_status: str, manager_note: str | None = None
) -> tuple[Any, Any]:
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
            access_key_code=state_data.get("access_key_code"),
            access_key_id=state_data.get("access_key_id"),
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


async def finalize_order(
    message: Message,
    state: FSMContext,
    payment_status: str,
    order_status: str,
    payment_provider_name: str = "mock",
    provider_payment_id: str | None = None,
    paid_at: str | None = None,
    manager_note: str | None = None,
) -> None:
    data = await state.get_data()
    order, applicants = build_order_payload(data, payment_status, order_status, manager_note)
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
    if data.get("access_key_id"):
        access_key_repository.consume_for_order(data["access_key_id"], order.id)
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
        f"Статус: {payment_status_label(order.payment_status)}, {order_status_label(order.order_status)}.\n"
        "Мы не гарантируем наличие свободных слотов. Менеджер начнет обработку и сообщит о следующих шагах.",
        reply_markup=main_menu_keyboard(settings.client_miniapp_url),
    )


async def prompt_next_applicant(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    current_index = data.get("current_applicant_index", 0)
    applicants_count = data["applicants_count"]
    if current_index >= applicants_count:
        await state.update_data(payment_status_label="вне бота / подтверждена агентством")
        await state.set_state(AppointmentRequestState.summary)
        summary_data = await state.get_data()
        await message.answer(render_summary(summary_data), reply_markup=summary_keyboard())
        return
    await state.set_state(AppointmentRequestState.applicant_last_name)
    await message.answer(f"Заявитель {current_index + 1} из {applicants_count}. Укажите фамилию.")


def get_user_access_key(telegram_id: int):
    return access_key_repository.get_active_for_telegram_user(telegram_id)


def user_has_valid_access_key(telegram_id: int) -> bool:
    access_key = access_key_repository.get_active_for_telegram_user(telegram_id)
    if access_key is None:
        return False
    result = validate_access_key(access_key, telegram_id)
    return result.valid


def order_start_text() -> str:
    return (
        "Начинаем создание заявки. Сначала выберите страну, затем город подачи, цель поездки и желаемое окно поиска.\n\n"
        f"{SENSITIVE_NOTE}\n\n"
        f"{sensitive_fields_warning(settings)}"
    )


async def store_applicant_and_continue(message: Message, state: FSMContext, applicant: dict[str, Any]) -> None:
    data = await state.get_data()
    applicants = data["applicants"]
    applicants.append(applicant)
    await state.update_data(
        applicants=applicants,
        current_applicant_index=data["current_applicant_index"] + 1,
        current_applicant={},
    )
    await prompt_next_applicant(message, state)


__all__ = [
    "AppointmentRequestState",
    "OrderStatus",
    "PaymentStatus",
    "SPECIAL_COUNTRIES",
    "PURPOSE_OPTIONS",
    "applicant_count_keyboard",
    "build_manager_contact_notification",
    "consulates",
    "countries",
    "country_keyboard",
    "ensure_registered",
    "finalize_order",
    "find_consulates_by_country",
    "find_country_by_name",
    "get_user_access_key",
    "main_menu_keyboard",
    "notify_admins",
    "order_repository",
    "order_start_text",
    "payment_provider",
    "price_keyboard",
    "price_tiers",
    "promo_repository",
    "prompt_next_applicant",
    "purpose_keyboard",
    "simple_keyboard",
    "render_summary",
    "settings",
    "sensitive_fields_enabled",
    "skip_keyboard",
    "start_consultation_order",
    "store_applicant_and_continue",
    "summary_keyboard",
    "support_request_repository",
    "user_has_valid_access_key",
    "user_repository",
    "validate_access_key",
]
