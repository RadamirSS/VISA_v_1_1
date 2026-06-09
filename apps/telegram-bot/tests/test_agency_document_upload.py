from __future__ import annotations

from pathlib import Path

import pytest

from bot.models import AgencyDocumentStatus, DocumentCategory
from bot.repositories.documents import DocumentRepository
from bot.services.document_status import should_notify_client_for_agency_status
from bot.services.document_storage import DocumentStorageService
from bot.services.notifications import (
    build_agency_document_ready_message,
    build_agency_document_transferred_separately_message,
)
from tests.test_documents_repository import build_repo


def test_manager_agency_upload_saves_file_metadata(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    agency = documents.create_agency_item(case_id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
    storage = DocumentStorageService(
        repository=documents,
        storage_dir=tmp_path / "storage" / "documents",
        max_file_mb=15,
        enabled=False,
    )

    storage.save_manager_agency_upload(
        case_id=case_id,
        document_item_id=agency.id,
        uploaded_by="admin:99",
        filename="hotel.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.4 agency",
    )
    updated = documents.mark_agency_ready_after_upload(agency.id, admin_id=99)

    active = documents.get_latest_active_file(agency.id)
    assert active is not None
    assert active.mime_type == "application/pdf"
    assert Path(active.storage_path).exists()
    assert updated.status == AgencyDocumentStatus.READY_FOR_CLIENT.value


def test_agency_document_without_file_cannot_become_ready(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    agency = documents.create_agency_item(case_id, DocumentCategory.INVITATION.value, admin_id=1)

    with pytest.raises(ValueError):
        documents.mark_agency_ready_after_upload(agency.id, admin_id=1)


def test_ready_notification_not_sent_without_file() -> None:
    assert should_notify_client_for_agency_status(AgencyDocumentStatus.READY_FOR_CLIENT.value, has_file=False) is False
    assert should_notify_client_for_agency_status(AgencyDocumentStatus.SHARED_WITH_CLIENT.value, has_file=False) is False


def test_transferred_separately_notification_allowed_without_file() -> None:
    assert should_notify_client_for_agency_status(
        AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value,
        has_file=False,
    )


def test_notification_messages_do_not_include_sensitive_links() -> None:
    ready = build_agency_document_ready_message("Бронь отеля")
    separate = build_agency_document_transferred_separately_message("Бронь отеля")

    for text in (ready, separate):
        assert "http://" not in text
        assert "https://" not in text
        assert "passport" not in text.lower()


def test_env_example_contains_document_upload_variables() -> None:
    env_example = Path(__file__).resolve().parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "DOCUMENT_UPLOADS_ENABLED=false" in content
    assert "DOCUMENT_STORAGE_DIR=./storage/documents" in content
    assert "DOCUMENT_MAX_FILE_MB=15" in content
    assert "secure object storage" in content
