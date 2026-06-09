from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.repositories.access_keys import new_access_key
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path) -> tuple[TestClient, str]:
    container = build_api_container(tmp_path, database_name="applicant-profiles.db")
    user = container.users.upsert_from_telegram(3003, "group", "Mini", "App")
    access_key = new_access_key("GROUP-3003", 1, "miniapp", [], 3, None, None)
    container.access_keys.save(access_key)
    container.access_keys.bind_and_activate(access_key.code, user.id, user.telegram_id)
    return TestClient(api_main.app), "3003"


def test_create_applicants_count_and_list(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": telegram_id}

    case_response = client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 2})
    list_response = client.get("/api/applicants", headers=headers)

    assert case_response.status_code == 200
    assert case_response.json()["applicants_count"] == 2
    assert len(list_response.json()) == 2


def test_update_profile_calculates_completion_and_status(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": telegram_id}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    applicant = client.get("/api/applicants", headers=headers).json()[0]

    response = client.patch(
        f"/api/applicants/{applicant['id']}",
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

    assert response.status_code == 200
    assert response.json()["completion_percent"] == 100
    assert response.json()["status"] == "completed"


def test_copy_address_and_contacts_from_primary(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": telegram_id}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 2})
    applicants = client.get("/api/applicants", headers=headers).json()
    primary = applicants[0]
    secondary = applicants[1]
    client.patch(
        f"/api/applicants/{primary['id']}",
        headers=headers,
        json={
            "phone": "+79990000000",
            "email": "group@example.com",
            "residence_country": "Россия",
            "residence_city": "Москва",
            "residence_address": "ул. Пример, 1",
            "postal_code": "101000",
        },
    )

    response = client.post(f"/api/applicants/{secondary['id']}/copy-from-primary", headers=headers)

    assert response.status_code == 200
    assert response.json()["phone"] == "+79990000000"
    assert response.json()["residence_address"] == "ул. Пример, 1"
