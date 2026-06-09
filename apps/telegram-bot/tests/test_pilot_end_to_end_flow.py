from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.models import (
    AgencyDocumentStatus,
    AppointmentSlotOptionStatus,
    ClientDocumentStatus,
    DocumentCategory,
    VisaCaseStatus,
)
from bot.repositories.access_keys import new_access_key
from bot.services.case_status import case_status_label, format_case_public_number
from bot.services.manager_case_actions import (
    ManagerCaseQueueItem,
    build_manager_queue_view,
    queue_text_contains_raw_status,
)
from bot.services.manager_case_view import (
    SENSITIVE_SUBSTRINGS,
    render_document_summary_for_manager,
    render_manager_case_summary,
    render_queue_item,
)
from bot.services.notifications import build_slot_selected_notification
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

ADMIN_ID = 1


@dataclass
class PilotContext:
    client: TestClient
    telegram_id: str
    username: str
    container: api_main.Container


def _headers(telegram_id: str) -> dict[str, str]:
    return {"X-Dev-Telegram-Id": telegram_id}


def build_pilot_context(tmp_path: Path, *, uploads_enabled: bool = True) -> PilotContext:
    container = build_api_container(
        tmp_path,
        database_name="pilot-e2e.db",
        uploads_enabled=uploads_enabled,
    )
    user = container.users.upsert_from_telegram(10001, "pilotclient", "Pilot", "Client")
    key = new_access_key("PILOT-KEY-01", ADMIN_ID, "miniapp", [], 2, None, None)
    container.access_keys.save(key)
    container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
    return PilotContext(
        client=TestClient(api_main.app),
        telegram_id=str(user.telegram_id),
        username="pilotclient",
        container=container,
    )


def _complete_profile(client: TestClient, telegram_id: str, applicant_id: str) -> None:
    response = client.patch(
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
    assert response.status_code == 200


def _submit_case(ctx: PilotContext) -> str:
    client = ctx.client
    telegram_id = ctx.telegram_id
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
    return submit.json()["case"]["id"]


def test_scenario_1_access_key_and_case_creation(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path)
    case_id = _submit_case(ctx)

    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None
    public_number = format_case_public_number(case)
    assert public_number.startswith("VISA-CASE-")

    current = ctx.client.get("/api/case/current", headers=_headers(ctx.telegram_id))
    assert current.status_code == 200
    assert current.json()["id"] == case_id
    assert current.json()["status"] == VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value

    summary = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id))
    assert summary.status_code == 200
    serialized = json.dumps(summary.json())
    for key in SENSITIVE_KEYS:
        assert key not in serialized
    assert summary.json()["case"]["status_label"] == "Заявка отправлена менеджеру"


def test_scenario_2_manager_queue_and_case_workspace(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path)
    case_id = _submit_case(ctx)
    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None

    active_cases = ctx.container.miniapp.list_manager_active_cases_with_username()
    case_ids = {item[0].id for item in active_cases}
    assert case_id in case_ids

    applicants = ctx.container.miniapp.list_applicants_for_case(case_id)
    doc_counts = ctx.container.documents.count_summary(case_id)
    summary_text = render_manager_case_summary(
        case,
        username=ctx.username,
        applicants=applicants,
        doc_counts=doc_counts,
    )
    queue_text = render_queue_item(case)
    queue_view = build_manager_queue_view(
        [
            ManagerCaseQueueItem(
                visa_case=case,
                username=ctx.username,
                client_pending=int(doc_counts.get("client_pending", 0)),
                client_under_review=int(doc_counts.get("client_under_review", 0)),
            )
        ]
    )

    assert format_case_public_number(case) in summary_text
    assert f"@{ctx.username}" in summary_text
    assert ctx.telegram_id in summary_text
    assert "Италия" in summary_text
    assert "Москва" in summary_text
    assert "Italy visa center" in summary_text
    assert "Заявителей: 1" in summary_text
    assert "документы не запрошены" in summary_text
    assert "не назначена" in summary_text
    assert "Заявка отправлена менеджеру" in summary_text

    for text in (summary_text, queue_text, queue_view.summary_text):
        assert queue_text_contains_raw_status(text) is False
        for substring in SENSITIVE_SUBSTRINGS:
            assert substring not in text
        assert "storage_path" not in text
        assert "http://" not in text
        assert "https://" not in text


def test_scenario_3_client_document_request_and_upload(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path, uploads_enabled=True)
    case_id = _submit_case(ctx)

    doc_item = ctx.container.documents.create_client_request(
        case_id,
        DocumentCategory.INTERNATIONAL_PASSPORT.value,
        admin_id=ADMIN_ID,
    )

    list_response = ctx.client.get("/api/case/current/documents", headers=_headers(ctx.telegram_id))
    assert list_response.status_code == 200
    documents = list_response.json()["items"]
    assert len(documents) == 1
    assert documents[0]["id"] == doc_item.id

    upload = ctx.client.post(
        f"/api/case/current/documents/{doc_item.id}/upload",
        headers=_headers(ctx.telegram_id),
        files={"file": ("passport-scan.pdf", BytesIO(b"%PDF-1.4 pilot"), "application/pdf")},
    )
    assert upload.status_code == 200
    assert upload.json()["status"] == ClientDocumentStatus.UPLOADED_BY_CLIENT.value

    updated = ctx.container.documents.get_for_case(case_id, doc_item.id)
    assert updated is not None
    assert updated.status == ClientDocumentStatus.UPLOADED_BY_CLIENT.value

    counts = ctx.container.documents.count_summary(case_id)
    doc_summary = render_document_summary_for_manager(counts)
    assert "1 на проверке" in doc_summary

    refreshed = ctx.client.get("/api/case/current/documents", headers=_headers(ctx.telegram_id)).json()
    serialized = json.dumps(list_response.json()) + json.dumps(refreshed)
    assert "storage_path" not in serialized
    assert "passport-scan.pdf" not in serialized


def test_scenario_4_agency_document_upload_and_download(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path, uploads_enabled=True)
    case_id = _submit_case(ctx)

    agency = ctx.container.documents.create_agency_item(
        case_id,
        DocumentCategory.HOTEL_BOOKING.value,
        admin_id=ADMIN_ID,
    )
    assert agency.status == AgencyDocumentStatus.PREPARING_BY_AGENCY.value

    with pytest.raises(ValueError):
        ctx.container.documents.mark_agency_ready_after_upload(agency.id, admin_id=ADMIN_ID)

    ctx.container.document_storage.save_manager_agency_upload(
        case_id=case_id,
        document_item_id=agency.id,
        uploaded_by=f"admin:{ADMIN_ID}",
        filename="hotel-booking.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.4 hotel booking",
    )
    ready = ctx.container.documents.mark_agency_ready_after_upload(agency.id, admin_id=ADMIN_ID)
    assert ready.status == AgencyDocumentStatus.READY_FOR_CLIENT.value

    download = ctx.client.get(
        f"/api/case/current/documents/{agency.id}/download",
        headers=_headers(ctx.telegram_id),
    )
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")

    other_user = ctx.client.get(
        f"/api/case/current/documents/{agency.id}/download",
        headers=_headers("10002"),
    )
    assert other_user.status_code in {403, 404}

    docs_response = ctx.client.get("/api/case/current/documents", headers=_headers(ctx.telegram_id)).json()
    serialized = json.dumps(docs_response)
    assert "storage_path" not in serialized
    assert "http://" not in serialized
    assert "https://" not in serialized
    assert "hotel-booking.pdf" not in serialized


def test_scenario_5_slot_offers_and_client_selection(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path)
    case_id = _submit_case(ctx)
    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None

    _, options, _ = ctx.container.miniapp.create_slot_offer(
        case.id,
        ADMIN_ID,
        [
            ParsedSlotOption(option_date="2026-07-15", option_time="10:30", city="Москва", provider="VMS Italy"),
            ParsedSlotOption(option_date="2026-07-16", option_time="11:00", city="Москва", provider="VMS Italy"),
            ParsedSlotOption(option_date="2026-07-17", option_time="09:00", city="Москва", provider="VMS Italy"),
        ],
    )

    offers = ctx.client.get("/api/case/current/slot-offers", headers=_headers(ctx.telegram_id))
    assert offers.status_code == 200
    assert len(offers.json()) == 1
    assert len(offers.json()[0]["options"]) == 3

    option_id = options[0].id
    selected = ctx.client.post(
        f"/api/case/current/slot-options/{option_id}/select",
        headers=_headers(ctx.telegram_id),
    )
    assert selected.status_code == 200
    assert selected.json()["status"] == VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value

    other_select = ctx.client.post(
        f"/api/case/current/slot-options/{option_id}/select",
        headers=_headers("10002"),
    )
    assert other_select.status_code in {403, 404}

    with ctx.container.miniapp._connect() as connection:
        connection.execute(
            "UPDATE appointment_slot_options SET status = ? WHERE id = ?",
            (AppointmentSlotOptionStatus.EXPIRED.value, options[2].id),
        )
        connection.commit()
    expired_select = ctx.client.post(
        f"/api/case/current/slot-options/{options[2].id}/select",
        headers=_headers(ctx.telegram_id),
    )
    assert expired_select.status_code == 400

    notification = build_slot_selected_notification(
        case_id=case.id,
        telegram_id=int(ctx.telegram_id),
        username=ctx.username,
        option_date="2026-07-15",
        option_time="10:30",
        city="Москва",
        provider="VMS Italy",
    )
    lowered = notification.lower()
    assert "passport" not in lowered
    assert "birth_place" not in lowered
    assert "residence_address" not in lowered
    assert case.id in notification
    assert "2026-07-15" in notification


def test_scenario_6_appointment_confirmation(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path)
    case_id = _submit_case(ctx)
    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None

    with pytest.raises(ValueError):
        ctx.container.miniapp.confirm_appointment(case.id, ADMIN_ID)

    _, options, _ = ctx.container.miniapp.create_slot_offer(
        case.id,
        ADMIN_ID,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30", city="Москва", provider="VMS Italy")],
    )
    ctx.container.miniapp.select_slot_option_for_user(int(ctx.telegram_id), options[0].id)
    confirmed_case = ctx.container.miniapp.confirm_appointment(case.id, ADMIN_ID)
    assert confirmed_case.status == VisaCaseStatus.APPOINTMENT_CONFIRMED.value

    summary = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id))
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["appointment"]["confirmed"] is not None
    assert payload["case"]["status"] == VisaCaseStatus.APPOINTMENT_CONFIRMED.value
    assert payload["case"]["status_label"] == "Запись подтверждена"
    assert payload["case"]["status_label"] != payload["case"]["status"]

    timeline = ctx.client.get("/api/case/current/timeline", headers=_headers(ctx.telegram_id))
    assert timeline.status_code == 200
    timeline_payload = timeline.json()
    assert timeline_payload["status_label"] == case_status_label(VisaCaseStatus.APPOINTMENT_CONFIRMED.value)
    confirmed_step = next(item for item in timeline_payload["steps"] if item["key"] == "confirmed")
    assert confirmed_step["state"] == "current"


def test_pilot_flow_final_status_labels(tmp_path: Path) -> None:
    ctx = build_pilot_context(tmp_path, uploads_enabled=True)
    case_id = _submit_case(ctx)

    applicants_summary = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id)).json()
    assert applicants_summary["applicants"]["completed"] == 1

    submitted_summary = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id)).json()
    assert submitted_summary["case"]["status_label"] == "Заявка отправлена менеджеру"

    ctx.container.documents.create_client_request(case_id, DocumentCategory.PHOTO.value, admin_id=ADMIN_ID)
    doc_item = ctx.container.documents.list_by_case(case_id)[0]
    ctx.client.post(
        f"/api/case/current/documents/{doc_item.id}/upload",
        headers=_headers(ctx.telegram_id),
        files={"file": ("photo.png", BytesIO(b"\x89PNG\r\n"), "image/png")},
    )

    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None
    _, options, _ = ctx.container.miniapp.create_slot_offer(
        case.id,
        ADMIN_ID,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")],
    )
    ctx.container.miniapp.select_slot_option_for_user(int(ctx.telegram_id), options[0].id)
    ctx.container.miniapp.confirm_appointment(case.id, ADMIN_ID)

    timeline = ctx.client.get("/api/case/current/timeline", headers=_headers(ctx.telegram_id)).json()
    step_labels = {item["key"]: item["label"] for item in timeline["steps"]}
    assert "заполнен" in step_labels["profiles"].lower()
    assert step_labels["submitted"] == "Заявка отправлена менеджеру"
    assert step_labels["slot_options"] == "Даты отправлены клиенту"
    assert step_labels["slot_selected"] == "Дата выбрана клиентом"
    assert step_labels["confirmed"] == "Запись подтверждена"

    final_summary = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id)).json()
    assert final_summary["case"]["status_label"] == "Запись подтверждена"
