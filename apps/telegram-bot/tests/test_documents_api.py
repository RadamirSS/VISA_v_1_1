from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.models import AgencyDocumentStatus, DocumentCategory
from bot.repositories.access_keys import new_access_key
from tests.conftest import build_api_container


def build_client(tmp_path: Path, *, uploads_enabled: bool = False) -> tuple[TestClient, str, str]:
    container = build_api_container(
        tmp_path,
        database_name="documents-api.db",
        uploads_enabled=uploads_enabled,
    )
    user = container.users.upsert_from_telegram(9200, "docsapi", "Docs", "Api")
    key = new_access_key("DOCS-API", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = container.miniapp.create_case(user, key.id, key.code)
    item = container.documents.create_client_request(
        case.id,
        DocumentCategory.INTERNATIONAL_PASSPORT.value,
        admin_id=1,
    )
    return TestClient(api_main.app), str(user.telegram_id), item.id


def test_user_sees_own_case_documents(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)

    response = client.get("/api/case/current/documents", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Загранпаспорт"


def test_user_cannot_access_another_users_documents(tmp_path: Path) -> None:
    client, _, _ = build_client(tmp_path)

    response = client.get("/api/case/current/documents", headers={"X-Dev-Telegram-Id": "9201"})

    assert response.status_code in {403, 404}


def test_document_summary_returns_counts_only(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)

    response = client.get("/api/case/current/documents/summary", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_pending"] == 1
    assert "storage_path" not in payload
    assert "original_filename" not in payload


def test_upload_endpoint_rejects_when_disabled(tmp_path: Path) -> None:
    client, telegram_id, document_id = build_client(tmp_path, uploads_enabled=False)

    response = client.post(
        f"/api/case/current/documents/{document_id}/upload",
        headers={"X-Dev-Telegram-Id": telegram_id},
        files={"file": ("passport.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 501


def test_upload_accepts_allowed_file_types_when_enabled(tmp_path: Path) -> None:
    client, telegram_id, document_id = build_client(tmp_path, uploads_enabled=True)

    response = client.post(
        f"/api/case/current/documents/{document_id}/upload",
        headers={"X-Dev-Telegram-Id": telegram_id},
        files={"file": ("passport.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "uploaded_by_client"
    assert payload["has_file"] is True
    active = api_main.get_container().documents.get_latest_active_file(document_id)
    assert active is not None
    assert active.storage_path
    assert Path(active.storage_path).exists()


def _build_agency_client(tmp_path: Path) -> tuple[TestClient, str, str, api_main.Container]:
    container = build_api_container(tmp_path, database_name="agency-download-api.db", uploads_enabled=False)
    user = container.users.upsert_from_telegram(9210, "agency", "Agency", "User")
    key = new_access_key("AGENCY-API", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = container.miniapp.create_case(user, key.id, key.code)
    agency = container.documents.create_agency_item(case.id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
    container.document_storage.save_manager_agency_upload(
        case_id=case.id,
        document_item_id=agency.id,
        uploaded_by="admin:1",
        filename="hotel.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.4 agency",
    )
    container.documents.update_status(agency.id, AgencyDocumentStatus.READY_FOR_CLIENT.value, admin_id=1)
    return TestClient(api_main.app), str(user.telegram_id), agency.id, container


def test_client_downloads_ready_agency_document(tmp_path: Path) -> None:
    client, telegram_id, document_id, _ = _build_agency_client(tmp_path)

    response = client.get(
        f"/api/case/current/documents/{document_id}/download",
        headers={"X-Dev-Telegram-Id": telegram_id},
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_client_cannot_download_agency_document_without_file(tmp_path: Path) -> None:
    container = build_api_container(tmp_path, database_name="agency-no-file-api.db", uploads_enabled=False)
    user = container.users.upsert_from_telegram(9211, "agency2", "Agency", "Two")
    key = new_access_key("AGENCY-NF", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = container.miniapp.create_case(user, key.id, key.code)
    agency = container.documents.create_agency_item(case.id, DocumentCategory.INVITATION.value, admin_id=1)
    container.documents.mark_transferred_separately(agency.id, admin_id=1)
    client = TestClient(api_main.app)

    response = client.get(
        f"/api/case/current/documents/{agency.id}/download",
        headers={"X-Dev-Telegram-Id": str(user.telegram_id)},
    )

    assert response.status_code == 403


def test_agency_document_list_marks_transferred_separately(tmp_path: Path) -> None:
    container = build_api_container(tmp_path, database_name="agency-list-api.db", uploads_enabled=False)
    user = container.users.upsert_from_telegram(9212, "agency3", "Agency", "Three")
    key = new_access_key("AGENCY-LS", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = container.miniapp.create_case(user, key.id, key.code)
    agency = container.documents.create_agency_item(case.id, DocumentCategory.TRAVEL_PLAN.value, admin_id=1)
    container.documents.mark_transferred_separately(agency.id, admin_id=1)
    client = TestClient(api_main.app)

    response = client.get("/api/case/current/documents", headers={"X-Dev-Telegram-Id": str(user.telegram_id)})

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["transferred_separately"] is True
    assert item["can_download"] is False
    assert "отдельно" in item["status_label"].lower()
