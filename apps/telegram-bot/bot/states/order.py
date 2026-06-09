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
    applicants_manual_count = State()
    applicant_last_name = State()
    applicant_first_name = State()
    applicant_patronymic = State()
    applicant_birth_date = State()
    applicant_citizenship = State()
    applicant_location = State()
    applicant_relationship = State()
    applicant_passport_number = State()  # Reserved for future secure backend flow. Not used by Telegram UX.
    applicant_passport_expiry = State()  # Reserved for future secure backend flow. Not used by Telegram UX.
    promo_question = State()
    promo_entry = State()
    summary = State()
    payment = State()
    payment_confirmation = State()


class AdminState(StatesGroup):
    search_order = State()
    confirm_cash_order = State()
    change_status_order = State()
    promo_code = State()
    promo_type = State()
    promo_value = State()
    promo_max_uses = State()
    promo_expires_at = State()
    promo_country_codes = State()
    promo_time_window_codes = State()
    promo_note = State()
