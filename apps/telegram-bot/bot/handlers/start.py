from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.keyboards.inline import consent_keyboard
from bot.keyboards.main import admin_menu_keyboard, main_menu_keyboard, simple_keyboard
from bot.repositories.users import UserRepository
from bot.services.access import is_admin
from bot.states.order import OnboardingState, RegistrationState
from bot.texts.common import HOW_IT_WORKS, PRIVACY_NOTE

router = Router()
settings = get_settings()
user_repository = UserRepository(settings.database_url)

def _user_summary_text() -> str:
    return (
        "Бот помогает оформить заявку на запись, применить промокод, отследить статус и связаться с менеджером.\n\n"
        f"{PRIVACY_NOTE}"
    )


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user and user_repository.is_registered(user):
        await state.clear()
        await message.answer(
            "С возвращением! Здесь можно создать новую заявку, проверить статусы или связаться с менеджером.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(OnboardingState.waiting_for_consent)
    await message.answer(
        "Здравствуйте! Это основной клиентский бот агентства по визовой поддержке.\n\n"
        f"{_user_summary_text()}\n\n"
        "Чтобы продолжить, подтвердите согласие на обработку данных.",
        reply_markup=consent_keyboard(),
    )


@router.callback_query(F.data == "consent:details")
async def consent_details_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Мы используем данные только для регистрации, связи и создания заявки. "
        "Паспортные данные и документы по умолчанию здесь не собираются."
    )


@router.callback_query(F.data == "consent:cancel")
async def consent_cancel_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.answer("Сценарий остановлен. Вернуться можно командой /start.")


@router.callback_query(F.data == "consent:accept")
async def consent_accept_handler(callback: CallbackQuery, state: FSMContext) -> None:
    from_user = callback.from_user
    user_repository.mark_consent(from_user.id, from_user.username, from_user.first_name, from_user.last_name)
    await state.set_state(RegistrationState.last_name)
    await callback.answer()
    await callback.message.answer("Спасибо. Теперь зарегистрируем профиль. Укажите фамилию.")


@router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    if is_admin(message.from_user.id, settings):
        await message.answer("Главное меню", reply_markup=main_menu_keyboard())
        await message.answer("Менеджерское меню", reply_markup=admin_menu_keyboard())
        return
    await message.answer("Главное меню", reply_markup=main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == "❓ Как это работает")
async def help_handler(message: Message) -> None:
    await message.answer(HOW_IT_WORKS)


@router.message(Command("status"))
@router.message(F.text == "📌 Мои заявки")
async def status_handler(message: Message) -> None:
    orders = order_repository.list_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет сохраненных заявок. Создать новую можно через кнопку «📝 Создать заявку на запись».")
        return
    lines = []
    for order in orders:
        lines.append(
            f"{order['public_number']}\n"
            f"Страна: {order['country_name_ru']}\n"
            f"Город: {order['submission_city']}\n"
            f"Окно: {order['time_window_code']}\n"
            f"Оплата: {order['payment_status']}\n"
            f"Статус: {order['order_status']}\n"
            f"Создано: {order['created_at'][:10]}"
        )
    await message.answer("\n\n".join(lines))


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Текущий сценарий остановлен. Можно вернуться в меню командой /menu.", reply_markup=main_menu_keyboard())


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if not is_admin(message.from_user.id, settings):
        await message.answer("У вас нет доступа к менеджерскому меню.")
        return
    await message.answer("Меню менеджера", reply_markup=admin_menu_keyboard())


@router.message(RegistrationState.last_name)
async def registration_last_name(message: Message, state: FSMContext) -> None:
    await state.update_data(last_name=message.text.strip())
    await state.set_state(RegistrationState.first_name)
    await message.answer("Укажите имя.")


@router.message(RegistrationState.first_name)
async def registration_first_name(message: Message, state: FSMContext) -> None:
    await state.update_data(first_name=message.text.strip())
    await state.set_state(RegistrationState.patronymic)
    await message.answer("Укажите отчество или нажмите «Пропустить».", reply_markup=simple_keyboard(["Пропустить"]))


@router.message(RegistrationState.patronymic)
async def registration_patronymic(message: Message, state: FSMContext) -> None:
    patronymic = None if message.text == "Пропустить" else message.text.strip()
    await state.update_data(patronymic=patronymic)
    await state.set_state(RegistrationState.birth_date)
    await message.answer("Укажите дату рождения в любом понятном формате, например 12.03.1991.")


@router.message(RegistrationState.birth_date)
async def registration_birth_date(message: Message, state: FSMContext) -> None:
    await state.update_data(birth_date=message.text.strip())
    await state.set_state(RegistrationState.citizenship)
    await message.answer("Укажите гражданство. По умолчанию можно выбрать «Россия».", reply_markup=simple_keyboard(["Россия"]))


@router.message(RegistrationState.citizenship)
async def registration_citizenship(message: Message, state: FSMContext) -> None:
    await state.update_data(citizenship=message.text.strip() or "Россия")
    await state.set_state(RegistrationState.location)
    await message.answer("Укажите текущую страну и город.")


@router.message(RegistrationState.location)
async def registration_location(message: Message, state: FSMContext) -> None:
    await state.update_data(current_location=message.text.strip())
    await state.set_state(RegistrationState.phone)
    await message.answer("Укажите телефон для связи.")


@router.message(RegistrationState.phone)
async def registration_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(RegistrationState.email)
    await message.answer("Укажите email или нажмите «Пропустить».", reply_markup=simple_keyboard(["Пропустить"]))


@router.message(RegistrationState.email)
async def registration_email(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    email = None if message.text == "Пропустить" else message.text.strip()
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user is None:
        user = user_repository.mark_consent(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    user.last_name = data["last_name"]
    user.first_name = data["first_name"]
    user.patronymic = data.get("patronymic")
    user.birth_date = data["birth_date"]
    user.citizenship = data["citizenship"]
    user.current_location = data["current_location"]
    user.phone = data["phone"]
    user.email = email
    user.username = message.from_user.username or user.username
    user_repository.save(user)
    await state.clear()
    await message.answer(
        "Профиль сохранен. Теперь можно создать заявку, посмотреть статусы или связаться с менеджером.",
        reply_markup=main_menu_keyboard(),
    )
