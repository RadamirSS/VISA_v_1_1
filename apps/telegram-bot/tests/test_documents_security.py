from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.models import DocumentCategory
from bot.repositories.access_keys import new_access_key
from bot.services.notifications import (
    build_agency_document_ready_message,
    build_client_uploaded_notification,
    build_documents_requested_message,
)
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path) -> tuple[TestClient, str, str]:
    container = build_api_container(tmp_path, database_name="documents-security.db", uploads_enabled=True)
    owner = container.users.upsert_from_telegram(9400, "owner", "Owner", "User")
    key = new_access_key("SEC-KEY", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, owner.id, owner.telegram_id)
    case = container.miniapp.create_case(owner, key.id, key.code)
    item = container.documents.create_client_request(case.id, DocumentCategory.PHOTO.value, admin_id=1)
    return TestClient(api_main.app), str(owner.telegram_id), item.id


def test_cross_user_document_upload_returns_404(tmp_path: Path) -> None:
    client, _, document_id = build_client(tmp_path)

    response = client.post(
        f"/api/case/current/documents/{document_id}/upload",
        headers={"X-Dev-Telegram-Id": "9401"},
        files={"file": ("photo.png", BytesIO(b"\x89PNG\r\n"), "image/png")},
    )

    assert response.status_code in {403, 404}


def test_document_list_does_not_expose_storage_path(tmp_path: Path) -> None:
    client, telegram_id, document_id = build_client(tmp_path)
    client.post(
        f"/api/case/current/documents/{document_id}/upload",
        headers={"X-Dev-Telegram-Id": telegram_id},
        files={"file": ("photo.png", BytesIO(b"\x89PNG\r\n"), "image/png")},
    )

    response = client.get("/api/case/current/documents", headers={"X-Dev-Telegram-Id": telegram_id})
    payload = response.json()

    serialized = str(payload)
    assert "storage_path" not in serialized
    assert "photo.png" not in serialized


def test_notification_texts_contain_no_sensitive_content() -> None:
    requested = build_documents_requested_message()
    ready = build_agency_document_ready_message("Бронь отеля")
    uploaded = build_client_uploaded_notification("VISA-CASE-2026-000123", "Загранпаспорт", "uploaded_by_client")

    for text in (requested, ready, uploaded):
        lowered = text.lower()
        assert "passport" not in lowered
        assert "http://" not in lowered
        assert "https://" not in lowered

    assert "Загранпаспорт" in uploaded
    assert "uploaded_by_client" in uploaded
