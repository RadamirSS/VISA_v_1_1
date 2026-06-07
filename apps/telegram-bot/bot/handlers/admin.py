from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.keyboards.inline import admin_order_actions_keyboard, admin_status_keyboard
from bot.keyboards.main import admin_menu_keyboard, simple_keyboard
from bot.models import OrderStatus, PromoCode
from bot.repositories.orders import OrderRepository
from bot.repositories.promos import PromoRepository
from bot.services.access import is_admin
from bot.states.order import AdminState

router = Router()
settings = get_settings()
order_repository = OrderRepository(settings.database_url)
promo_repository = PromoRepository(settings.database_url)


def _require_admin(message: Message) -> bool:
    return is_admin(message.from_user.id, settings)


async def _deny(message: Message) -> None:
    await message.answer("У вас нет доступа к менеджерскому меню.")


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
    if not orders:
        await message.answer("В очереди нет новых заявок.")
        return
    await message.answer(
        "\n\n".join(
            f"{item['public_number']}\n{item['country_name_ru']} / {item['submission_city']}\n{item['payment_status']} / {item['order_status']}\n{item['created_at'][:16]}"
            for item in orders
        )
    )


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


@router.message(F.text == "🎟 Создать промокод")
async def create_promo_entry(message: Message, state: FSMContext) -> None:
    if not _require_admin(message):
        await _deny(message)
        return
    await state.set_state(AdminState.promo_code)
    await message.answer("Введите код промокода.")


@router.message(AdminState.promo_code)
async def promo_code_step(message: Message, state: FSMContext) -> None:
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
    await state.update_data(type=message.text.strip())
    await state.set_state(AdminState.promo_value)
    await message.answer("Введите значение промокода. Для full_discount и cash_paid можно указать 0.")


@router.message(AdminState.promo_value)
async def promo_value_step(message: Message, state: FSMContext) -> None:
    await state.update_data(value=int(message.text.strip()))
    await state.set_state(AdminState.promo_max_uses)
    await message.answer("Введите максимальное число использований.")


@router.message(AdminState.promo_max_uses)
async def promo_max_uses_step(message: Message, state: FSMContext) -> None:
    await state.update_data(max_uses=int(message.text.strip()))
    await state.set_state(AdminState.promo_expires_at)
    await message.answer("Введите дату окончания в ISO-формате или «-» без ограничения.")


@router.message(AdminState.promo_expires_at)
async def promo_expires_step(message: Message, state: FSMContext) -> None:
    await state.update_data(expires_at=None if message.text.strip() == "-" else message.text.strip())
    await state.set_state(AdminState.promo_country_codes)
    await message.answer("Введите коды стран через запятую или «-» без ограничения.")


@router.message(AdminState.promo_country_codes)
async def promo_country_step(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    await state.update_data(country_codes=[] if raw == "-" else [item.strip().upper() for item in raw.split(",") if item.strip()])
    await state.set_state(AdminState.promo_time_window_codes)
    await message.answer("Введите коды окон поиска через запятую или «-» без ограничения.")


@router.message(AdminState.promo_time_window_codes)
async def promo_window_step(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    await state.update_data(time_window_codes=[] if raw == "-" else [item.strip() for item in raw.split(",") if item.strip()])
    await state.set_state(AdminState.promo_note)
    await message.answer("Введите заметку или «-».")


@router.message(AdminState.promo_note)
async def promo_note_step(message: Message, state: FSMContext) -> None:
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
        await callback.answer("Нет доступа", show_alert=True)
        return
    public_number = callback.data.split(":")[2]
    updated = order_repository.update_order_status(public_number, callback.from_user.id, OrderStatus.SENT_TO_BOOKING_PROVIDER.value)
    await callback.answer("Заявка взята в работу.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(updated["telegram_id"], f"Заявка {public_number} взята в работу менеджером.")


@router.callback_query(F.data.startswith("admin:cash:"))
async def admin_cash_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
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
        await callback.answer("Нет доступа", show_alert=True)
        return
    public_number = callback.data.split(":")[2]
    await callback.answer()
    await callback.message.answer("Выберите новый статус.", reply_markup=admin_status_keyboard(public_number))


@router.callback_query(F.data.startswith("admin:setstatus:"))
async def admin_set_status(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
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
        await callback.answer("Нет доступа", show_alert=True)
        return
    public_number = callback.data.split(":")[2]
    details = order_repository.get_order_details(public_number)
    await callback.answer("Сообщение отправлено.")
    if details:
        await callback.message.bot.send_message(
            details["telegram_id"],
            f"По заявке {public_number}: менеджер проверяет детали. Доступность слотов зависит от внешних систем, мы сообщим о следующих шагах отдельно.",
        )


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel_order(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    public_number = callback.data.split(":")[2]
    updated = order_repository.update_order_status(public_number, callback.from_user.id, OrderStatus.CANCELLED.value, payment_status="cancelled")
    await callback.answer("Заявка отменена.")
    if updated:
        await callback.message.answer(_render_order_details(updated), reply_markup=admin_order_actions_keyboard(public_number))
        await callback.message.bot.send_message(updated["telegram_id"], f"Заявка {public_number} отменена менеджером.")
