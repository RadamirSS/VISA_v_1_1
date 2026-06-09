from __future__ import annotations

from aiogram import Bot

from bot.config import Settings
from bot.models import BookingOrder, SupportRequest


def build_new_order_notification(order: BookingOrder) -> str:
    return (
        f"Новая заявка #{order.public_number}\n"
        f"Страна: {order.country_name_ru}\n"
        f"Город подачи: {order.submission_city}\n"
        f"Окно поиска: {order.time_window_code}\n"
        f"Оплата: {order.payment_status}\n"
        f"Статус: {order.order_status}"
    )


def build_manager_contact_notification(telegram_id: int, username: str | None) -> str:
    lines = [
        "Клиент запросил связь с менеджером.",
        f"Telegram ID: {telegram_id}",
    ]
    if username:
        lines.append(f"Username: @{username}")
    return "\n".join(lines)


def build_access_key_activated_notification(code: str) -> str:
    return f"Ключ доступа {code} активирован. Теперь можно создать заявку на запись."


def build_support_request_notification(request: SupportRequest) -> str:
    lines = [
        f"Новый запрос клиента: {request.id}",
        f"Telegram ID: {request.telegram_id}",
        f"Статус: {request.status}",
    ]
    if request.username:
        lines.append(f"Username: @{request.username}")
    if request.message:
        lines.append(f"Сообщение: {request.message}")
    return "\n".join(lines)


def build_profiles_completed_notification(
    telegram_id: int,
    username: str | None,
    applicants_count: int,
    case_status: str,
) -> str:
    lines = [
        "Клиент заполнил анкеты.",
        f"Telegram: @{username}" if username else f"Telegram ID: {telegram_id}",
        f"telegram_id: {telegram_id}",
        f"Заявителей: {applicants_count}",
        f"Статус: {case_status}",
        "Откройте менеджерский интерфейс для проверки.",
    ]
    return "\n".join(lines)


def build_case_submitted_notification(
    case_id: str,
    telegram_id: int,
    username: str | None,
    applicants_count: int,
    country_name: str | None,
    city: str | None,
    provider: str | None,
    travel_purpose: str | None,
    case_status: str,
) -> str:
    lines = [
        "Новая заявка отправлена на проверку.",
        f"Кейс: {case_id}",
        f"Клиент: @{username} / {telegram_id}" if username else f"Клиент: {telegram_id}",
        f"Заявителей: {applicants_count}",
        f"Страна: {country_name or 'не выбрана'}",
        f"Город подачи: {city or 'уточнить с менеджером'}",
        f"Визовый центр: {provider or 'консультация / уточнить'}",
        f"Цель: {travel_purpose or 'уточнить'}",
        f"Статус: {case_status}",
        "Откройте менеджерский интерфейс для проверки анкет.",
    ]
    return "\n".join(lines)


def build_user_case_submitted_message() -> str:
    return "Ваша заявка отправлена менеджеру на проверку.\nМенеджер проверит данные и сообщит следующие шаги."


def build_slot_options_sent_to_manager(case_id: str, options_count: int) -> str:
    return f"Варианты дат отправлены клиенту.\nКейс: {case_id}\nВариантов: {options_count}"


def build_slot_options_message() -> str:
    return "Менеджер подобрал возможные даты записи.\nВыберите удобный вариант:"


def build_slot_selected_notification(
    case_id: str,
    telegram_id: int,
    username: str | None,
    option_date: str,
    option_time: str,
    city: str | None,
    provider: str | None,
) -> str:
    lines = [
        "Клиент выбрал дату записи.",
        f"Кейс: {case_id}",
        f"Клиент: @{username} / {telegram_id}" if username else f"Клиент: {telegram_id}",
        f"Дата: {option_date}",
        f"Время: {option_time}",
        f"Город: {city or 'не указан'}",
        f"Провайдер: {provider or 'не указан'}",
    ]
    return "\n".join(lines)


def build_user_slot_selected_message(option_date: str, option_time: str) -> str:
    return f"Вы выбрали дату: {option_date} {option_time}.\nМенеджер подтвердит запись и сообщит дальнейшие шаги."


def build_appointment_confirmed_message(
    option_date: str | None,
    option_time: str | None,
    city: str | None,
    provider: str | None,
) -> str:
    return (
        "Запись подтверждена.\n"
        f"Дата: {option_date or '-'}\n"
        f"Время: {option_time or '-'}\n"
        f"Город: {city or '-'}\n"
        f"Визовый центр: {provider or '-'}\n"
        "Менеджер сообщит, какие документы нужно подготовить."
    )


def build_documents_requested_message() -> str:
    return "Менеджер запросил документы.\nОткройте личный кабинет → Документы."


def build_agency_document_ready_message(title: str) -> str:
    return f"Документ от агентства готов: {title}.\nОткройте личный кабинет → Документы."


def build_agency_document_transferred_separately_message(title: str) -> str:
    return (
        f"Документ от агентства: {title}.\n"
        "Менеджер передаст его отдельно.\n"
        "Откройте личный кабинет → Документы."
    )


def build_client_uploaded_notification(case_public_number: str, document_title: str, status: str) -> str:
    return (
        "Клиент загрузил документ.\n"
        f"Кейс: {case_public_number}\n"
        f"Документ: {document_title}\n"
        f"Статус: {status}"
    )


async def notify_admins(bot: Bot, settings: Settings, text: str) -> None:
    for admin_id in settings.bot_admin_ids:
        await bot.send_message(admin_id, text)
