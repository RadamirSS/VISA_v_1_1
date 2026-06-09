from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import (
    ApplicantProfile,
    ApplicantProfileStatus,
    AppointmentSlotOffer,
    AppointmentSlotOfferStatus,
    AppointmentSlotOption,
    AppointmentSlotOptionStatus,
    ConsulateOption,
    CountryOption,
    User,
    VisaCase,
    VisaCaseStatus,
)
from bot.services.case_status import format_case_public_number
from bot.services.config_loader import load_consulates, load_countries
from bot.services.slot_offers import ParsedSlotOption

REQUIRED_COMPLETION_FIELDS = (
    "last_name_latin",
    "first_name_latin",
    "last_name_cyrillic",
    "first_name_cyrillic",
    "birth_date",
    "birth_place",
    "citizenship",
    "phone",
    "residence_country",
    "residence_city",
    "residence_address",
    "passport_number",
    "passport_issue_date",
    "passport_expiry_date",
    "passport_issuing_country",
    "desired_country_code",
    "travel_purpose",
)

CONSULTATION_COUNTRY_CODE = "CONSULTATION"
CONSULTATION_COUNTRY_NAME_RU = "Нужна консультация"
LOCKED_CASE_STATUSES = {
    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
    VisaCaseStatus.MANAGER_REVIEWING.value,
    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value,
    VisaCaseStatus.SLOT_OPTIONS_SENT.value,
    VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value,
    VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value,
    VisaCaseStatus.APPOINTMENT_CONFIRMED.value,
    VisaCaseStatus.CLOSED.value,
}
EDITABLE_CASE_STATUSES = {
    VisaCaseStatus.DRAFT.value,
    VisaCaseStatus.PROFILES_COMPLETED.value,
    VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value,
    VisaCaseStatus.NEEDS_CLARIFICATION.value,
}
SLOT_ELIGIBLE_CASE_STATUSES = {
    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
    VisaCaseStatus.MANAGER_REVIEWING.value,
    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value,
    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value,
}
MANAGER_QUEUE_STATUSES = (
    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value,
    VisaCaseStatus.WAITING_MANAGER_REVIEW.value,
    VisaCaseStatus.NEEDS_CLARIFICATION.value,
    VisaCaseStatus.MANAGER_REVIEWING.value,
    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value,
    VisaCaseStatus.SLOT_OPTIONS_SENT.value,
    VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value,
    VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value,
    VisaCaseStatus.APPOINTMENT_CONFIRMED.value,
)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def calculate_completion(profile: ApplicantProfile) -> tuple[int, str]:
    filled = 0
    for field_name in REQUIRED_COMPLETION_FIELDS:
        if _clean(getattr(profile, field_name)):
            filled += 1
    percent = round((filled / len(REQUIRED_COMPLETION_FIELDS)) * 100)
    if percent == 0:
        status = ApplicantProfileStatus.DRAFT.value
    elif percent == 100:
        status = ApplicantProfileStatus.COMPLETED.value
    else:
        status = ApplicantProfileStatus.INCOMPLETE.value
    return percent, status


class MiniAppRepository:
    def __init__(self, database_url: str, repo_root: Path | None = None):
        self._path = sqlite_path_from_url(database_url)
        self._repo_root = repo_root

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_countries(self) -> list[CountryOption]:
        if self._repo_root is None:
            return []
        return load_countries(self._repo_root)

    def list_consulates(self, country_code: str) -> list[ConsulateOption]:
        if self._repo_root is None:
            return []
        return [item for item in load_consulates(self._repo_root) if item.country_code == country_code]

    def find_country(self, country_code: str) -> CountryOption | None:
        return next((item for item in self.list_countries() if item.code == country_code), None)

    def find_consulate(self, country_code: str, city: str, provider: str) -> ConsulateOption | None:
        city_clean = (city or "").strip()
        provider_clean = (provider or "").strip()
        return next(
            (
                item
                for item in self.list_consulates(country_code)
                if item.city == city_clean and item.provider == provider_clean
            ),
            None,
        )

    def get_case_for_telegram_user(self, telegram_id: int) -> VisaCase | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM visa_cases WHERE telegram_id = ? ORDER BY created_at DESC LIMIT 1",
                (telegram_id,),
            ).fetchone()
        return self._case_from_row(row)

    def get_case_by_id(self, telegram_id: int, case_id: str) -> VisaCase | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM visa_cases WHERE telegram_id = ? AND id = ?",
                (telegram_id, case_id),
            ).fetchone()
        return self._case_from_row(row)

    def get_case_by_any_id(self, case_id: str) -> VisaCase | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM visa_cases WHERE id = ?", (case_id,)).fetchone()
        return self._case_from_row(row)

    def get_case_manager_context(self, case_id: str) -> tuple[VisaCase | None, str | None]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT visa_cases.*, users.username AS username
                FROM visa_cases
                LEFT JOIN users ON users.id = visa_cases.user_id
                WHERE visa_cases.id = ?
                """,
                (case_id,),
            ).fetchone()
        if row is None:
            return None, None
        username = row["username"]
        return self._case_from_row(row), username

    def list_applicants_for_case(self, case_id: str) -> list[ApplicantProfile]:
        visa_case = self.get_case_by_any_id(case_id)
        if visa_case is None:
            return []
        return self.list_applicants(visa_case.telegram_id)

    def list_manager_active_cases(self, limit: int = 200) -> list[VisaCase]:
        placeholders = ", ".join("?" for _ in MANAGER_QUEUE_STATUSES)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM visa_cases
                WHERE status IN ({placeholders})
                ORDER BY COALESCE(submitted_at, updated_at) DESC
                LIMIT ?
                """,
                (*MANAGER_QUEUE_STATUSES, limit),
            ).fetchall()
        return [self._case_from_row(row) for row in rows if row is not None]

    def list_manager_active_cases_with_username(self, limit: int = 200) -> list[tuple[VisaCase, str | None]]:
        placeholders = ", ".join("?" for _ in MANAGER_QUEUE_STATUSES)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT visa_cases.*, users.username AS username
                FROM visa_cases
                LEFT JOIN users ON users.id = visa_cases.user_id
                WHERE visa_cases.status IN ({placeholders})
                ORDER BY COALESCE(visa_cases.submitted_at, visa_cases.updated_at) DESC
                LIMIT ?
                """,
                (*MANAGER_QUEUE_STATUSES, limit),
            ).fetchall()
        result: list[tuple[VisaCase, str | None]] = []
        for row in rows:
            visa_case = self._case_from_row(row)
            if visa_case is not None:
                result.append((visa_case, row["username"]))
        return result

    def get_case_by_public_number(self, public_number: str) -> VisaCase | None:
        normalized = public_number.strip().upper()
        if not normalized.startswith("VISA-CASE-"):
            return None
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM visa_cases ORDER BY created_at DESC").fetchall()
        for row in rows:
            visa_case = self._case_from_row(row)
            if visa_case is not None and format_case_public_number(visa_case).upper() == normalized:
                return visa_case
        return None

    def get_case_by_telegram_id_for_manager(self, telegram_id: int) -> VisaCase | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM visa_cases
                WHERE telegram_id = ?
                ORDER BY COALESCE(submitted_at, updated_at) DESC
                LIMIT 1
                """,
                (telegram_id,),
            ).fetchone()
        return self._case_from_row(row)

    def get_case_by_username(self, username: str) -> VisaCase | None:
        normalized = username.strip().lstrip("@").lower()
        if not normalized:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT visa_cases.*
                FROM visa_cases
                JOIN users ON users.id = visa_cases.user_id
                WHERE LOWER(users.username) = ?
                ORDER BY COALESCE(visa_cases.submitted_at, visa_cases.updated_at) DESC
                LIMIT 1
                """,
                (normalized,),
            ).fetchone()
        return self._case_from_row(row)

    def resolve_case_lookup(self, query: str) -> VisaCase | None:
        raw = query.strip()
        if not raw:
            return None
        upper = raw.upper()
        if upper.startswith("VISA-CASE-"):
            return self.get_case_by_public_number(upper)
        if UUID_PATTERN.match(raw):
            return self.get_case_by_any_id(raw)
        if raw.isdigit():
            return self.get_case_by_telegram_id_for_manager(int(raw))
        if raw.startswith("@"):
            return self.get_case_by_username(raw)
        if re.fullmatch(r"[A-Za-z0-9_]{3,32}", raw):
            return self.get_case_by_username(raw)
        return self.get_case_by_any_id(raw)

    def has_slot_offers(self, case_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM appointment_slot_offers WHERE case_id = ? LIMIT 1",
                (case_id,),
            ).fetchone()
        return row is not None

    def has_selected_slot(self, visa_case: VisaCase) -> bool:
        return bool(visa_case.selected_slot_option_id or visa_case.selected_appointment_date)

    def update_manager_case_status(self, case_id: str, status: str, admin_id: int) -> VisaCase:
        del admin_id
        visa_case = self.get_case_by_any_id(case_id)
        if visa_case is None:
            raise ValueError("Кейс не найден.")
        visa_case.status = status
        visa_case.updated_at = now_iso()
        if status == VisaCaseStatus.MANAGER_REVIEWING.value and not visa_case.manager_reviewed_at:
            visa_case.manager_reviewed_at = visa_case.updated_at
        self.save_case(visa_case)
        return visa_case

    def ensure_case(self, user: User, access_key_id: str | None, access_key_code: str | None) -> VisaCase:
        existing = self.get_case_for_telegram_user(user.telegram_id)
        if existing is not None:
            if access_key_id and not existing.access_key_id:
                existing.access_key_id = access_key_id
                existing.access_key_code = access_key_code
                existing.updated_at = now_iso()
                self.save_case(existing)
            return existing
        case = VisaCase(
            id=str(uuid4()),
            user_id=user.id,
            telegram_id=user.telegram_id,
            access_key_id=access_key_id,
            access_key_code=access_key_code,
            status=VisaCaseStatus.PROFILES_IN_PROGRESS.value,
            applicants_count=0,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        self.save_case(case)
        return case

    def save_case(self, visa_case: VisaCase) -> None:
        payload = asdict(visa_case)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO visa_cases (
                  id, user_id, telegram_id, access_key_id, access_key_code, status,
                  applicants_count, desired_country_code, desired_country_name_ru,
                  preferred_submission_city, submission_provider, submission_provider_type,
                  submission_jurisdiction, submission_verification_status, travel_purpose,
                  approximate_travel_start_date, approximate_travel_end_date, client_comment,
                  submitted_at, manager_reviewed_at, selected_slot_option_id,
                  selected_appointment_date, selected_appointment_time, selected_appointment_city,
                  selected_appointment_provider, appointment_confirmed_at, created_at, updated_at
                ) VALUES (
                  :id, :user_id, :telegram_id, :access_key_id, :access_key_code, :status,
                  :applicants_count, :desired_country_code, :desired_country_name_ru,
                  :preferred_submission_city, :submission_provider, :submission_provider_type,
                  :submission_jurisdiction, :submission_verification_status, :travel_purpose,
                  :approximate_travel_start_date, :approximate_travel_end_date, :client_comment,
                  :submitted_at, :manager_reviewed_at, :selected_slot_option_id,
                  :selected_appointment_date, :selected_appointment_time, :selected_appointment_city,
                  :selected_appointment_provider, :appointment_confirmed_at, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                  access_key_id = excluded.access_key_id,
                  access_key_code = excluded.access_key_code,
                  status = excluded.status,
                  applicants_count = excluded.applicants_count,
                  desired_country_code = excluded.desired_country_code,
                  desired_country_name_ru = excluded.desired_country_name_ru,
                  preferred_submission_city = excluded.preferred_submission_city,
                  submission_provider = excluded.submission_provider,
                  submission_provider_type = excluded.submission_provider_type,
                  submission_jurisdiction = excluded.submission_jurisdiction,
                  submission_verification_status = excluded.submission_verification_status,
                  travel_purpose = excluded.travel_purpose,
                  approximate_travel_start_date = excluded.approximate_travel_start_date,
                  approximate_travel_end_date = excluded.approximate_travel_end_date,
                  client_comment = excluded.client_comment,
                  submitted_at = excluded.submitted_at,
                  manager_reviewed_at = excluded.manager_reviewed_at,
                  selected_slot_option_id = excluded.selected_slot_option_id,
                  selected_appointment_date = excluded.selected_appointment_date,
                  selected_appointment_time = excluded.selected_appointment_time,
                  selected_appointment_city = excluded.selected_appointment_city,
                  selected_appointment_provider = excluded.selected_appointment_provider,
                  appointment_confirmed_at = excluded.appointment_confirmed_at,
                  updated_at = excluded.updated_at
                """,
                payload,
            )
            connection.commit()

    def create_case(self, user: User, access_key_id: str | None, access_key_code: str | None) -> VisaCase:
        visa_case = self.ensure_case(user, access_key_id, access_key_code)
        applicants = self.list_applicants(user.telegram_id)
        visa_case.applicants_count = len(applicants)
        visa_case.status = (
            VisaCaseStatus.PROFILES_COMPLETED.value
            if applicants and all(item.status == ApplicantProfileStatus.COMPLETED.value for item in applicants)
            else VisaCaseStatus.PROFILES_IN_PROGRESS.value
        )
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        return visa_case

    def set_applicants_count(self, visa_case: VisaCase, count: int) -> VisaCase:
        visa_case.applicants_count = count
        visa_case.status = VisaCaseStatus.PROFILES_NOT_STARTED.value if count else VisaCaseStatus.PROFILES_IN_PROGRESS.value
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        self._sync_applicant_slots(visa_case)
        return self.refresh_case_status(visa_case.telegram_id)

    def create_applicant(self, visa_case: VisaCase) -> ApplicantProfile:
        position = len(self.list_applicants(visa_case.telegram_id)) + 1
        profile = ApplicantProfile(
            id=str(uuid4()),
            user_id=visa_case.user_id,
            telegram_id=visa_case.telegram_id,
            case_id=visa_case.id,
            position=position,
            role="primary" if position == 1 else "group_member",
            status=ApplicantProfileStatus.DRAFT.value,
            completion_percent=0,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        self.save_applicant(profile)
        visa_case.applicants_count = position
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        self.refresh_case_status(visa_case.telegram_id)
        return profile

    def list_applicants(self, telegram_id: int) -> list[ApplicantProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM applicant_profiles WHERE telegram_id = ? ORDER BY position ASC",
                (telegram_id,),
            ).fetchall()
        return [self._applicant_from_row(row) for row in rows]

    def list_incomplete_applicants(self, telegram_id: int) -> list[ApplicantProfile]:
        return [item for item in self.list_applicants(telegram_id) if item.status != ApplicantProfileStatus.COMPLETED.value]

    def get_applicant(self, telegram_id: int, applicant_id: str) -> ApplicantProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM applicant_profiles WHERE telegram_id = ? AND id = ?",
                (telegram_id, applicant_id),
            ).fetchone()
        return self._applicant_from_row(row)

    def save_applicant(self, profile: ApplicantProfile) -> ApplicantProfile:
        profile.completion_percent, profile.status = calculate_completion(profile)
        profile.updated_at = now_iso()
        payload = asdict(profile)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO applicant_profiles (
                  id, user_id, telegram_id, case_id, position, role, status, completion_percent,
                  last_name_latin, first_name_latin, last_name_cyrillic, first_name_cyrillic,
                  patronymic, birth_date, birth_place, citizenship, gender, marital_status,
                  phone, email, residence_country, residence_city, residence_address, postal_code,
                  passport_number, passport_issue_date, passport_expiry_date, passport_issuing_authority,
                  passport_issuing_country, desired_country_code, desired_country_name_ru, travel_purpose,
                  approximate_travel_dates, entries_count, preferred_submission_city, created_at, updated_at
                ) VALUES (
                  :id, :user_id, :telegram_id, :case_id, :position, :role, :status, :completion_percent,
                  :last_name_latin, :first_name_latin, :last_name_cyrillic, :first_name_cyrillic,
                  :patronymic, :birth_date, :birth_place, :citizenship, :gender, :marital_status,
                  :phone, :email, :residence_country, :residence_city, :residence_address, :postal_code,
                  :passport_number, :passport_issue_date, :passport_expiry_date, :passport_issuing_authority,
                  :passport_issuing_country, :desired_country_code, :desired_country_name_ru, :travel_purpose,
                  :approximate_travel_dates, :entries_count, :preferred_submission_city, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                  case_id = excluded.case_id,
                  position = excluded.position,
                  role = excluded.role,
                  status = excluded.status,
                  completion_percent = excluded.completion_percent,
                  last_name_latin = excluded.last_name_latin,
                  first_name_latin = excluded.first_name_latin,
                  last_name_cyrillic = excluded.last_name_cyrillic,
                  first_name_cyrillic = excluded.first_name_cyrillic,
                  patronymic = excluded.patronymic,
                  birth_date = excluded.birth_date,
                  birth_place = excluded.birth_place,
                  citizenship = excluded.citizenship,
                  gender = excluded.gender,
                  marital_status = excluded.marital_status,
                  phone = excluded.phone,
                  email = excluded.email,
                  residence_country = excluded.residence_country,
                  residence_city = excluded.residence_city,
                  residence_address = excluded.residence_address,
                  postal_code = excluded.postal_code,
                  passport_number = excluded.passport_number,
                  passport_issue_date = excluded.passport_issue_date,
                  passport_expiry_date = excluded.passport_expiry_date,
                  passport_issuing_authority = excluded.passport_issuing_authority,
                  passport_issuing_country = excluded.passport_issuing_country,
                  desired_country_code = excluded.desired_country_code,
                  desired_country_name_ru = excluded.desired_country_name_ru,
                  travel_purpose = excluded.travel_purpose,
                  approximate_travel_dates = excluded.approximate_travel_dates,
                  entries_count = excluded.entries_count,
                  preferred_submission_city = excluded.preferred_submission_city,
                  updated_at = excluded.updated_at
                """,
                payload,
            )
            connection.commit()
        return profile

    def update_applicant(self, telegram_id: int, applicant_id: str, updates: dict[str, Any]) -> ApplicantProfile | None:
        profile = self.get_applicant(telegram_id, applicant_id)
        if profile is None:
            return None
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, _clean(value))
        saved = self.save_applicant(profile)
        self.refresh_case_status(telegram_id)
        return saved

    def copy_from_primary(self, telegram_id: int, applicant_id: str) -> ApplicantProfile | None:
        target = self.get_applicant(telegram_id, applicant_id)
        primary = next((item for item in self.list_applicants(telegram_id) if item.position == 1), None)
        if target is None or primary is None or target.id == primary.id:
            return target
        for field_name in ("phone", "email", "residence_country", "residence_city", "residence_address", "postal_code"):
            setattr(target, field_name, getattr(primary, field_name))
        saved = self.save_applicant(target)
        self.refresh_case_status(telegram_id)
        return saved

    def update_case(self, telegram_id: int, updates: dict[str, Any]) -> VisaCase | None:
        visa_case = self.get_case_for_telegram_user(telegram_id)
        if visa_case is None:
            return None
        if visa_case.status in LOCKED_CASE_STATUSES:
            raise ValueError("Заявка уже отправлена и пока недоступна для редактирования.")

        country_code = _clean(updates.get("desired_country_code", visa_case.desired_country_code))
        country_name = _clean(updates.get("desired_country_name_ru", visa_case.desired_country_name_ru))
        if country_code:
            if country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}:
                country_name = country_name or CONSULTATION_COUNTRY_NAME_RU
            else:
                country = self.find_country(country_code)
                if country is None:
                    raise ValueError("Выбранная страна отсутствует в конфигурации.")
                country_name = country.name_ru

        city = _clean(updates.get("preferred_submission_city", visa_case.preferred_submission_city))
        provider = _clean(updates.get("submission_provider", visa_case.submission_provider))
        consulate = None
        if country_code and country_code not in {CONSULTATION_COUNTRY_CODE, "OTHER"} and (city or provider):
            if not city or not provider:
                raise ValueError("Для выбранной страны нужно указать и город подачи, и визовый центр.")
            consulate = self.find_consulate(country_code, city, provider)
            if consulate is None:
                raise ValueError("Выбранный город или визовый центр не соответствует конфигурации.")

        for key, value in updates.items():
            if hasattr(visa_case, key):
                setattr(visa_case, key, _clean(value))

        visa_case.desired_country_code = country_code
        visa_case.desired_country_name_ru = country_name
        if consulate is not None:
            visa_case.preferred_submission_city = consulate.city
            visa_case.submission_provider = consulate.provider
            visa_case.submission_provider_type = consulate.type
            visa_case.submission_jurisdiction = consulate.jurisdiction
            visa_case.submission_verification_status = consulate.verification_status
        elif country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}:
            visa_case.preferred_submission_city = None
            visa_case.submission_provider = None
            visa_case.submission_provider_type = None
            visa_case.submission_jurisdiction = None
            visa_case.submission_verification_status = None

        if visa_case.desired_country_code:
            visa_case.status = (
                VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value
                if visa_case.desired_country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}
                else VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value
            )
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        return visa_case

    def submit_case(self, telegram_id: int) -> tuple[VisaCase, list[ApplicantProfile]]:
        visa_case = self.get_case_for_telegram_user(telegram_id)
        if visa_case is None:
            raise ValueError("Визовая заявка еще не создана.")
        if visa_case.status in LOCKED_CASE_STATUSES:
            raise ValueError("Заявка уже отправлена менеджеру.")
        applicants = self.list_applicants(telegram_id)
        if not applicants:
            raise ValueError("Сначала добавьте заявителей.")
        incomplete = [item for item in applicants if item.status != ApplicantProfileStatus.COMPLETED.value]
        if incomplete:
            raise ValueError("Заполните анкеты всех заявителей перед отправкой заявки менеджеру.")
        if not visa_case.desired_country_code:
            raise ValueError("Сначала выберите страну подачи.")
        if visa_case.desired_country_code not in {CONSULTATION_COUNTRY_CODE, "OTHER"}:
            if not visa_case.preferred_submission_city or not visa_case.submission_provider:
                raise ValueError("Сначала выберите город подачи и визовый центр.")
        if not visa_case.travel_purpose:
            raise ValueError("Сначала выберите цель поездки.")

        visa_case.applicants_count = len(applicants)
        visa_case.submitted_at = now_iso()
        visa_case.updated_at = visa_case.submitted_at
        visa_case.status = (
            VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value
            if visa_case.desired_country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}
            else VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
        )
        self.save_case(visa_case)
        return visa_case, incomplete

    def list_submitted_cases(self, limit: int = 20) -> list[VisaCase]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM visa_cases
                WHERE status IN (?, ?, ?, ?)
                ORDER BY COALESCE(submitted_at, updated_at) DESC
                LIMIT ?
                """,
                (
                    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
                    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value,
                    VisaCaseStatus.MANAGER_REVIEWING.value,
                    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value,
                    limit,
                ),
            ).fetchall()
        return [self._case_from_row(row) for row in rows if row is not None]

    def create_slot_offer(
        self,
        case_id: str,
        created_by_admin_id: int,
        parsed_options: list[ParsedSlotOption],
        *,
        message: str | None = None,
        expires_at: str | None = None,
    ) -> tuple[AppointmentSlotOffer, list[AppointmentSlotOption], VisaCase]:
        visa_case = self.get_case_by_any_id(case_id)
        if visa_case is None:
            raise ValueError("Кейс не найден.")
        if visa_case.status not in SLOT_ELIGIBLE_CASE_STATUSES:
            raise ValueError("Для этого кейса пока нельзя отправлять варианты дат.")

        offer = AppointmentSlotOffer(
            id=str(uuid4()),
            case_id=case_id,
            created_by_admin_id=created_by_admin_id,
            status=AppointmentSlotOfferStatus.ACTIVE.value,
            message=message,
            expires_at=expires_at,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        options = [
            AppointmentSlotOption(
                id=str(uuid4()),
                offer_id=offer.id,
                case_id=case_id,
                option_date=item.option_date,
                option_time=item.option_time,
                city=item.city or visa_case.preferred_submission_city,
                provider=item.provider or visa_case.submission_provider,
                comment=item.comment,
                status=AppointmentSlotOptionStatus.AVAILABLE.value,
                created_at=now_iso(),
                updated_at=now_iso(),
            )
            for item in parsed_options
        ]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO appointment_slot_offers (id, case_id, created_by_admin_id, status, message, expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    offer.id,
                    offer.case_id,
                    offer.created_by_admin_id,
                    offer.status,
                    offer.message,
                    offer.expires_at,
                    offer.created_at,
                    offer.updated_at,
                ),
            )
            for option in options:
                connection.execute(
                    """
                    INSERT INTO appointment_slot_options (
                      id, offer_id, case_id, option_date, option_time, city, provider, address, comment, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        option.id,
                        option.offer_id,
                        option.case_id,
                        option.option_date,
                        option.option_time,
                        option.city,
                        option.provider,
                        option.address,
                        option.comment,
                        option.status,
                        option.created_at,
                        option.updated_at,
                    ),
                )
            connection.commit()
        visa_case.status = VisaCaseStatus.SLOT_OPTIONS_SENT.value
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        return offer, options, visa_case

    def list_slot_offers_for_case(self, case_id: str) -> list[tuple[AppointmentSlotOffer, list[AppointmentSlotOption]]]:
        with self._connect() as connection:
            offer_rows = connection.execute(
                "SELECT * FROM appointment_slot_offers WHERE case_id = ? ORDER BY created_at DESC",
                (case_id,),
            ).fetchall()
            grouped: list[tuple[AppointmentSlotOffer, list[AppointmentSlotOption]]] = []
            for row in offer_rows:
                option_rows = connection.execute(
                    "SELECT * FROM appointment_slot_options WHERE offer_id = ? ORDER BY option_date ASC, option_time ASC",
                    (row["id"],),
                ).fetchall()
                grouped.append((self._offer_from_row(row), [self._option_from_row(item) for item in option_rows]))
        return grouped

    def list_slot_offers_for_user(self, telegram_id: int) -> list[tuple[AppointmentSlotOffer, list[AppointmentSlotOption]]]:
        visa_case = self.get_case_for_telegram_user(telegram_id)
        if visa_case is None:
            return []
        return self.list_slot_offers_for_case(visa_case.id)

    def list_available_slot_options_for_user(self, telegram_id: int) -> list[AppointmentSlotOption]:
        available: list[AppointmentSlotOption] = []
        for _, options in self.list_slot_offers_for_user(telegram_id):
            for option in options:
                if option.status == AppointmentSlotOptionStatus.AVAILABLE.value:
                    available.append(option)
        return available

    def has_available_slot_options_for_user(self, telegram_id: int) -> bool:
        return bool(self.list_available_slot_options_for_user(telegram_id))

    def select_slot_option_for_user(self, telegram_id: int, option_id: str) -> tuple[VisaCase, AppointmentSlotOption]:
        visa_case = self.get_case_for_telegram_user(telegram_id)
        if visa_case is None:
            raise ValueError("Кейс не найден.")
        if visa_case.status in {VisaCaseStatus.APPOINTMENT_CONFIRMED.value, VisaCaseStatus.CANCELLED.value, VisaCaseStatus.CLOSED.value}:
            raise ValueError("Выбор даты для этого кейса уже недоступен.")
        with self._connect() as connection:
            option_row = connection.execute(
                "SELECT * FROM appointment_slot_options WHERE id = ? AND case_id = ?",
                (option_id, visa_case.id),
            ).fetchone()
            if option_row is None:
                raise ValueError("Вариант даты не найден.")
            option = self._option_from_row(option_row)
            offer_row = connection.execute(
                "SELECT * FROM appointment_slot_offers WHERE id = ?",
                (option.offer_id,),
            ).fetchone()
            if offer_row is None:
                raise ValueError("Предложение дат не найдено.")
            offer = self._offer_from_row(offer_row)
            if offer.expires_at and datetime.fromisoformat(offer.expires_at) < datetime.now(UTC):
                raise ValueError("Срок действия предложения истек.")
            if option.status != AppointmentSlotOptionStatus.AVAILABLE.value:
                raise ValueError("Этот вариант даты уже недоступен.")
            connection.execute(
                "UPDATE appointment_slot_options SET status = ?, updated_at = ? WHERE offer_id = ? AND id != ? AND status = ?",
                (
                    AppointmentSlotOptionStatus.UNAVAILABLE.value,
                    now_iso(),
                    option.offer_id,
                    option.id,
                    AppointmentSlotOptionStatus.AVAILABLE.value,
                ),
            )
            connection.execute(
                "UPDATE appointment_slot_options SET status = ?, updated_at = ? WHERE id = ?",
                (AppointmentSlotOptionStatus.SELECTED.value, now_iso(), option.id),
            )
            connection.execute(
                "UPDATE appointment_slot_offers SET status = ?, updated_at = ? WHERE id = ?",
                (AppointmentSlotOfferStatus.COMPLETED.value, now_iso(), offer.id),
            )
            connection.commit()

        visa_case.selected_slot_option_id = option.id
        visa_case.selected_appointment_date = option.option_date
        visa_case.selected_appointment_time = option.option_time
        visa_case.selected_appointment_city = option.city
        visa_case.selected_appointment_provider = option.provider
        visa_case.status = VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        return visa_case, self.get_slot_option(option.id)

    def get_slot_option(self, option_id: str) -> AppointmentSlotOption:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM appointment_slot_options WHERE id = ?", (option_id,)).fetchone()
        if row is None:
            raise ValueError("Вариант даты не найден.")
        return self._option_from_row(row)

    def confirm_appointment(self, case_id: str, admin_id: int) -> VisaCase:
        del admin_id
        visa_case = self.get_case_by_any_id(case_id)
        if visa_case is None:
            raise ValueError("Кейс не найден.")
        if not visa_case.selected_slot_option_id:
            raise ValueError("Клиент еще не выбрал дату.")
        visa_case.status = VisaCaseStatus.APPOINTMENT_CONFIRMED.value
        visa_case.appointment_confirmed_at = now_iso()
        visa_case.updated_at = visa_case.appointment_confirmed_at
        self.save_case(visa_case)
        return visa_case

    def refresh_case_status(self, telegram_id: int) -> VisaCase:
        visa_case = self.get_case_for_telegram_user(telegram_id)
        if visa_case is None:
            raise RuntimeError("Visa case is missing.")
        if visa_case.status in LOCKED_CASE_STATUSES:
            return visa_case
        applicants = self.list_applicants(telegram_id)
        visa_case.applicants_count = len(applicants)
        if not applicants:
            visa_case.status = VisaCaseStatus.PROFILES_IN_PROGRESS.value
        elif applicants and all(item.status == ApplicantProfileStatus.COMPLETED.value for item in applicants):
            if visa_case.desired_country_code:
                visa_case.status = (
                    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value
                    if visa_case.desired_country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}
                    else VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value
                )
            else:
                visa_case.status = VisaCaseStatus.PROFILES_COMPLETED.value
        else:
            visa_case.status = VisaCaseStatus.PROFILES_IN_PROGRESS.value
        visa_case.updated_at = now_iso()
        self.save_case(visa_case)
        return visa_case

    def _sync_applicant_slots(self, visa_case: VisaCase) -> None:
        existing = self.list_applicants(visa_case.telegram_id)
        existing_by_position = {item.position: item for item in existing}
        for position in range(1, visa_case.applicants_count + 1):
            if position in existing_by_position:
                continue
            profile = ApplicantProfile(
                id=str(uuid4()),
                user_id=visa_case.user_id,
                telegram_id=visa_case.telegram_id,
                case_id=visa_case.id,
                position=position,
                role="primary" if position == 1 else "group_member",
                status=ApplicantProfileStatus.DRAFT.value,
                completion_percent=0,
                created_at=now_iso(),
                updated_at=now_iso(),
            )
            self.save_applicant(profile)
        for item in existing:
            if item.position > visa_case.applicants_count:
                with self._connect() as connection:
                    connection.execute("DELETE FROM applicant_profiles WHERE id = ?", (item.id,))
                    connection.commit()

    def _case_from_row(self, row: sqlite3.Row | None) -> VisaCase | None:
        if row is None:
            return None
        return VisaCase(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            access_key_id=row["access_key_id"],
            access_key_code=row["access_key_code"],
            status=row["status"],
            applicants_count=row["applicants_count"],
            desired_country_code=row["desired_country_code"],
            desired_country_name_ru=row["desired_country_name_ru"],
            preferred_submission_city=row["preferred_submission_city"],
            submission_provider=row["submission_provider"],
            submission_provider_type=row["submission_provider_type"],
            submission_jurisdiction=row["submission_jurisdiction"],
            submission_verification_status=row["submission_verification_status"],
            travel_purpose=row["travel_purpose"],
            approximate_travel_start_date=row["approximate_travel_start_date"],
            approximate_travel_end_date=row["approximate_travel_end_date"],
            client_comment=row["client_comment"],
            submitted_at=row["submitted_at"],
            manager_reviewed_at=row["manager_reviewed_at"],
            selected_slot_option_id=row["selected_slot_option_id"],
            selected_appointment_date=row["selected_appointment_date"],
            selected_appointment_time=row["selected_appointment_time"],
            selected_appointment_city=row["selected_appointment_city"],
            selected_appointment_provider=row["selected_appointment_provider"],
            appointment_confirmed_at=row["appointment_confirmed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _applicant_from_row(self, row: sqlite3.Row | None) -> ApplicantProfile | None:
        if row is None:
            return None
        return ApplicantProfile(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            case_id=row["case_id"],
            position=row["position"],
            role=row["role"],
            status=row["status"],
            completion_percent=row["completion_percent"],
            last_name_latin=row["last_name_latin"],
            first_name_latin=row["first_name_latin"],
            last_name_cyrillic=row["last_name_cyrillic"],
            first_name_cyrillic=row["first_name_cyrillic"],
            patronymic=row["patronymic"],
            birth_date=row["birth_date"],
            birth_place=row["birth_place"],
            citizenship=row["citizenship"],
            gender=row["gender"],
            marital_status=row["marital_status"],
            phone=row["phone"],
            email=row["email"],
            residence_country=row["residence_country"],
            residence_city=row["residence_city"],
            residence_address=row["residence_address"],
            postal_code=row["postal_code"],
            passport_number=row["passport_number"],
            passport_issue_date=row["passport_issue_date"],
            passport_expiry_date=row["passport_expiry_date"],
            passport_issuing_authority=row["passport_issuing_authority"],
            passport_issuing_country=row["passport_issuing_country"],
            desired_country_code=row["desired_country_code"],
            desired_country_name_ru=row["desired_country_name_ru"],
            travel_purpose=row["travel_purpose"],
            approximate_travel_dates=row["approximate_travel_dates"],
            entries_count=row["entries_count"],
            preferred_submission_city=row["preferred_submission_city"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _offer_from_row(self, row: sqlite3.Row) -> AppointmentSlotOffer:
        return AppointmentSlotOffer(
            id=row["id"],
            case_id=row["case_id"],
            created_by_admin_id=row["created_by_admin_id"],
            status=row["status"],
            message=row["message"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _option_from_row(self, row: sqlite3.Row) -> AppointmentSlotOption:
        return AppointmentSlotOption(
            id=row["id"],
            offer_id=row["offer_id"],
            case_id=row["case_id"],
            option_date=row["option_date"],
            option_time=row["option_time"],
            city=row["city"],
            provider=row["provider"],
            address=row["address"],
            comment=row["comment"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
