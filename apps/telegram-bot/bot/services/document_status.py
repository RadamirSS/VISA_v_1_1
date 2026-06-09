from __future__ import annotations

from typing import TYPE_CHECKING

from bot.models import (
    AgencyDocumentStatus,
    ClientDocumentStatus,
    DocumentSourceType,
)

if TYPE_CHECKING:
    from bot.models import DocumentItem

CLIENT_STATUS_LABELS: dict[str, str] = {
    ClientDocumentStatus.REQUESTED.value: "Ожидаем от вас",
    ClientDocumentStatus.UPLOADED_BY_CLIENT.value: "Загружено, менеджер проверяет",
    ClientDocumentStatus.RECEIVED_BY_MANAGER.value: "Загружено, менеджер проверяет",
    ClientDocumentStatus.APPROVED.value: "Принято",
    ClientDocumentStatus.REJECTED.value: "Нужно заменить",
    ClientDocumentStatus.NOT_NEEDED.value: "Не требуется",
}

AGENCY_STATUS_LABELS: dict[str, str] = {
    AgencyDocumentStatus.PLANNED.value: "Запланировано",
    AgencyDocumentStatus.PREPARING_BY_AGENCY.value: "Готовит агентство",
    AgencyDocumentStatus.READY_FOR_CLIENT.value: "Готово",
    AgencyDocumentStatus.SHARED_WITH_CLIENT.value: "Передано клиенту",
    AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value: "Документ будет передан менеджером отдельно.",
    AgencyDocumentStatus.NOT_NEEDED.value: "Не требуется",
}

AGENCY_READY_STATUSES = frozenset(
    {
        AgencyDocumentStatus.READY_FOR_CLIENT.value,
        AgencyDocumentStatus.SHARED_WITH_CLIENT.value,
    }
)

AGENCY_READY_GUARD_MESSAGE = (
    "Сначала загрузите файл агентства или оставьте комментарий, что документ будет передан отдельно."
)

CLIENT_STATUSES = frozenset(status.value for status in ClientDocumentStatus)
AGENCY_STATUSES = frozenset(status.value for status in AgencyDocumentStatus)


def document_status_label(item: DocumentItem, *, has_file: bool = False) -> str:
    if item.source_type == DocumentSourceType.CLIENT_REQUIRED.value:
        return CLIENT_STATUS_LABELS.get(item.status, "Статус уточняется")

    if item.status == AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value:
        return AGENCY_STATUS_LABELS[item.status]
    if item.status in AGENCY_READY_STATUSES and not has_file:
        return AGENCY_STATUS_LABELS[AgencyDocumentStatus.PREPARING_BY_AGENCY.value]
    return AGENCY_STATUS_LABELS.get(item.status, "Статус уточняется")


def is_transferred_separately(item: DocumentItem) -> bool:
    return (
        item.source_type == DocumentSourceType.AGENCY_PREPARED.value
        and item.status == AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value
    )


def can_client_upload(item: DocumentItem) -> bool:
    if item.source_type != DocumentSourceType.CLIENT_REQUIRED.value:
        return False
    return item.status in {
        ClientDocumentStatus.REQUESTED.value,
        ClientDocumentStatus.REJECTED.value,
    }


def can_client_download(item: DocumentItem, *, has_file: bool) -> bool:
    if item.source_type != DocumentSourceType.AGENCY_PREPARED.value or not has_file:
        return False
    return item.status in AGENCY_READY_STATUSES


def validate_status_for_source(source_type: str, status: str) -> None:
    allowed = CLIENT_STATUSES if source_type == DocumentSourceType.CLIENT_REQUIRED.value else AGENCY_STATUSES
    if status not in allowed:
        raise ValueError(f"Status {status} is not valid for source_type {source_type}")


def validate_agency_ready_status(*, status: str, has_file: bool) -> None:
    if status not in AGENCY_READY_STATUSES:
        return
    if not has_file:
        raise ValueError(AGENCY_READY_GUARD_MESSAGE)


def should_notify_client_for_agency_status(status: str, *, has_file: bool) -> bool:
    if status == AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value:
        return True
    if status in AGENCY_READY_STATUSES:
        return has_file
    return False


def build_document_summary_counts(items: list[DocumentItem]) -> dict[str, int | bool]:
    client_pending = 0
    client_under_review = 0
    client_uploaded = 0
    agency_in_progress = 0
    agency_ready = 0
    agency_shared = 0

    for item in items:
        if not item.visible_to_client:
            continue
        if item.source_type == DocumentSourceType.CLIENT_REQUIRED.value:
            if item.status == ClientDocumentStatus.REQUESTED.value:
                client_pending += 1
            elif item.status in {
                ClientDocumentStatus.UPLOADED_BY_CLIENT.value,
                ClientDocumentStatus.RECEIVED_BY_MANAGER.value,
            }:
                client_under_review += 1
                client_uploaded += 1
        elif item.source_type == DocumentSourceType.AGENCY_PREPARED.value:
            if item.status in {
                AgencyDocumentStatus.PLANNED.value,
                AgencyDocumentStatus.PREPARING_BY_AGENCY.value,
            }:
                agency_in_progress += 1
            elif item.status == AgencyDocumentStatus.READY_FOR_CLIENT.value:
                agency_ready += 1
            elif item.status == AgencyDocumentStatus.SHARED_WITH_CLIENT.value:
                agency_shared += 1
            elif item.status == AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value:
                agency_in_progress += 1

    visible_items = [item for item in items if item.visible_to_client]
    return {
        "has_items": bool(visible_items),
        "client_pending": client_pending,
        "client_under_review": client_under_review,
        "client_uploaded": client_uploaded,
        "agency_in_progress": agency_in_progress,
        "agency_ready": agency_ready,
        "agency_shared": agency_shared,
    }


def get_manager_queue_document_counts(counts: dict[str, int | bool]) -> tuple[int, int]:
    client_pending = int(counts.get("client_pending", 0))
    client_under_review = int(counts.get("client_under_review", 0))
    if client_under_review == 0:
        client_under_review = int(counts.get("client_uploaded", 0))
    return client_pending, client_under_review
