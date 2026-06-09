from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path) -> TestClient:
    build_api_container(tmp_path, database_name="consulate-config.db")
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
