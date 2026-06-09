from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .shared import (
    AppointmentRequestState,
    skip_keyboard,
    store_applicant_and_continue,
)

router = Router()


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
    await message.answer("Укажите отчество или нажмите «Пропустить».", reply_markup=skip_keyboard())


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
    await message.answer("Укажите гражданство заявителя.", reply_markup=skip_keyboard())


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
    await message.answer("Укажите отношение к основному заявителю или нажмите «Пропустить».", reply_markup=skip_keyboard())


@router.message(AppointmentRequestState.applicant_relationship)
async def applicant_relationship(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    applicant = data["current_applicant"]
    applicant["relationship"] = None if message.text == "Пропустить" else message.text.strip()
    await state.update_data(current_applicant=applicant)
    await message.answer(
        "Паспортные данные и документы менеджер запросит отдельно через защищенный канал, если они понадобятся. "
        "В Telegram-боте паспортные данные не собираются."
    )
    await store_applicant_and_continue(message, state, applicant)


@router.message(AppointmentRequestState.applicant_passport_number)
async def applicant_passport_number(message: Message, state: FSMContext) -> None:
    # Reserved for future secure backend flow. Not used by Telegram UX.
    await state.set_state(AppointmentRequestState.applicant_relationship)
    await message.answer(
        "Сбор паспортных данных в Telegram отключен. Для production нужен отдельный защищенный backend/storage flow.",
        reply_markup=skip_keyboard(),
    )


@router.message(AppointmentRequestState.applicant_passport_expiry)
async def applicant_passport_expiry(message: Message, state: FSMContext) -> None:
    # Reserved for future secure backend flow. Not used by Telegram UX.
    await state.set_state(AppointmentRequestState.applicant_relationship)
    await message.answer(
        "Сбор паспортных данных в Telegram отключен. Для production нужен отдельный защищенный backend/storage flow.",
        reply_markup=skip_keyboard(),
    )
