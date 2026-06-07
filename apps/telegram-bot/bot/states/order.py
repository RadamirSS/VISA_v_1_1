from aiogram.fsm.state import State, StatesGroup


class OnboardingState(StatesGroup):
    waiting_for_consent = State()


class RegistrationState(StatesGroup):
    last_name = State()
    first_name = State()
    patronymic = State()
    birth_date = State()
    citizenship = State()
    location = State()
    phone = State()
    email = State()


class AppointmentRequestState(StatesGroup):
    country = State()
    city = State()
    purpose = State()
    time_window = State()
    applicants_count = State()
    applicants = State()
    promo = State()
    summary = State()
