from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bot.models import VisaCaseStatus
from bot.services.manager_case_view import manager_case_status_label, render_queue_item

if TYPE_CHECKING:
    from bot.models import VisaCase

QUEUE_GROUP_LABELS: list[tuple[str, str]] = [
    ("new_review", "Новые на проверку"),
    ("needs_documents", "Нужны документы"),
    ("awaiting_client_docs", "Ожидаем документы клиента"),
    ("docs_under_review", "Документы на проверке"),
    ("slot_search", "Подбираем даты"),
    ("slots_sent", "Даты отправлены"),
    ("slot_selected", "Клиент выбрал дату"),
    ("appointment_confirmed", "Запись подтверждена"),
]

NEW_REVIEW_STATUSES = frozenset(
    {
        VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
        VisaCaseStatus.NEEDS_MANAGER_CONSULTATION.value,
        VisaCaseStatus.WAITING_MANAGER_REVIEW.value,
    }
)

NEEDS_DOCUMENTS_STATUSES = frozenset(
    {
        VisaCaseStatus.MANAGER_REVIEWING.value,
        VisaCaseStatus.NEEDS_CLARIFICATION.value,
    }
)

SLOT_SEARCH_STATUSES = frozenset({VisaCaseStatus.READY_FOR_SLOT_SEARCH.value})
SLOTS_SENT_STATUSES = frozenset({VisaCaseStatus.SLOT_OPTIONS_SENT.value})
SLOT_SELECTED_STATUSES = frozenset(
    {
        VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value,
        VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value,
    }
)
APPOINTMENT_CONFIRMED_STATUSES = frozenset({VisaCaseStatus.APPOINTMENT_CONFIRMED.value})

TERMINAL_STATUSES = frozenset(
    {
        VisaCaseStatus.CANCELLED.value,
        VisaCaseStatus.CLOSED.value,
    }
)

MANAGER_CASE_STATUSES: list[tuple[str, str]] = [
    (VisaCaseStatus.MANAGER_REVIEWING.value, "Менеджер проверяет данные"),
    (VisaCaseStatus.NEEDS_CLARIFICATION.value, "Требуются уточнения"),
    (VisaCaseStatus.READY_FOR_SLOT_SEARCH.value, "Менеджер подбирает даты"),
    (VisaCaseStatus.SLOT_OPTIONS_SENT.value, "Менеджер отправил варианты дат"),
    (VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value, "Дата выбрана клиентом"),
    (VisaCaseStatus.APPOINTMENT_CONFIRMATION_PENDING.value, "Запись подтверждается"),
    (VisaCaseStatus.APPOINTMENT_CONFIRMED.value, "Запись подтверждена"),
    (VisaCaseStatus.CANCELLED.value, "Заявка отменена"),
    (VisaCaseStatus.CLOSED.value, "Заявка закрыта"),
]

CASE_MESSAGE_TEMPLATES: list[tuple[str, str]] = [
    ("reviewing", "Проверяем заявку"),
    ("clarify", "Нужны уточнения"),
    ("docs_requested", "Запросили документы"),
    ("awaiting_docs", "Ожидаем документы"),
    ("docs_received", "Документы получены"),
    ("slot_search", "Подбираем даты"),
    ("slots_sent", "Даты отправлены"),
    ("slot_selected", "Дата выбрана"),
    ("appointment_confirmed", "Запись подтверждена"),
    ("contact_manager", "Свяжитесь с менеджером"),
]

CASE_TEMPLATE_TEXTS: dict[str, str] = {
    "reviewing": "Менеджер проверяет вашу заявку.",
    "clarify": "По вашей заявке нужны уточнения. Пожалуйста, свяжитесь с менеджером.",
    "docs_requested": "Мы запросили документы по вашей заявке. Проверьте список в личном кабинете.",
    "awaiting_docs": "Ожидаем документы от вас. Загрузите их в личном кабинете.",
    "docs_received": "Документы получены. Менеджер проверяет их.",
    "slot_search": "Менеджер подбирает даты для записи.",
    "slots_sent": "Менеджер отправил варианты дат. Выберите подходящий в личном кабинете.",
    "slot_selected": "Вы выбрали дату. Менеджер подтвердит запись отдельно.",
    "appointment_confirmed": "Запись подтверждена. Менеджер направит детали отдельно.",
    "contact_manager": "Пожалуйста, свяжитесь с менеджером для уточнения деталей.",
}

QUEUE_SEARCH_HINT = "Используйте 🔎 Найти заявку по ID или номеру."
MAX_MANAGER_QUEUE_ITEMS = 10
QUEUE_ITEMS_LIMIT_MESSAGE = "Показаны первые 10 кейсов. Для поиска используйте 🔎 Найти заявку."

RAW_CASE_STATUS_CODES = frozenset(
    {
        VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
        VisaCaseStatus.MANAGER_REVIEWING.value,
        VisaCaseStatus.SLOT_OPTIONS_SENT.value,
        VisaCaseStatus.APPOINTMENT_CONFIRMED.value,
        VisaCaseStatus.READY_FOR_SLOT_SEARCH.value,
        VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value,
    }
)


@dataclass(slots=True)
class ManagerCaseQueueItem:
    visa_case: VisaCase
    username: str | None
    client_pending: int = 0
    client_under_review: int = 0


@dataclass(slots=True)
class ManagerQueueGroup:
    key: str
    label: str
    items: list[ManagerCaseQueueItem]
    truncated: bool = False


@dataclass(slots=True)
class ManagerQueueView:
    summary_text: str
    actionable_items: list[ManagerCaseQueueItem]
    has_more_items: bool


def is_terminal_case_status(status: str) -> bool:
    return status in TERMINAL_STATUSES


def get_case_template_text(template_code: str, public_number: str | None = None) -> str:
    text = CASE_TEMPLATE_TEXTS.get(template_code, "Менеджер обновил статус по вашей заявке.")
    if public_number:
        return f"По заявке {public_number}: {text}"
    return text


def validate_status_transition(
    visa_case: VisaCase,
    new_status: str,
    *,
    has_slot_options: bool,
    has_selected_slot: bool,
) -> str | None:
    if new_status == VisaCaseStatus.APPOINTMENT_CONFIRMED.value and not has_selected_slot:
        return "Нельзя подтвердить запись без выбранной даты клиентом."
    if new_status == VisaCaseStatus.SLOT_OPTIONS_SENT.value and not has_slot_options:
        return "Нельзя установить статус «даты отправлены» без вариантов дат."
    if new_status in SLOT_SELECTED_STATUSES and not has_selected_slot:
        return "Нельзя установить статус выбранной даты без выбранного слота."
    if visa_case.status in TERMINAL_STATUSES and new_status not in TERMINAL_STATUSES:
        return "Нельзя изменить статус закрытой или отмененной заявки."
    return None


def get_allowed_statuses_for_case(
    visa_case: VisaCase,
    *,
    has_slot_options: bool,
    has_selected_slot: bool,
) -> list[tuple[str, str]]:
    allowed: list[tuple[str, str]] = []
    for status, label in MANAGER_CASE_STATUSES:
        if validate_status_transition(
            visa_case,
            status,
            has_slot_options=has_slot_options,
            has_selected_slot=has_selected_slot,
        ):
            continue
        allowed.append((status, label))
    return allowed


def _matches_group(item: ManagerCaseQueueItem, group_key: str) -> bool:
    case = item.visa_case
    status = case.status
    if status in TERMINAL_STATUSES:
        return False
    if group_key == "new_review":
        return status in NEW_REVIEW_STATUSES
    if group_key == "needs_documents":
        return status in NEEDS_DOCUMENTS_STATUSES
    if group_key == "awaiting_client_docs":
        return item.client_pending > 0
    if group_key == "docs_under_review":
        return item.client_under_review > 0
    if group_key == "slot_search":
        return status in SLOT_SEARCH_STATUSES
    if group_key == "slots_sent":
        return status in SLOTS_SENT_STATUSES
    if group_key == "slot_selected":
        return status in SLOT_SELECTED_STATUSES
    if group_key == "appointment_confirmed":
        return status in APPOINTMENT_CONFIRMED_STATUSES
    return False


def build_manager_queue_groups(items: list[ManagerCaseQueueItem]) -> list[ManagerQueueGroup]:
    groups: list[ManagerQueueGroup] = []
    for key, label in QUEUE_GROUP_LABELS:
        matched = [item for item in items if _matches_group(item, key)]
        groups.append(
            ManagerQueueGroup(
                key=key,
                label=label,
                items=matched,
            )
        )
    return groups


def _queue_item_sort_key(item: ManagerCaseQueueItem) -> str:
    case = item.visa_case
    return case.submitted_at or case.updated_at or case.created_at


def select_actionable_queue_items(
    items: list[ManagerCaseQueueItem],
    *,
    limit: int = MAX_MANAGER_QUEUE_ITEMS,
) -> tuple[list[ManagerCaseQueueItem], bool]:
    unique: dict[str, ManagerCaseQueueItem] = {}
    for item in sorted(items, key=_queue_item_sort_key, reverse=True):
        unique.setdefault(item.visa_case.id, item)
    ordered = list(unique.values())
    return ordered[:limit], len(ordered) > limit


def render_manager_queue(groups: list[ManagerQueueGroup]) -> str:
    blocks: list[str] = []
    has_items = False
    for group in groups:
        if not group.items:
            continue
        has_items = True
        header = f"▸ {group.label} ({len(group.items)})"
        blocks.append(header)
        for item in group.items:
            blocks.append(render_queue_item(item.visa_case))
    if not has_items:
        return "В очереди нет активных Mini App кейсов."
    return "\n\n".join(blocks)


def build_manager_queue_view(items: list[ManagerCaseQueueItem]) -> ManagerQueueView:
    groups = build_manager_queue_groups(items)
    summary_text = render_manager_queue(groups)
    actionable_items, has_more_items = select_actionable_queue_items(items)
    if has_more_items:
        summary_text = f"{summary_text}\n\n{QUEUE_ITEMS_LIMIT_MESSAGE}"
    return ManagerQueueView(
        summary_text=summary_text,
        actionable_items=actionable_items,
        has_more_items=has_more_items,
    )


def queue_text_contains_raw_status(text: str) -> bool:
    lowered = text.lower()
    return any(status in lowered for status in RAW_CASE_STATUS_CODES)
