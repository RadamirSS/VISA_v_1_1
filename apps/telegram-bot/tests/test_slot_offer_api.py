from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.slot_offers import ParsedSlotOption


def build_client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'slot-offer-api.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    api_main._container = api_main.Container(
        settings=api_main.Settings(
            bot_token="",
            bot_admin_ids=[],
            database_url=database_url,
            client_miniapp_url="http://localhost:3001",
            miniapp_bot_token="",
            miniapp_allowed_origin="http://localhost:3001",
            miniapp_dev_auth=True,
            repo_root=repo_root,
            root_dir=repo_root / "apps" / "telegram-bot",
        ),
        users=UserRepository(database_url),
        access_keys=AccessKeyRepository(database_url),
        miniapp=MiniAppRepository(database_url, repo_root=repo_root),
    )
    container = api_main.get_container()
    user = container.users.upsert_from_telegram(9300, "apiuser", "Api", "User")
    key = new_access_key("API-KEY", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = container.miniapp.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    container.miniapp.save_case(case)
    container.miniapp.create_slot_offer(case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])
    return TestClient(api_main.app)


def test_user_sees_own_slot_offers(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/case/current/slot-offers", headers={"X-Dev-Telegram-Id": "9300"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_user_cannot_see_another_users_offers(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/case/current/slot-offers", headers={"X-Dev-Telegram-Id": "9301"})

    assert response.status_code in {403, 404}


def test_user_selects_available_option_and_cannot_select_unavailable(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "9300"}
    offers = client.get("/api/case/current/slot-offers", headers=headers).json()
    option_id = offers[0]["options"][0]["id"]

    selected = client.post(f"/api/case/current/slot-options/{option_id}/select", headers=headers)
    repeat = client.post(f"/api/case/current/slot-options/{option_id}/select", headers=headers)

    assert selected.status_code == 200
    assert selected.json()["status"] == "slot_selected_by_client"
    assert repeat.status_code == 400
