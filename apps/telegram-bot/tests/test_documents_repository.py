from __future__ import annotations

from pathlib import Path

import pytest

from bot.database import init_db
from bot.models import (
    AgencyDocumentStatus,
    ClientDocumentStatus,
    DocumentCategory,
)
from bot.repositories.documents import DocumentRepository
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository


def build_repo(tmp_path: Path) -> tuple[DocumentRepository, str]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'documents-repo.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    access_keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    documents = DocumentRepository(database_url)
    user = users.upsert_from_telegram(7100, "docuser", "Doc", "User")
    key = new_access_key("DOC-KEY", 1, "miniapp", [], 2, None, None)
    access_keys.save(key)
    access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    return documents, case.id


def test_create_client_required_document_request(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)

    item = documents.create_client_request(
        case_id,
        DocumentCategory.INTERNATIONAL_PASSPORT.value,
        admin_id=1,
        comment="Загрузите разворот с фото.",
    )

    assert item.source_type == "client_required"
    assert item.status == ClientDocumentStatus.REQUESTED.value
    assert item.visible_to_client is True
    assert item.manager_comment == "Загрузите разворот с фото."


def test_create_agency_prepared_document_item(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)

    item = documents.create_agency_item(
        case_id,
        DocumentCategory.HOTEL_BOOKING.value,
        admin_id=1,
    )

    assert item.source_type == "agency_prepared"
    assert item.status == AgencyDocumentStatus.PREPARING_BY_AGENCY.value


def test_list_documents_by_case(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    documents.create_client_request(case_id, DocumentCategory.PHOTO.value, admin_id=1)
    documents.create_agency_item(case_id, DocumentCategory.INVITATION.value, admin_id=1)

    items = documents.list_by_case(case_id)

    assert len(items) == 2


def test_update_status_and_manager_comment(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    item = documents.create_client_request(case_id, DocumentCategory.PHOTO.value, admin_id=1)

    updated = documents.update_status(item.id, ClientDocumentStatus.APPROVED.value, admin_id=1)
    commented = documents.add_manager_comment(item.id, "Принято.", admin_id=1)

    assert updated.status == ClientDocumentStatus.APPROVED.value
    assert commented.manager_comment == "Принято."


def test_count_requested_uploaded_ready_documents(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    requested = documents.create_client_request(case_id, DocumentCategory.PHOTO.value, admin_id=1)
    documents.create_client_request(case_id, DocumentCategory.BANK_STATEMENT.value, admin_id=1)
    agency = documents.create_agency_item(case_id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
    documents.mark_uploaded_by_client(requested.id, "7100")
    documents.update_status(agency.id, AgencyDocumentStatus.READY_FOR_CLIENT.value, admin_id=1)

    counts = documents.count_summary(case_id)

    assert counts["client_pending"] == 1
    assert counts["client_uploaded"] == 1
    assert counts["agency_ready"] == 1


def test_invalid_status_for_source_type(tmp_path: Path) -> None:
    documents, case_id = build_repo(tmp_path)
    item = documents.create_client_request(case_id, DocumentCategory.PHOTO.value, admin_id=1)

    with pytest.raises(ValueError):
        documents.update_status(item.id, AgencyDocumentStatus.READY_FOR_CLIENT.value, admin_id=1)
