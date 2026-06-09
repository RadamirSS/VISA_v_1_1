from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.repositories.access_keys import new_access_key
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path) -> tuple[TestClient, str]:
    container = build_api_container(tmp_path, database_name="visa-cases.db")
    user = container.users.upsert_from_telegram(4040, "caseuser", "Case", "User")
    access_key = new_access_key("CASE-4040", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(access_key)
    container.access_keys.bind_and_activate(access_key.code, user.id, user.telegram_id)
    return TestClient(api_main.app), "4040"


def _complete_profile(client: TestClient, headers: dict[str, str], applicant_id: str) -> None:
    client.patch(
        f"/api/applicants/{applicant_id}",
        headers=headers,
        json={
            "last_name_latin": "IVANOV",
            "first_name_latin": "IVAN",
            "last_name_cyrillic": "Иванов",
            "first_name_cyrillic": "Иван",
            "birth_date": "1990-01-01",
            "birth_place": "Москва",
            "citizenship": "Россия",
            "phone": "+79990000000",
            "residence_country": "Россия",
            "residence_city": "Москва",
            "residence_address": "ул. Пример, 1",
            "passport_number": "123456789",
            "passport_issue_date": "2020-01-01",
            "passport_expiry_date": "2030-01-01",
            "passport_issuing_country": "Россия",
            "desired_country_code": "IT",
            "travel_purpose": "Туризм",
        },
    )


def test_create_current_case_after_access(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)

    response = client.post("/api/case", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 200
    assert response.json()["case"]["status"] == "profiles_in_progress"


def test_update_applicants_count_changes_case_status(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": telegram_id}

    response = client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 2})

    assert response.status_code == 200
    assert response.json()["status"] == "profiles_in_progress"


def test_case_status_becomes_profiles_in_progress_and_completed(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": telegram_id}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 2})
    applicants = client.get("/api/applicants", headers=headers).json()

    _complete_profile(client, headers, applicants[0]["id"])
    in_progress = client.get("/api/case/current", headers=headers)
    _complete_profile(client, headers, applicants[1]["id"])
    completed = client.get("/api/case/current", headers=headers)

    assert in_progress.json()["status"] == "profiles_in_progress"
    assert completed.json()["status"] == "profiles_completed"
