from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.repositories.access_keys import new_access_key
from bot.repositories.miniapp import MiniAppRepository
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path, with_access_key: bool) -> tuple[TestClient, MiniAppRepository]:
    container = build_api_container(tmp_path, database_name="case-creation.db")
    user = container.users.upsert_from_telegram(5001, "casecreate", "Case", "Create")
    if with_access_key:
        access_key = new_access_key("CASE-CREATE", 1, "miniapp", [], 2, None, None)
        container.access_keys.save(access_key)
        container.access_keys.bind_and_activate(access_key.code, user.id, user.telegram_id)
    return TestClient(api_main.app), container.miniapp


def test_cannot_create_case_without_access_key(tmp_path: Path) -> None:
    client, _ = build_client(tmp_path, with_access_key=False)

    response = client.post("/api/case", headers={"X-Dev-Telegram-Id": "5001"})

    assert response.status_code == 403


def test_can_create_draft_case_with_valid_access_key(tmp_path: Path) -> None:
    client, miniapp = build_client(tmp_path, with_access_key=True)
    user_case = miniapp.get_case_for_telegram_user(5001)
    assert user_case is None

    response = client.post("/api/case", headers={"X-Dev-Telegram-Id": "5001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case"]["status"] in {"profiles_in_progress", "profiles_completed"}


def test_case_links_to_current_telegram_user_and_other_user_cannot_read_it(tmp_path: Path) -> None:
    client, miniapp = build_client(tmp_path, with_access_key=True)
    client.post("/api/case/applicants-count", headers={"X-Dev-Telegram-Id": "5001"}, json={"applicants_count": 1})
    create_response = client.post("/api/case", headers={"X-Dev-Telegram-Id": "5001"})
    case_id = create_response.json()["case"]["id"]

    case = miniapp.get_case_by_id(5001, case_id)
    assert case is not None
    assert case.telegram_id == 5001

    other = client.get("/api/case/current", headers={"X-Dev-Telegram-Id": "6002"})
    assert other.status_code in {403, 404}
