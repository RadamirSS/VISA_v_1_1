from __future__ import annotations

from typing import TYPE_CHECKING

from bot.models import ApplicantProfileStatus, VisaCaseStatus
from bot.services.case_status import case_next_action, case_status_label, format_case_public_number
from bot.services.trust_display import format_provider_display_name

if TYPE_CHECKING:
    from bot.models import ApplicantProfile, VisaCase

SENSITIVE_SUBSTRINGS = (
    "passport_number",
    "birth_place",
    "residence_address",
    "storage_path",
    "passport.pdf",
    "123456789",
)

APPLICANT_STATUS_LABELS: dict[str, str] = {
    ApplicantProfileStatus.DRAFT.value: "черновик",
    ApplicantProfileStatus.INCOMPLETE.value: "заполняется",
    ApplicantProfileStatus.COMPLETED.value: "заполнено",
    ApplicantProfileStatus.NEEDS_REVIEW.value: "на проверке",
    ApplicantProfileStatus.APPROVED_BY_MANAGER.value: "одобрено",
}

ROLE_LABELS: dict[str, str] = {
    "primary": "Основной заявитель",
    "group_member": "Заявитель",
    "child": "Ребенок",
    "spouse": "Супруг(а)",
}


def manager_case_status_label(status: str) -> str:
    return case_status_label(status)


def format_safe_client_line(telegram_id: int, username: str | None) -> str:
    if username:
        return f"@{username} / {telegram_id}"
    return str(telegram_id)


def format_applicant_display_name(profile: ApplicantProfile) -> str:
    parts = [
        profile.last_name_cyrillic,
        profile.first_name_cyrillic,
    ]
    name = " ".join(part.strip() for part in parts if part and part.strip())
    if name:
        return name
    parts = [
        profile.last_name_latin,
        profile.first_name_latin,
    ]
    name = " ".join(part.strip() for part in parts if part and part.strip())
    if name:
        return name
    if profile.role:
        return ROLE_LABELS.get(profile.role, profile.role)
    return f"Заявитель {profile.position}"


def applicant_status_label(status: str) -> str:
    return APPLICANT_STATUS_LABELS.get(status, status)


def render_appointment_state(visa_case: VisaCase) -> str:
    if visa_case.appointment_confirmed_at or visa_case.status == VisaCaseStatus.APPOINTMENT_CONFIRMED.value:
        return "подтверждена"
    if visa_case.selected_slot_option_id or visa_case.selected_appointment_date:
        if visa_case.status == VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value:
            return "дата выбрана, ожидает подтверждения"
        return "дата выбрана"
    if visa_case.status == VisaCaseStatus.SLOT_OPTIONS_SENT.value:
        return "даты отправлены"
    if visa_case.status == VisaCaseStatus.READY_FOR_SLOT_SEARCH.value:
        return "подбираем даты"
    return "не назначена"


def render_document_summary_for_manager(counts: dict[str, int | bool]) -> str:
    if not counts.get("has_items"):
        return "документы не запрошены"
    client_pending = int(counts.get("client_pending", 0))
    client_under_review = int(counts.get("client_under_review", 0))
    agency_in_progress = int(counts.get("agency_in_progress", 0))
    agency_ready = int(counts.get("agency_ready", 0))
    client_line = f"{client_pending} ожидают / {client_under_review} на проверке"
    agency_line = f"{agency_in_progress} в работе / {agency_ready} готов"
    return f"Документы от клиента: {client_line}\nДокументы агентства: {agency_line}"


def render_applicants_summary(applicants: list[ApplicantProfile]) -> str:
    if not applicants:
        return "Заявители: 0"
    lines = [f"Заявители: {len(applicants)}"]
    for index, profile in enumerate(applicants, start=1):
        name = format_applicant_display_name(profile)
        status = applicant_status_label(profile.status)
        lines.append(f"{index}. {name} — {profile.completion_percent}% · {status}")
    return "\n".join(lines)


def render_manager_case_summary(
    visa_case: VisaCase,
    *,
    username: str | None = None,
    applicants: list[ApplicantProfile] | None = None,
    doc_counts: dict[str, int | bool] | None = None,
) -> str:
    applicants = applicants or []
    doc_counts = doc_counts or {}
    public_number = format_case_public_number(visa_case)
    completed = sum(1 for item in applicants if item.status == ApplicantProfileStatus.COMPLETED.value)
    applicant_count = len(applicants) or visa_case.applicants_count
    doc_summary = render_document_summary_for_manager(doc_counts) if doc_counts else "документы не запрошены"
    pending_uploads = int(doc_counts.get("client_pending", 0)) if doc_counts else 0
    next_action = case_next_action(
        visa_case.status,
        has_applicants=bool(applicants),
        has_city_selected=bool(visa_case.preferred_submission_city),
        pending_document_uploads=pending_uploads,
    )
    provider = format_provider_display_name(visa_case.submission_provider) or "не выбран"
    return (
        f"Кейс: {public_number}\n"
        f"ID: {visa_case.id}\n"
        f"Клиент: {format_safe_client_line(visa_case.telegram_id, username)}\n"
        f"Страна: {visa_case.desired_country_name_ru or 'не выбрана'}\n"
        f"Город подачи: {visa_case.preferred_submission_city or 'не выбран'}\n"
        f"Визовый центр: {provider}\n"
        f"Цель: {visa_case.travel_purpose or 'уточнить'}\n"
        f"Заявителей: {applicant_count}\n"
        f"Анкеты: {completed}/{applicant_count} заполнено\n"
        f"{doc_summary}\n"
        f"Запись: {render_appointment_state(visa_case)}\n"
        f"Статус: {manager_case_status_label(visa_case.status)}\n"
        f"Следующее действие: {next_action['label']}"
    )


def render_queue_item(visa_case: VisaCase) -> str:
    public_number = format_case_public_number(visa_case)
    country = visa_case.desired_country_name_ru or "Консультация"
    city = visa_case.preferred_submission_city or "уточнить"
    applicants = visa_case.applicants_count
    status = manager_case_status_label(visa_case.status)
    return (
        f"{public_number}\n"
        f"{country} / {city}\n"
        f"Заявителей: {applicants}\n"
        f"Статус: {status}"
    )
