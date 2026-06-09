from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.database import init_db
from bot.repositories.access_keys import AccessKeyRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository


def build_client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'consulate-config.db'}"
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
    return TestClient(api_main.app)


def test_countries_endpoint_returns_countries(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/config/countries", headers={"X-Dev-Telegram-Id": "7007"})

    assert response.status_code == 200
    assert any(item["code"] == "IT" for item in response.json())


def test_consulates_endpoint_filters_by_country_and_includes_verification_status(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/config/consulates?countryCode=IT", headers={"X-Dev-Telegram-Id": "7007"})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(item["country_code"] == "IT" for item in payload)
    assert all("verification_status" in item for item in payload)


def test_unknown_country_returns_empty_list(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/config/consulates?countryCode=ZZ", headers={"X-Dev-Telegram-Id": "7007"})

    assert response.status_code == 200
    assert response.json() == []
