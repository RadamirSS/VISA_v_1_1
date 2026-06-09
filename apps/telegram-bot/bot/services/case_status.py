from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bot.models import VisaCaseStatus

if TYPE_CHECKING:
    from bot.models import VisaCase

UNKNOWN_STATUS_LABEL = "Статус уточняется"

STATUS_LABELS: dict[str, str] = {
    VisaCaseStatus.ACCESS_ACTIVATED.value: "Ключ доступа активирован",
    VisaCaseStatus.DRAFT.value: "Анкеты заполняются",
    VisaCaseStatus.PROFILES_NOT_STARTED.value: "Заполните анкеты заявителей",
    VisaCaseStatus.PROFILES_IN_PROGRESS.value: "Анкеты заполняются",
    VisaCaseStatus.PROFILES_COMPLETED.value: "Анкеты заявителей заполнены",
    VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value: "Выберите страну и город подачи",
    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value: "Заявка отправлена менеджеру",
    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value: "Нужна консультация менеджера",
    VisaCaseStatus.WAITING_MANAGER_REVIEW.value: "Заявка отправлена менеджеру",
    VisaCaseStatus.NEEDS_CLARIFICATION.value: "Требуются уточнения",
    VisaCaseStatus.MANAGER_REVIEWING.value: "Менеджер проверяет данные",
    VisaCaseStatus.READY_FOR_CITY_SELECTION.value: "Выберите страну и город подачи",
    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value: "Менеджер подбирает даты",
    VisaCaseStatus.SLOT_OPTIONS_SENT.value: "Менеджер отправил варианты дат",
    VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value: "Дата выбрана клиентом",
    VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value: "Запись подтверждается",
    VisaCaseStatus.APPOINTMENT_CONFIRMED.value: "Запись подтверждена",
    VisaCaseStatus.CANCELLED.value: "Заявка отменена",
    VisaCaseStatus.CLOSED.value: "Заявка закрыта",
}

ACCESS_ACTIVE_LABEL = "Доступ активирован"
ACCESS_INACTIVE_LABEL = "Введите ключ доступа"

TIMELINE_STEPS: list[tuple[str, str]] = [
    ("access", "Ключ доступа активирован"),
    ("profiles", "Анкеты заявителей заполнены"),
    ("city", "Страна и город подачи выбраны"),
    ("submitted", "Заявка отправлена менеджеру"),
    ("review", "Менеджер проверяет данные"),
    ("slot_search", "Менеджер подбирает даты"),
    ("slot_options", "Даты отправлены клиенту"),
    ("slot_selected", "Дата выбрана клиентом"),
    ("confirmation", "Запись подтверждается"),
    ("confirmed", "Запись подтверждена"),
]

STATUS_STEP_INDEX: dict[str, int] = {
    VisaCaseStatus.ACCESS_ACTIVATED.value: 0,
    VisaCaseStatus.DRAFT.value: 1,
    VisaCaseStatus.PROFILES_NOT_STARTED.value: 1,
    VisaCaseStatus.PROFILES_IN_PROGRESS.value: 1,
    VisaCaseStatus.PROFILES_COMPLETED.value: 2,
    VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value: 2,
    VisaCaseStatus.READY_FOR_CITY_SELECTION.value: 2,
    VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value: 3,
    VisaCaseStatus.WAITING_MANAGER_REVIEW.value: 3,
    VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value: 3,
    VisaCaseStatus.NEEDS_CLARIFICATION.value: 3,
    VisaCaseStatus.MANAGER_REVIEWING.value: 4,
    VisaCaseStatus.READY_FOR_SLOT_SEARCH.value: 5,
    VisaCaseStatus.SLOT_OPTIONS_SENT.value: 6,
    VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value: 7,
    VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value: 8,
    VisaCaseStatus.APPOINTMENT_CONFIRMED.value: 9,
    VisaCaseStatus.CLOSED.value: 9,
    VisaCaseStatus.CANCELLED.value: -1,
}


def case_status_label(status: str) -> str:
    return STATUS_LABELS.get(status, UNKNOWN_STATUS_LABEL)


def access_status_label(active: bool) -> str:
    return ACCESS_ACTIVE_LABEL if active else ACCESS_INACTIVE_LABEL


def case_next_action(
    status: str,
    *,
    has_applicants: bool = False,
    has_slot_options: bool = False,
    has_selected_slot: bool = False,
) -> dict[str, str]:
    del has_applicants, has_slot_options, has_selected_slot

    if status == "no_access":
        return {
            "type": "enter_access_key",
            "label": "Вернитесь в бот и введите ключ доступа",
            "href": "/",
        }
    if status == "no_case":
        return {
            "type": "create_case",
            "label": "Создайте заявку",
            "href": "/case/new",
        }

    actions: dict[str, dict[str, str]] = {
        VisaCaseStatus.PROFILES_NOT_STARTED.value: {
            "type": "fill_profiles",
            "label": "Заполните анкеты заявителей",
            "href": "/applicants",
        },
        VisaCaseStatus.PROFILES_IN_PROGRESS.value: {
            "type": "fill_profiles",
            "label": "Продолжите заполнение анкет",
            "href": "/applicants",
        },
        VisaCaseStatus.DRAFT.value: {
            "type": "fill_profiles",
            "label": "Продолжите заполнение анкет",
            "href": "/applicants",
        },
        VisaCaseStatus.PROFILES_COMPLETED.value: {
            "type": "select_city",
            "label": "Выберите страну и город подачи",
            "href": "/case",
        },
        VisaCaseStatus.CITY_SELECTION_IN_PROGRESS.value: {
            "type": "select_city",
            "label": "Выберите страну и город подачи",
            "href": "/case",
        },
        VisaCaseStatus.READY_FOR_CITY_SELECTION.value: {
            "type": "select_city",
            "label": "Выберите страну и город подачи",
            "href": "/case",
        },
        VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value: {
            "type": "wait_manager",
            "label": "Ожидайте проверки менеджера",
            "href": "/status",
        },
        VisaCaseStatus.WAITING_MANAGER_REVIEW.value: {
            "type": "wait_manager",
            "label": "Ожидайте проверки менеджера",
            "href": "/status",
        },
        VisaCaseStatus.MANAGER_REVIEWING.value: {
            "type": "wait_manager",
            "label": "Менеджер проверяет данные",
            "href": "/status",
        },
        VisaCaseStatus.READY_FOR_SLOT_SEARCH.value: {
            "type": "wait_manager",
            "label": "Менеджер подбирает даты",
            "href": "/status",
        },
        VisaCaseStatus.SLOT_OPTIONS_SENT.value: {
            "type": "select_slot",
            "label": "Выберите удобную дату",
            "href": "/appointment",
        },
        VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value: {
            "type": "wait_confirmation",
            "label": "Ожидайте подтверждения менеджера",
            "href": "/status",
        },
        VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value: {
            "type": "wait_confirmation",
            "label": "Ожидайте подтверждения менеджера",
            "href": "/status",
        },
        VisaCaseStatus.APPOINTMENT_CONFIRMED.value: {
            "type": "view_appointment",
            "label": "Запись подтверждена",
            "href": "/appointment",
        },
        VisaCaseStatus.NEEDS_CLARIFICATION.value: {
            "type": "contact_manager",
            "label": "Свяжитесь с менеджером",
            "href": "/status",
        },
        VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value: {
            "type": "contact_manager",
            "label": "Свяжитесь с менеджером",
            "href": "/status",
        },
        VisaCaseStatus.CANCELLED.value: {
            "type": "terminal",
            "label": "Заявка отменена",
            "href": "/status",
        },
        VisaCaseStatus.CLOSED.value: {
            "type": "terminal",
            "label": "Заявка закрыта",
            "href": "/status",
        },
        VisaCaseStatus.ACCESS_ACTIVATED.value: {
            "type": "create_case",
            "label": "Создайте заявку",
            "href": "/case/new",
        },
    }
    return actions.get(
        status,
        {
            "type": "wait_manager",
            "label": case_status_label(status),
            "href": "/status",
        },
    )


def _timeline_current_index(status: str, access_active: bool, applicants_completed: bool) -> int:
    if status == "no_case":
        return 0 if not access_active else 1
    if status == VisaCaseStatus.CANCELLED.value:
        if applicants_completed:
            return 3
        if access_active:
            return 1
        return 0
    current_index = STATUS_STEP_INDEX.get(status, 1)
    if not access_active and current_index > 0:
        return 0
    return current_index


def build_case_timeline(status: str, access_active: bool, applicants_completed: bool) -> list[dict[str, str]]:
    is_cancelled = status == VisaCaseStatus.CANCELLED.value
    current_index = _timeline_current_index(status, access_active, applicants_completed)

    steps: list[dict[str, str]] = []
    for index, (key, label) in enumerate(TIMELINE_STEPS):
        if is_cancelled:
            if index < current_index:
                state = "done"
            elif index == current_index:
                state = "warning"
            else:
                state = "locked"
        elif index < current_index:
            state = "done"
        elif index == current_index:
            state = "current"
        else:
            state = "locked"

        if not is_cancelled and key == "access" and access_active and current_index > 0 and index == 0:
            state = "done"

        steps.append({"key": key, "label": label, "state": state})

    return steps


def format_case_public_number(visa_case: VisaCase) -> str:
    year = visa_case.created_at[:4] if visa_case.created_at else "0000"
    suffix = int(hashlib.md5(visa_case.id.encode()).hexdigest()[:6], 16) % 1_000_000
    return f"VISA-CASE-{year}-{suffix:06d}"
