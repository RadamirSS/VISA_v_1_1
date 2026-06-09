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
from bot.services.access_keys import normalize_access_key, validate_access_key
from bot.states.order import AppointmentRequestState, OnboardingState, RegistrationState
from bot.texts.common import HOW_IT_WORKS, PRIVACY_NOTE
from bot.repositories.access_keys import AccessKeyRepository

router = Router()
settings = get_settings()
user_repository = UserRepository(settings.database_url)
access_key_repository = AccessKeyRepository(settings.database_url)

def _user_summary_text() -> str:
    return (
        "Бот помогает оформить заявку на запись, активировать ключ доступа, отследить статус и связаться с менеджером.\n\n"
        f"{PRIVACY_NOTE}"
    )


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user and user_repository.is_registered(user):
        await state.clear()
        await message.answer(
            "С возвращением! Здесь можно создать новую заявку, проверить статусы или связаться с менеджером.",
            reply_markup=main_menu_keyboard(settings.client_miniapp_url),
        )
        return

    await state.set_state(OnboardingState.waiting_for_consent)
    await message.answer(
        "Здравствуйте! Это основной клиентский бот агентства по визовой поддержке.\n\n"
        f"{_user_summary_text()}\n\n"
        "Для создания заявки нужен ключ доступа от менеджера агентства.\n"
        "Если вы уже оплатили услугу или менеджер пригласил вас в бот, нажмите «🔑 Ввести ключ доступа» после регистрации.\n\n"
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
        await message.answer("Главное меню", reply_markup=main_menu_keyboard(settings.client_miniapp_url))
        await message.answer("Менеджерское меню", reply_markup=admin_menu_keyboard())
        return
    await message.answer("Главное меню", reply_markup=main_menu_keyboard(settings.client_miniapp_url))


@router.message(Command("help"))
@router.message(F.text == "❓ Как это работает")
async def help_handler(message: Message) -> None:
    await message.answer(HOW_IT_WORKS)


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Текущий сценарий остановлен. Можно вернуться в меню командой /menu.",
        reply_markup=main_menu_keyboard(settings.client_miniapp_url),
    )


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
        "Профиль сохранен. Для создания заявки активируйте ключ доступа от менеджера через кнопку «🔑 Ввести ключ доступа».",
        reply_markup=main_menu_keyboard(settings.client_miniapp_url),
    )


@router.message(F.text == "🔑 Ввести ключ доступа")
async def access_key_entry(message: Message, state: FSMContext) -> None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user is None or not user_repository.is_registered(user):
        await message.answer("Сначала завершите согласие и регистрацию через /start.")
        return
    await state.clear()
    await state.set_state(AppointmentRequestState.access_key_entry)
    await message.answer("Введите ключ доступа, который вы получили от менеджера.")


@router.message(AppointmentRequestState.access_key_entry)
async def activate_access_key(message: Message, state: FSMContext) -> None:
    user = user_repository.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Сначала завершите регистрацию через /start.")
        return
    code = normalize_access_key(message.text)
    access_key = access_key_repository.get_by_code(code)
    result = validate_access_key(access_key, message.from_user.id)
    if not result.valid:
        await message.answer(result.error or "Ключ доступа недействителен.")
        return
    activated = access_key_repository.bind_and_activate(code, user.id, message.from_user.id)
    await state.clear()
    if activated is None:
        await message.answer("Не удалось активировать ключ доступа.")
        return
    await message.answer(
        "Ключ доступа активирован. Теперь вы можете создать заявку на запись.",
        reply_markup=main_menu_keyboard(settings.client_miniapp_url),
    )


@router.message(F.text == "📋 Открыть личный кабинет")
async def open_cabinet(message: Message) -> None:
    if not settings.client_miniapp_url:
        await message.answer("Личный кабинет пока не настроен. Обратитесь к менеджеру.")
        return
    await message.answer(
        "В личном кабинете вы можете заполнить анкеты, создать заявку и выбрать город подачи. "
        "Используйте кнопку Mini App в меню выше."
    )
