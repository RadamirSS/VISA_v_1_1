from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.repositories.access_keys import new_access_key
from bot.services.notifications import build_case_submitted_notification
from fastapi.testclient import TestClient
from tests.conftest import build_api_container


def build_client(tmp_path: Path) -> TestClient:
    container = build_api_container(tmp_path, database_name="case-submission.db")
    user = container.users.upsert_from_telegram(8008, "submitter", "Case", "Submit")
    access_key = new_access_key("CASE-SUBMIT", 1, "miniapp", [], 2, None, None)
    container.access_keys.save(access_key)
    container.access_keys.bind_and_activate(access_key.code, user.id, user.telegram_id)
    return TestClient(api_main.app)


def _complete_profile(client: TestClient, telegram_id: str, applicant_id: str) -> None:
    client.patch(
        f"/api/applicants/{applicant_id}",
        headers={"X-Dev-Telegram-Id": telegram_id},
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


def test_reject_if_applicants_incomplete(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)
    client.patch("/api/case/current", headers=headers, json={"desired_country_code": "IT", "preferred_submission_city": "Москва", "submission_provider": "Italy visa center / provider to verify", "travel_purpose": "Туризм"})

    response = client.post("/api/case/current/submit", headers=headers)

    assert response.status_code == 400


def test_reject_if_country_missing_or_city_missing_for_normal_country(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)
    applicant = client.get("/api/applicants", headers=headers).json()[0]
    _complete_profile(client, "8008", applicant["id"])

    missing_country = client.post("/api/case/current/submit", headers=headers)
    client.patch("/api/case/current", headers=headers, json={"desired_country_code": "IT", "travel_purpose": "Туризм"})
    missing_city = client.post("/api/case/current/submit", headers=headers)

    assert missing_country.status_code == 400
    assert missing_city.status_code == 400


def test_allow_consultation_case_without_city_and_submit_normal_case(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)
    applicant = client.get("/api/applicants", headers=headers).json()[0]
    _complete_profile(client, "8008", applicant["id"])

    client.patch(
        "/api/case/current",
        headers=headers,
        json={
            "desired_country_code": "IT",
            "preferred_submission_city": "Москва",
            "submission_provider": "Italy visa center / provider to verify",
            "travel_purpose": "Туризм",
            "approximate_travel_start_date": "2026-09-10",
            "approximate_travel_end_date": "2026-09-20",
        },
    )
    normal_submit = client.post("/api/case/current/submit", headers=headers)

    assert normal_submit.status_code == 200
    assert normal_submit.json()["case"]["status"] == "submitted_for_manager_review"

    # Fresh container for consultation path
    client = build_client(tmp_path / "consult")
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)
    applicant = client.get("/api/applicants", headers=headers).json()[0]
    _complete_profile(client, "8008", applicant["id"])
    client.patch(
        "/api/case/current",
        headers=headers,
        json={"desired_country_code": "CONSULTATION", "desired_country_name_ru": "Не знаю, нужна консультация", "travel_purpose": "Другое / уточнить с менеджером"},
    )
    consult_submit = client.post("/api/case/current/submit", headers=headers)

    assert consult_submit.status_code == 200
    assert consult_submit.json()["case"]["status"] == "needs_manager_consultation"


def test_reject_invalid_country_and_city_for_country(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)

    invalid_country = client.patch("/api/case/current", headers=headers, json={"desired_country_code": "ZZ"})
    invalid_city = client.patch(
        "/api/case/current",
        headers=headers,
        json={"desired_country_code": "IT", "preferred_submission_city": "Париж", "submission_provider": "France visa center / provider to verify"},
    )

    assert invalid_country.status_code == 400
    assert invalid_city.status_code == 400


def test_update_case_fields(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    headers = {"X-Dev-Telegram-Id": "8008"}
    client.post("/api/case/applicants-count", headers=headers, json={"applicants_count": 1})
    client.post("/api/case", headers=headers)

    response = client.patch(
        "/api/case/current",
        headers=headers,
        json={
            "desired_country_code": "IT",
            "preferred_submission_city": "Москва",
            "submission_provider": "Italy visa center / provider to verify",
            "travel_purpose": "Туризм",
            "approximate_travel_start_date": "2026-09-10",
            "approximate_travel_end_date": "2026-09-20",
            "client_comment": "Подача нужна осенью",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["desired_country_code"] == "IT"
    assert payload["preferred_submission_city"] == "Москва"
    assert payload["submission_provider"] == "Italy visa center / provider to verify"
    assert payload["travel_purpose"] == "Туризм"
    assert payload["approximate_travel_start_date"] == "2026-09-10"


def test_manager_notification_payload_excludes_sensitive_fields() -> None:
    text = build_case_submitted_notification(
        case_id="VISA-CASE-2026-000123",
        telegram_id=123456,
        username="client",
        applicants_count=3,
        country_name="Италия",
        city="Москва",
        provider="Italy visa center / provider to verify",
        travel_purpose="Туризм",
        case_status="submitted_for_manager_review",
    )

    assert "123456789" not in text
    assert "passport" not in text.lower()
    assert "место рождения" not in text.lower()
    assert "адрес" not in text.lower()
