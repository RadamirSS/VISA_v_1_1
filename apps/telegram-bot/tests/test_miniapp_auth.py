from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.repositories.access_keys import new_access_key
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path, dev_auth: bool = True) -> TestClient:
    build_api_container(tmp_path, database_name="miniapp-auth.db", miniapp_dev_auth=dev_auth)
    return TestClient(api_main.app)


def test_valid_dev_auth_returns_identity(tmp_path: Path) -> None:
    client = build_client(tmp_path, dev_auth=True)

    response = client.post("/api/telegram/validate", headers={"X-Dev-Telegram-Id": "1001", "X-Dev-Username": "client"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["telegram_id"] == 1001
    assert payload["username"] == "client"


def test_missing_auth_rejected_when_dev_auth_disabled(tmp_path: Path) -> None:
    client = build_client(tmp_path, dev_auth=False)

    response = client.get("/api/me")

    assert response.status_code == 401


def test_user_cannot_access_other_users_profile(tmp_path: Path) -> None:
    client = build_client(tmp_path, dev_auth=True)
    container = api_main.get_container()
    primary_user = container.users.upsert_from_telegram(1001, "alpha", "A", "User")
    access_key = new_access_key("AUTH-1001", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(access_key)
    container.access_keys.bind_and_activate(access_key.code, primary_user.id, primary_user.telegram_id)
    case = container.miniapp.ensure_case(primary_user, access_key.id, access_key.code)
    container.miniapp.set_applicants_count(case, 1)
    applicant = container.miniapp.list_applicants(1001)[0]

    response = client.get(f"/api/applicants/{applicant.id}", headers={"X-Dev-Telegram-Id": "2002"})

    assert response.status_code == 404
