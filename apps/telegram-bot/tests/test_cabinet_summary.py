from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.models import AppointmentSlotOptionStatus, DocumentCategory, VisaCaseStatus
from bot.repositories.access_keys import new_access_key
from bot.services.slot_offers import ParsedSlotOption
from tests.conftest import build_api_container

SENSITIVE_KEYS = {
    "passport_number",
    "passport_issue_date",
    "passport_expiry_date",
    "birth_place",
    "residence_address",
    "passport_issuing_authority",
    "postal_code",
}


def build_client(tmp_path: Path, *, with_access: bool = True) -> tuple[TestClient, str, api_main.Container]:
    container = build_api_container(tmp_path, database_name="cabinet-summary.db")
    user = container.users.upsert_from_telegram(6100, "cabinetuser", "Cabinet", "User")
    if with_access:
        key = new_access_key("CABINET-KEY", 1, "miniapp", [], 2, None, None)
        container.access_keys.save(key)
        container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    return TestClient(api_main.app), str(user.telegram_id), container


def _headers(telegram_id: str) -> dict[str, str]:
    return {"X-Dev-Telegram-Id": telegram_id}


def _complete_profile(client: TestClient, telegram_id: str, applicant_id: str) -> None:
    client.patch(
        f"/api/applicants/{applicant_id}",
        headers=_headers(telegram_id),
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


def _prepare_submitted_case(client: TestClient, telegram_id: str) -> None:
    client.post("/api/case/applicants-count", headers=_headers(telegram_id), json={"applicants_count": 1})
    client.post("/api/case", headers=_headers(telegram_id))
    applicant = client.get("/api/applicants", headers=_headers(telegram_id)).json()[0]
    _complete_profile(client, telegram_id, applicant["id"])
    patch = client.patch(
        "/api/case/current",
        headers=_headers(telegram_id),
        json={
            "desired_country_code": "IT",
            "desired_country_name_ru": "Италия",
            "preferred_submission_city": "Москва",
            "submission_provider": "Italy visa center / provider to verify",
            "travel_purpose": "Туризм",
            "approximate_travel_start_date": "2026-09-10",
            "approximate_travel_end_date": "2026-09-20",
        },
    )
    assert patch.status_code == 200
    submit = client.post("/api/case/current/submit", headers=_headers(telegram_id))
    assert submit.status_code == 200
    assert submit.json()["case"]["status"] == VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value


def test_no_access_key_summary(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path, with_access=False)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["access"]["active"] is False
    assert payload["case"] is None
    assert payload["next_action"]["type"] == "enter_access_key"


def test_access_active_no_case_summary(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["access"]["active"] is True
    assert payload["case"] is None
    assert payload["next_action"]["type"] == "create_case"


def test_case_with_incomplete_applicants(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)
    client.post("/api/case/applicants-count", headers=_headers(telegram_id), json={"applicants_count": 2})
    client.post("/api/case", headers=_headers(telegram_id))

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["applicants"]["incomplete"] > 0
    assert payload["case"]["status_label"] == "Анкеты заполняются"


def test_case_submitted_for_manager_review(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["case"]["status"] == VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    assert payload["case"]["status_label"] == "Заявка отправлена менеджеру"


def test_case_with_slot_options_sent(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    container.miniapp.create_slot_offer(case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["appointment"]["has_options"] is True
    assert payload["case"]["status"] == VisaCaseStatus.SLOT_OPTIONS_SENT.value
    assert payload["case"]["next_action"]["type"] == "select_slot"


def test_slot_options_sent_without_available_options(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    _, options, _ = container.miniapp.create_slot_offer(
        case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")]
    )
    with container.miniapp._connect() as connection:
        connection.execute(
            "UPDATE appointment_slot_options SET status = ? WHERE id = ?",
            (AppointmentSlotOptionStatus.EXPIRED.value, options[0].id),
        )
        connection.commit()

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["appointment"]["has_options"] is False
    assert payload["case"]["status"] == VisaCaseStatus.SLOT_OPTIONS_SENT.value
    assert payload["case"]["next_action"]["type"] != "select_slot"
    assert payload["case"]["next_action"]["type"] == "wait_manager"


def test_case_with_selected_slot(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    _, options, _ = container.miniapp.create_slot_offer(
        case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30", city="Москва", provider="VMS Italy")]
    )
    container.miniapp.select_slot_option_for_user(int(telegram_id), options[0].id)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["appointment"]["selected"] is not None
    assert payload["appointment"]["selected"]["date"] == "2026-07-15"
    assert payload["case"]["status"] == VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value
    assert payload["case"]["next_action"]["type"] == "wait_confirmation"


def test_case_with_confirmed_appointment(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    _, options, _ = container.miniapp.create_slot_offer(
        case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30", city="Москва", provider="VMS Italy")]
    )
    container.miniapp.select_slot_option_for_user(int(telegram_id), options[0].id)
    container.miniapp.confirm_appointment(case.id, 1)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["appointment"]["confirmed"] is not None
    assert payload["case"]["status"] == VisaCaseStatus.APPOINTMENT_CONFIRMED.value
    assert payload["case"]["next_action"]["type"] == "view_appointment"


def test_has_options_false_when_all_options_selected(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    _prepare_submitted_case(client, telegram_id)
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    _, options, _ = container.miniapp.create_slot_offer(
        case.id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")]
    )
    container.miniapp.select_slot_option_for_user(int(telegram_id), options[0].id)

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["appointment"]["has_options"] is False


def test_summary_excludes_sensitive_applicant_fields(tmp_path: Path) -> None:
    client, telegram_id, _ = build_client(tmp_path)
    client.post("/api/case/applicants-count", headers=_headers(telegram_id), json={"applicants_count": 1})
    client.post("/api/case", headers=_headers(telegram_id))
    applicant = client.get("/api/applicants", headers=_headers(telegram_id)).json()[0]
    _complete_profile(client, telegram_id, applicant["id"])

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    serialized = json.dumps(response.json())
    for key in SENSITIVE_KEYS:
        assert key not in serialized


def test_summary_includes_documents_block(tmp_path: Path) -> None:
    client, telegram_id, container = build_client(tmp_path)
    client.post("/api/case/applicants-count", headers=_headers(telegram_id), json={"applicants_count": 1})
    case_response = client.post("/api/case", headers=_headers(telegram_id)).json()
    container.documents.create_client_request(
        case_response["case"]["id"],
        DocumentCategory.PHOTO.value,
        admin_id=1,
    )

    response = client.get("/api/cabinet/summary", headers=_headers(telegram_id))

    assert response.status_code == 200
    documents = response.json()["documents"]
    assert documents["has_items"] is True
    assert documents["client_pending"] == 1
