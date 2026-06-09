from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.keyboards.inline import (
    admin_message_templates_keyboard,
    admin_order_actions_keyboard,
    admin_status_keyboard,
    document_actions_keyboard,
    document_agency_template_keyboard,
    document_client_template_keyboard,
    document_items_keyboard,
    document_status_keyboard,
    slot_options_keyboard,
    support_request_actions_keyboard,
)
from bot.keyboards.main import admin_menu_keyboard, simple_keyboard
from bot.models import (
    AccessKeyStatus,
    AgencyDocumentStatus,
    BookingOrder,
    DocumentCategory,
    OrderStatus,
    PromoCode,
    PromoCodeType,
    SupportRequestStatus,
)
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.orders import OrderRepository
from bot.repositories.promos import PromoRepository
from bot.repositories.support_requests import SupportRequestRepository
from bot.services.access import deny_admin_callback, deny_admin_message, is_admin
from bot.services.access_keys import generate_access_key
from bot.services.booking_provider import MockBookingProvider
from bot.services.case_status import format_case_public_number
from bot.services.document_status import document_status_label
from bot.services.notifications import (
    build_agency_document_ready_message,
    build_appointment_confirmed_message,
    build_documents_requested_message,
    build_slot_options_message,
    build_slot_options_sent_to_manager,
    build_slot_selected_notification,
    build_user_slot_selected_message,
    notify_admins,
)
from bot.services.slot_offers import parse_slot_offer_lines
from bot.states.order import AdminState

router = Router()
settings = get_settings()
order_repository = OrderRepository(settings.database_url)
promo_repository = PromoRepository(settings.database_url)
access_key_repository = AccessKeyRepository(settings.database_url)
support_request_repository = SupportRequestRepository(settings.database_url)
miniapp_repository = MiniAppRepository(settings.database_url, repo_root=settings.repo_root)
document_repository = DocumentRepository(settings.database_url)
booking_provider = MockBookingProvider()


def _require_admin(message: Message) -> bool:
    return is_admin(message.from_user.id, settings)


async def _deny(message: Message) -> None:
    await deny_admin_message(message)


async def _deny_callback(callback: CallbackQuery) -> None:
    await deny_admin_callback(callback)


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _promo_value_error(promo_type: str, value: int) -> str | None:
    if promo_type == PromoCodeType.PERCENT_DISCOUNT and not 1 <= value <= 100:
        return "Для percent_discount введите число от 1 до 100."
    if promo_type == PromoCodeType.FIXED_DISCOUNT and value < 1:
        return "Для fixed_discount сумма скидки должна быть не меньше 1."
    if promo_type in {PromoCodeType.FULL_DISCOUNT, PromoCodeType.CASH_PAID} and value < 0:
        return "Для full_discount и cash_paid можно указать 0 или больше."
    if promo_type == PromoCodeType.MANAGER_OVERRIDE and value < 0:
        return "Значение manager_override должно быть 0 или больше."
    return None


def _render_access_key(access_key) -> str:
    country_text = ", ".join(access_key.country_codes) if access_key.country_codes else "без ограничения"
    applicants_text = f"до {access_key.max_applicants}" if access_key.max_applicants else "без лимита / manual review"
    expires_text = access_key.expires_at[:10] if access_key.expires_at else "без ограничения"
    service_map = {
        "appointment_request": "Запись в консульство / визовый центр",
        "consultation": "Консультация",
        "full_visa_support": "Полное визовое сопровождение",
    }
    service_text = service_map.get(access_key.service_type or "", access_key.service_type or "-")
    return (
        "Ключ доступа создан:\n"
        f"Код: {access_key.code}\n"
        f"Услуга: {service_text}\n"
        f"Страна: {country_text}\n"
        f"Заявителей: {applicants_text}\n"
        f"Срок действия: {expires_text}\n"
        "Отправьте клиенту:\n"
        f"Здравствуйте! Для продолжения работы откройте нашего Telegram-бота и введите ключ доступа: {access_key.code}"
    )


def _template_text(template_code: str, public_number: str | None = None) -> str:
    templates = {
        "reviewing": "Менеджер проверяет вашу заявку.",
        "clarify": "По вашей заявке нужны уточнения. Пожалуйста, свяжитесь с менеджером.",
        "waiting_slot": "По вашей заявке ожидаем доступный слот.",
        "slot_found": "По вашей заявке найден слот. Менеджер свяжется с вами для следующего шага.",
        "booked": "Запись подтверждена. Менеджер направит детали отдельно.",
        "contact_manager": "Пожалуйста, свяжитесь с менеджером для уточнения деталей.",
    }
    text = templates.get(template_code, "Менеджер обновил статус.")
    if public_number:
        return f"По заявке {public_number}: {text}"
    return text


def _render_support_request(request) -> str:
    return (
        f"Запрос: {request.id}\n"
        f"Клиент: @{request.username or '-'} / {request.telegram_id}\n"
        f"Статус: {request.status}\n"
        f"Создан: {request.created_at[:16]}\n"
        f"Сообщение: {request.message or '-'}"
    )


def _render_case_summary(visa_case) -> str:
    return (
        f"Кейс: {visa_case.id}\n"
        f"Клиент telegram_id: {visa_case.telegram_id}\n"
        f"Страна: {visa_case.desired_country_name_ru or 'не выбрана'}\n"
        f"Город: {visa_case.preferred_submission_city or 'не выбран'}\n"
        f"Провайдер: {visa_case.submission_provider or 'не выбран'}\n"
        f"Статус: {visa_case.status}"
    )


def _render_order_details(details: dict) -> str:
    first_applicant = details["applicants"][0] if details["applicants"] else {}
    payment = details.get("payment") or {}
    promo = details.get("promo_code") or "нет"
    return (
        f"Заявка: {details['public_number']}\n"
        f"Клиент: @{details['username'] or '-'} / {details['telegram_id']}\n"
        f"Первый заявитель: {first_applicant.get('last_name', '')} {first_applicant.get('first_name', '')}\n"
        f"Страна/город: {details['country_name_ru']} / {details['submission_city']}\n"
        f"Окно: {details['time_window_code']}\n"
        f"Цена: {details['total_price_rub']} ₽\n"
        f"Оплата: {details['payment_status']}\n"
        f"Промокод: {promo}\n"
        f"Статус: {details['order_status']}\n"
        f"Создана: {details['created_at'][:16]}\n"
        f"Заметка: {details.get('manager_note') or '-'}\n"
        f"Платеж: {payment.get('status', '-')}"
    )


def _build_booking_order(details: dict) -> BookingOrder:
    return BookingOrder(
        id=details["id"],
        public_number=details["public_number"],
        user_id=details["user_id"],
        country_code=details["country_code"],
        country_name_ru=details["country_name_ru"],
        submission_city=details["submission_city"],
        provider=details["provider"],
        visa_purpose=details["visa_purpose"],
        time_window_code=details["time_window_code"],
        applicants_count=details["applicants_count"],
        base_price_rub=details["base_price_rub"],
        additional_applicants_price_rub=details["additional_applicants_price_rub"],
        discount_rub=details["discount_rub"],
        total_price_rub=details["total_price_rub"],
        promo_code=details["promo_code"],
        payment_status=details["payment_status"],
        order_status=details["order_status"],
        requires_manager_review=bool(details["requires_manager_review"]),
        manager_note=details["manager_note"],
        user_comment=details["user_comment"],
        created_at=details["created_at"],
        updated_at=details["updated_at"],
    )


@router.message(Command("admin"))
async def command_admin(message: Message) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await message.answer("Менеджерское меню", reply_markup=admin_menu_keyboard())


@router.message(F.text == "📥 Новые заявки")
async def list_new_orders(message: Message) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    orders = order_repository.list_admin_queue()
    cases = miniapp_repository.list_submitted_cases()
    if not orders and not cases:
        await message.answer("В очереди нет новых заявок.")
        return
    blocks: list[str] = []
    if orders:
        blocks.extend(
            f"{item['public_number']}\n{item['country_name_ru']} / {item['submission_city']}\n{item['payment_status']} / {item['order_status']}\n{item['created_at'][:16]}"
            for item in orders
        )
    if cases:
        blocks.extend(
            f"MINIAPP CASE {item.id}\n{item.desired_country_name_ru or 'Консультация'} / {item.preferred_submission_city or 'уточнить'}\n{item.status}\n{(item.submitted_at or item.updated_at)[:16]}"
            for item in cases
        )
    await message.answer("\n\n".join(blocks))


@router.message(F.text == "🔎 Найти заявку")
async def find_order_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.search_order)
    await message.answer("Введите номер заявки, например VISA-2026-000123.")


@router.message(AdminState.search_order)
async def find_order(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    public_number = message.text.strip().upper()
    details = order_repository.get_order_details(public_number)
    if details is None:
        await message.answer("Заявка не найдена.")
        return
    await state.clear()
    await message.answer(_render_order_details(details), reply_markup=admin_order_actions_keyboard(public_number))


@router.message(F.text == "✅ Подтвердить оплату наличными")
async def confirm_cash_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.confirm_cash_order)
    await message.answer("Введите номер заявки для подтверждения наличной оплаты.")


@router.message(AdminState.confirm_cash_order)
async def confirm_cash(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    public_number = message.text.strip().upper()
    updated = order_repository.mark_cash_confirmed(public_number, message.from_user.id)
    if updated is None:
        await message.answer("Заявка не найдена.")
        return
    await state.clear()
    await message.answer("Оплата наличными подтверждена.")
    await message.bot.send_message(updated["telegram_id"], f"Менеджер подтвердил оплату по заявке {public_number}. Статус обновлен.")


@router.message(F.text == "🔄 Изменить статус заявки")
async def change_status_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.change_status_order)
    await message.answer("Введите номер заявки для смены статуса.")


@router.message(AdminState.change_status_order)
async def change_status_lookup(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    public_number = message.text.strip().upper()
    details = order_repository.get_order_details(public_number)
    if details is None:
        await message.answer("Заявка не найдена.")
        return
    await state.clear()
    await message.answer("Выберите новый статус.", reply_markup=admin_status_keyboard(public_number))


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    stats = order_repository.stats()
    await message.answer(
        f"Всего пользователей: {stats['users_total']}\n"
        f"Всего заявок: {stats['orders_total']}\n"
        f"Оплаченных: {stats['paid_total']}\n"
        f"На ручной проверке: {stats['review_total']}"
    )


@router.message(F.text == "📅 Отправить даты")
async def send_slot_dates_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.slot_offer_case_id)
    await message.answer("Введите ID кейса, для которого хотите отправить варианты дат.")


@router.message(AdminState.slot_offer_case_id)
async def send_slot_dates_case_id(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    case_id = message.text.strip()
    visa_case = miniapp_repository.get_case_by_any_id(case_id)
    if visa_case is None:
        await message.answer("Кейс не найден.")
        return
    await state.update_data(slot_offer_case_id=case_id)
    await state.set_state(AdminState.slot_offer_options)
    await message.answer(
        _render_case_summary(visa_case)
        + "\n\nВведите варианты дат построчно.\nПример:\n2026-07-15 10:30\n2026-07-16 14:00 | Москва | VMS Italy | Комментарий"
    )


@router.message(AdminState.slot_offer_options)
async def send_slot_dates_options(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    try:
        parsed = parse_slot_offer_lines(message.text)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    preview = "\n".join(
        f"{item.option_date} {item.option_time} | {item.city or '-'} | {item.provider or '-'} | {item.comment or '-'}"
        for item in parsed
    )
    await state.update_data(slot_offer_raw=message.text, slot_offer_preview=preview)
    await state.set_state(AdminState.slot_offer_confirm)
    await message.answer(
        "Проверьте варианты:\n"
        f"{preview}\n\n"
        "Если все верно, отправьте «Отправить». Для отмены отправьте «Отмена»."
    )


@router.message(AdminState.slot_offer_confirm)
async def send_slot_dates_confirm(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    text = message.text.strip()
    if text.lower() == "отмена":
        await state.clear()
        await message.answer("Отправка вариантов дат отменена.", reply_markup=admin_menu_keyboard())
        return
    if text.lower() != "отправить":
        await message.answer("Отправьте «Отправить» для подтверждения или «Отмена».")
        return
    data = await state.get_data()
    parsed = parse_slot_offer_lines(data["slot_offer_raw"])
    try:
        offer, options, visa_case = miniapp_repository.create_slot_offer(
            data["slot_offer_case_id"],
            message.from_user.id,
            parsed,
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.clear()
    labels = [(item.id, f"{item.option_date[8:10]}.{item.option_date[5:7]}.{item.option_date[:4]} {item.option_time}") for item in options]
    await message.bot.send_message(
        visa_case.telegram_id,
        build_slot_options_message(),
        reply_markup=slot_options_keyboard(labels, settings.client_miniapp_url),
    )
    await message.answer(build_slot_options_sent_to_manager(visa_case.id, len(options)), reply_markup=admin_menu_keyboard())


@router.message(F.text == "✅ Подтвердить запись")
async def confirm_appointment_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.confirm_appointment_case_id)
    await message.answer("Введите ID кейса для подтверждения записи.")


@router.message(AdminState.confirm_appointment_case_id)
async def confirm_appointment_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    case_id = message.text.strip()
    try:
        visa_case = miniapp_repository.confirm_appointment(case_id, message.from_user.id)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.clear()
    await message.answer("Запись подтверждена.", reply_markup=admin_menu_keyboard())
    await message.bot.send_message(
        visa_case.telegram_id,
        build_appointment_confirmed_message(
            visa_case.selected_appointment_date,
            visa_case.selected_appointment_time,
            visa_case.selected_appointment_city,
            visa_case.selected_appointment_provider,
        ),
    )


def _render_case_documents(case_id: str) -> str:
    items = document_repository.list_by_case(case_id)
    if not items:
        return f"По кейсу {case_id} документов пока нет."
    lines = [f"Документы по кейсу {case_id}:"]
    for item in items:
        lines.append(f"- {item.title}: {document_status_label(item)} ({item.source_type})")
    return "\n".join(lines)


@router.message(F.text == "📎 Документы по заявке")
async def documents_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.document_case_id)
    await message.answer("Введите ID кейса для работы с документами.")


@router.message(AdminState.document_case_id)
async def documents_case_id_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    case_id = message.text.strip()
    visa_case = miniapp_repository.get_case_by_any_id(case_id)
    if visa_case is None:
        await message.answer("Кейс не найден. Проверьте ID и попробуйте снова.")
        return
    await state.update_data(case_id=case_id, telegram_id=visa_case.telegram_id)
    await state.set_state(AdminState.document_action)
    await message.answer(
        f"Кейс найден: {format_case_public_number(visa_case)}.\nВыберите действие.",
        reply_markup=document_actions_keyboard(),
    )


@router.callback_query(F.data.startswith("doc:action:"))
async def document_action_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    action = callback.data.split(":", 2)[2]
    data = await state.get_data()
    case_id = data.get("case_id")
    if not case_id:
        await callback.answer("Сначала укажите ID кейса.", show_alert=True)
        return

    if action == "list":
        await callback.answer()
        await callback.message.answer(_render_case_documents(case_id))
        return

    if action == "request":
        await callback.answer()
        await callback.message.answer(
            "Выберите документ для запроса у клиента.",
            reply_markup=document_client_template_keyboard(),
        )
        return

    if action == "agency":
        await callback.answer()
        await callback.message.answer(
            "Выберите документ, который готовит агентство.",
            reply_markup=document_agency_template_keyboard(),
        )
        return

    if action == "status":
        items = document_repository.list_by_case(case_id)
        if not items:
            await callback.answer("Документов нет.", show_alert=True)
            return
        await state.update_data(document_action="status")
        await callback.answer()
        await callback.message.answer(
            "Выберите документ для изменения статуса.",
            reply_markup=document_items_keyboard(
                [(item.id, f"{item.title} ({document_status_label(item)})") for item in items],
                "pickstatus",
            ),
        )
        return

    if action == "comment":
        items = document_repository.list_by_case(case_id)
        if not items:
            await callback.answer("Документов нет.", show_alert=True)
            return
        await state.update_data(document_action="comment")
        await callback.answer()
        await callback.message.answer(
            "Выберите документ для комментария.",
            reply_markup=document_items_keyboard(
                [(item.id, item.title) for item in items],
                "pickcomment",
            ),
        )


@router.callback_query(F.data.startswith("doc:req:"))
async def document_request_template_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    category = callback.data.split(":", 2)[2]
    data = await state.get_data()
    case_id = data.get("case_id")
    if not case_id:
        await callback.answer("Сначала укажите ID кейса.", show_alert=True)
        return

    if category == DocumentCategory.OTHER_CLIENT_DOCUMENT.value:
        await state.update_data(pending_category=category, pending_source="client")
        await state.set_state(AdminState.document_agency_title)
        await callback.answer()
        await callback.message.answer("Введите название документа.")
        return

    await state.update_data(pending_category=category, pending_source="client")
    await state.set_state(AdminState.document_request_comment)
    await callback.answer()
    await callback.message.answer("Добавьте комментарий для клиента или отправьте «-» без комментария.")


@router.callback_query(F.data.startswith("doc:agency:"))
async def document_agency_template_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    category = callback.data.split(":", 2)[2]
    data = await state.get_data()
    case_id = data.get("case_id")
    telegram_id = data.get("telegram_id")
    if not case_id:
        await callback.answer("Сначала укажите ID кейса.", show_alert=True)
        return

    if category == DocumentCategory.OTHER_AGENCY_DOCUMENT.value:
        await state.update_data(pending_category=category, pending_source="agency")
        await state.set_state(AdminState.document_agency_title)
        await callback.answer()
        await callback.message.answer("Введите название документа агентства.")
        return

    try:
        document_repository.create_agency_item(
            case_id,
            category,
            admin_id=callback.from_user.id,
        )
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await callback.answer("Документ добавлен.")
    await callback.message.answer(_render_case_documents(case_id), reply_markup=admin_menu_keyboard())


@router.message(AdminState.document_agency_title)
async def document_custom_title_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    data = await state.get_data()
    case_id = data.get("case_id")
    pending_source = data.get("pending_source")
    pending_category = data.get("pending_category")
    custom_title = message.text.strip()
    if not case_id or not pending_source or not pending_category:
        await message.answer("Сессия истекла. Начните снова через меню документов.")
        await state.clear()
        return

    if pending_source == "client":
        await state.update_data(custom_title=custom_title)
        await state.set_state(AdminState.document_request_comment)
        await message.answer("Добавьте комментарий для клиента или отправьте «-» без комментария.")
        return

    try:
        document_repository.create_agency_item(
            case_id,
            pending_category,
            title=custom_title,
            admin_id=message.from_user.id,
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.set_state(AdminState.document_action)
    await message.answer(_render_case_documents(case_id), reply_markup=document_actions_keyboard())


@router.message(AdminState.document_request_comment)
async def document_request_comment_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    data = await state.get_data()
    case_id = data.get("case_id")
    pending_category = data.get("pending_category")
    custom_title = data.get("custom_title")
    telegram_id = data.get("telegram_id")
    if not case_id or not pending_category:
        await message.answer("Сессия истекла. Начните снова через меню документов.")
        await state.clear()
        return

    comment = None if message.text.strip() == "-" else message.text.strip()
    try:
        if custom_title:
            document_repository.create_custom_client_request(
                case_id,
                custom_title,
                admin_id=message.from_user.id,
                comment=comment,
            )
        else:
            document_repository.create_client_request(
                case_id,
                pending_category,
                admin_id=message.from_user.id,
                comment=comment,
            )
    except ValueError as exc:
        await message.answer(str(exc))
        return

    await state.set_state(AdminState.document_action)
    await message.answer(_render_case_documents(case_id), reply_markup=document_actions_keyboard())
    if telegram_id:
        await message.bot.send_message(telegram_id, build_documents_requested_message())


@router.callback_query(F.data.startswith("doc:pickstatus:"))
async def document_pick_status_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    document_id = callback.data.split(":", 2)[2]
    item = document_repository.get_by_id(document_id)
    if item is None:
        await callback.answer("Документ не найден.", show_alert=True)
        return
    await state.update_data(document_id=document_id)
    await callback.answer()
    await callback.message.answer(
        f"Новый статус для «{item.title}»:",
        reply_markup=document_status_keyboard(item.source_type),
    )


@router.callback_query(F.data.startswith("doc:setstatus:"))
async def document_set_status_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    status = callback.data.split(":", 2)[2]
    data = await state.get_data()
    document_id = data.get("document_id")
    case_id = data.get("case_id")
    telegram_id = data.get("telegram_id")
    if not document_id:
        await callback.answer("Сначала выберите документ.", show_alert=True)
        return
    try:
        updated = document_repository.update_status(document_id, status, admin_id=callback.from_user.id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer("Статус обновлён.")
    if case_id:
        await callback.message.answer(_render_case_documents(case_id))
    if telegram_id and updated.source_type == "agency_prepared" and status == AgencyDocumentStatus.READY_FOR_CLIENT.value:
        await callback.message.bot.send_message(
            telegram_id,
            build_agency_document_ready_message(updated.title),
        )


@router.callback_query(F.data.startswith("doc:pickcomment:"))
async def document_pick_comment_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    document_id = callback.data.split(":", 2)[2]
    await state.update_data(document_id=document_id)
    await state.set_state(AdminState.document_comment_text)
    await callback.answer()
    await callback.message.answer("Введите комментарий для клиента.")


@router.message(AdminState.document_comment_text)
async def document_comment_text_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    data = await state.get_data()
    document_id = data.get("document_id")
    case_id = data.get("case_id")
    if not document_id:
        await message.answer("Сначала выберите документ.")
        return
    try:
        document_repository.add_manager_comment(document_id, message.text.strip(), message.from_user.id)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.set_state(AdminState.document_action)
    if case_id:
        await message.answer(_render_case_documents(case_id), reply_markup=document_actions_keyboard())
    else:
        await message.answer("Комментарий сохранён.", reply_markup=admin_menu_keyboard())


@router.message(F.text == "🔑 Создать ключ доступа")
async def create_access_key_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.access_key_code)
    await message.answer("Введите код ключа доступа или отправьте «AUTO» для автогенерации.")


@router.message(AdminState.access_key_code)
async def access_key_code_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    code = generate_access_key() if message.text.strip().upper() == "AUTO" else message.text.strip().upper()
    await state.update_data(code=code)
    await state.set_state(AdminState.access_key_service_type)
    await message.answer(
        "Выберите тип услуги.",
        reply_markup=simple_keyboard(
            ["appointment_request"],
            ["consultation"],
            ["full_visa_support"],
        ),
    )


@router.message(AdminState.access_key_service_type)
async def access_key_service_type_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.update_data(service_type=message.text.strip())
    await state.set_state(AdminState.access_key_country)
    await message.answer(
        "Выберите ограничение по стране.",
        reply_markup=simple_keyboard(
            ["без ограничения"],
            ["IT", "FR", "ES"],
            ["GR", "DE", "PT"],
        ),
    )


@router.message(AdminState.access_key_country)
async def access_key_country_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    country_codes = [] if message.text.strip() == "без ограничения" else [message.text.strip().upper()]
    await state.update_data(country_codes=country_codes)
    await state.set_state(AdminState.access_key_max_applicants)
    await message.answer(
        "Укажите максимум заявителей.",
        reply_markup=simple_keyboard(["1", "2", "3"], ["4", "5"], ["без лимита / manual review"]),
    )


@router.message(AdminState.access_key_max_applicants)
async def access_key_max_applicants_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    text = message.text.strip()
    max_applicants = None if text == "без лимита / manual review" else int(text)
    await state.update_data(max_applicants=max_applicants)
    await state.set_state(AdminState.access_key_expiration)
    await message.answer(
        "Укажите срок действия.",
        reply_markup=simple_keyboard(["7 дней", "14 дней"], ["30 дней"], ["без ограничения"]),
    )


@router.message(AdminState.access_key_expiration)
async def access_key_expiration_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    mapping = {"7 дней": 7, "14 дней": 14, "30 дней": 30}
    expires_at = None
    if message.text.strip() in mapping:
        expires_at = (datetime.now(UTC).replace(microsecond=0) + timedelta(days=mapping[message.text.strip()])).isoformat()
    await state.update_data(expires_at=expires_at)
    await state.set_state(AdminState.access_key_note)
    await message.answer("Введите заметку или «-».")


@router.message(AdminState.access_key_note)
async def access_key_note_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    data = await state.get_data()
    note = None if message.text.strip() == "-" else message.text.strip()
    access_key = new_access_key(
        code=data["code"],
        created_by_admin_id=message.from_user.id,
        service_type=data["service_type"],
        country_codes=data["country_codes"],
        max_applicants=data["max_applicants"],
        expires_at=data["expires_at"],
        note=note,
    )
    access_key_repository.save(access_key)
    await state.clear()
    await message.answer(_render_access_key(access_key), reply_markup=admin_menu_keyboard())


@router.message(F.text == "📨 Запросы клиентов")
async def list_support_requests(message: Message) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    requests = support_request_repository.list_open()
    if not requests:
        await message.answer("Открытых запросов клиентов нет.")
        return
    for request in requests:
        await message.answer(_render_support_request(request), reply_markup=support_request_actions_keyboard(request.id))


@router.message(F.text == "🎟 Создать промокод")
async def create_promo_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.promo_code)
    await message.answer("Введите код промокода.")


@router.message(AdminState.promo_code)
async def promo_code_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AdminState.promo_type)
    await message.answer(
        "Выберите тип промокода.",
        reply_markup=simple_keyboard(
            ["full_discount", "cash_paid"],
            ["percent_discount", "fixed_discount"],
            ["manager_override"],
        ),
    )


@router.message(AdminState.promo_type)
async def promo_type_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    promo_type = message.text.strip()
    allowed_types = {
        PromoCodeType.FULL_DISCOUNT,
        PromoCodeType.CASH_PAID,
        PromoCodeType.PERCENT_DISCOUNT,
        PromoCodeType.FIXED_DISCOUNT,
        PromoCodeType.MANAGER_OVERRIDE,
    }
    if promo_type not in allowed_types:
        await message.answer("Выберите тип промокода кнопкой из списка.")
        return
    await state.update_data(type=promo_type)
    await state.set_state(AdminState.promo_value)
    await message.answer("Введите значение промокода. Для full_discount и cash_paid можно указать 0.")


@router.message(AdminState.promo_value)
async def promo_value_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    value = _parse_int(message.text)
    if value is None:
        await message.answer("Введите значение промокода числом.")
        return
    data = await state.get_data()
    error = _promo_value_error(data["type"], value)
    if error:
        await message.answer(error)
        return
    await state.update_data(value=value)
    await state.set_state(AdminState.promo_max_uses)
    await message.answer("Введите максимальное число использований.")


@router.message(AdminState.promo_max_uses)
async def promo_max_uses_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    max_uses = _parse_int(message.text)
    if max_uses is None:
        await message.answer("Введите максимальное число использований числом.")
        return
    if max_uses < 1:
        await message.answer("Максимальное число использований должно быть не меньше 1.")
        return
    await state.update_data(max_uses=max_uses)
    await state.set_state(AdminState.promo_expires_at)
    await message.answer("Введите дату окончания в ISO-формате или «-» без ограничения.")


@router.message(AdminState.promo_expires_at)
async def promo_expires_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.update_data(expires_at=None if message.text.strip() == "-" else message.text.strip())
    await state.set_state(AdminState.promo_country_codes)
    await message.answer("Введите коды стран через запятую или «-» без ограничения.")


@router.message(AdminState.promo_country_codes)
async def promo_country_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    raw = message.text.strip()
    await state.update_data(country_codes=[] if raw == "-" else [item.strip().upper() for item in raw.split(",") if item.strip()])
    await state.set_state(AdminState.promo_time_window_codes)
    await message.answer("Введите коды окон поиска через запятую или «-» без ограничения.")


@router.message(AdminState.promo_time_window_codes)
async def promo_window_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    raw = message.text.strip()
    await state.update_data(time_window_codes=[] if raw == "-" else [item.strip() for item in raw.split(",") if item.strip()])
    await state.set_state(AdminState.promo_note)
    await message.answer("Введите заметку или «-».")


@router.message(AdminState.promo_note)
async def promo_note_step(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    data = await state.get_data()
    note = None if message.text.strip() == "-" else message.text.strip()
    promo = PromoCode(
        id=str(uuid4()),
        code=data["code"],
        type=data["type"],
        value=data["value"],
        max_uses=data["max_uses"],
        used_count=0,
        active=True,
        expires_at=data["expires_at"],
        created_by_admin_id=message.from_user.id,
        country_codes=data["country_codes"],
        time_window_codes=data["time_window_codes"],
        note=note,
        created_at=datetime.now(UTC).isoformat(),
    )
    promo_repository.save(promo)
    await state.clear()
    await message.answer(f"Промокод {promo.code} сохранен.", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data.startswith("admin:take:"))
async def admin_take_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    public_number = callback.data.split(":")[2]
    details = order_repository.get_order_details(public_number)
    if details is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    booking_response = await booking_provider.create_request(_build_booking_order(details))
    updated = order_repository.update_order_status(
        public_number,
        callback.from_user.id,
        booking_response.status,
        manager_note=booking_response.message,
    )
    await callback.answer("Заявка взята в работу.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(
            updated["telegram_id"],
            f"Заявка {public_number} взята в работу менеджером. Реальное бронирование еще не выполнялось: сейчас используется mock-этап внутренней обработки.",
        )


@router.callback_query(F.data.startswith("admin:cash:"))
async def admin_cash_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    public_number = callback.data.split(":")[2]
    updated = order_repository.mark_cash_confirmed(public_number, callback.from_user.id)
    await callback.answer("Оплата подтверждена.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(updated["telegram_id"], f"По заявке {public_number} подтверждена наличная оплата.")


@router.callback_query(F.data.startswith("admin:status:"))
async def admin_status_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    public_number = callback.data.split(":")[2]
    await callback.answer()
    await callback.message.answer("Выберите новый статус.", reply_markup=admin_status_keyboard(public_number))


@router.callback_query(F.data.startswith("admin:setstatus:"))
async def admin_set_status(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    _, _, public_number, status = callback.data.split(":", 3)
    updated = order_repository.update_order_status(public_number, callback.from_user.id, status)
    await callback.answer("Статус обновлен.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(updated["telegram_id"], f"Статус заявки {public_number} обновлен: {status}.")


@router.callback_query(F.data.startswith("admin:message:"))
async def admin_message_user(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    public_number = callback.data.split(":")[2]
    await callback.answer()
    await callback.message.answer(
        "Выберите шаблон сообщения.",
        reply_markup=admin_message_templates_keyboard("order", public_number),
    )


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    public_number = callback.data.split(":")[2]
    updated = order_repository.update_order_status(public_number, callback.from_user.id, OrderStatus.CANCELLED.value, payment_status="cancelled")
    await callback.answer("Заявка отменена.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(updated["telegram_id"], f"Заявка {public_number} отменена менеджером.")


@router.callback_query(F.data.startswith("support:status:"))
async def support_status_update(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    _, _, request_id, status = callback.data.split(":", 3)
    updated = support_request_repository.update_status(request_id, status)
    if updated is None:
        await callback.answer("Запрос не найден.", show_alert=True)
        return
    await callback.answer("Статус запроса обновлен.")
    await callback.message.answer(_render_support_request(updated), reply_markup=support_request_actions_keyboard(request_id))


@router.callback_query(F.data.startswith("support:message:"))
async def support_message(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    request_id = callback.data.split(":")[2]
    await callback.answer()
    await callback.message.answer(
        "Выберите шаблон сообщения.",
        reply_markup=admin_message_templates_keyboard("support", request_id),
    )


@router.callback_query(F.data.startswith("admin:template:"))
async def admin_template_send(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await _deny_callback(callback)
        return
    _, _, target_kind, target_id, template_code = callback.data.split(":", 4)
    if target_kind == "order":
        details = order_repository.get_order_details(target_id)
        if details is None:
            await callback.answer("Заявка не найдена.", show_alert=True)
            return
        await callback.message.bot.send_message(details["telegram_id"], _template_text(template_code, target_id))
    else:
        request = support_request_repository.get(target_id)
        if request is None:
            await callback.answer("Запрос не найден.", show_alert=True)
            return
        await callback.message.bot.send_message(request.telegram_id, _template_text(template_code))
    await callback.answer("Сообщение отправлено.")


@router.callback_query(F.data.startswith("slotselect:"))
async def slot_select(callback: CallbackQuery) -> None:
    option_id = callback.data.split(":", 1)[1]
    try:
        visa_case, option = miniapp_repository.select_slot_option_for_user(callback.from_user.id, option_id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer("Дата выбрана.")
    await callback.message.answer(build_user_slot_selected_message(option.option_date, option.option_time))
    await notify_admins(
        callback.message.bot,
        settings,
        build_slot_selected_notification(
            visa_case.id,
            callback.from_user.id,
            callback.from_user.username,
            option.option_date,
            option.option_time,
            option.city,
            option.provider,
        ),
    )
