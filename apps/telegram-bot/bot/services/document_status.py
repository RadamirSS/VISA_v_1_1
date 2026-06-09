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
    AgencyDocumentStatus.NOT_NEEDED.value: "Не требуется",
}

CLIENT_STATUSES = frozenset(status.value for status in ClientDocumentStatus)
AGENCY_STATUSES = frozenset(status.value for status in AgencyDocumentStatus)


def document_status_label(item: DocumentItem) -> str:
    if item.source_type == DocumentSourceType.CLIENT_REQUIRED.value:
        return CLIENT_STATUS_LABELS.get(item.status, item.status)
    return AGENCY_STATUS_LABELS.get(item.status, item.status)


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
    return item.status in {
        AgencyDocumentStatus.READY_FOR_CLIENT.value,
        AgencyDocumentStatus.SHARED_WITH_CLIENT.value,
    }


def validate_status_for_source(source_type: str, status: str) -> None:
    allowed = CLIENT_STATUSES if source_type == DocumentSourceType.CLIENT_REQUIRED.value else AGENCY_STATUSES
    if status not in allowed:
        raise ValueError(f"Status {status} is not valid for source_type {source_type}")


def build_document_summary_counts(items: list[DocumentItem]) -> dict[str, int | bool]:
    client_pending = 0
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

    visible_items = [item for item in items if item.visible_to_client]
    return {
        "has_items": bool(visible_items),
        "client_pending": client_pending,
        "client_uploaded": client_uploaded,
        "agency_in_progress": agency_in_progress,
        "agency_ready": agency_ready,
        "agency_shared": agency_shared,
    }
