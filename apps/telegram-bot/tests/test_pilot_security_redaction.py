from __future__ import annotations

import json
from pathlib import Path

from bot.models import DocumentCategory, VisaCaseStatus
from bot.services.case_status import case_status_label, format_case_public_number
from bot.services.document_status import document_status_label
from bot.services.manager_case_actions import ManagerCaseQueueItem, queue_text_contains_raw_status
from bot.services.manager_case_view import render_manager_case_summary, render_queue_item
from bot.services.notifications import (
    build_agency_document_ready_message,
    build_agency_document_transferred_separately_message,
    build_appointment_confirmed_message,
    build_case_submitted_notification,
    build_client_uploaded_notification,
    build_documents_requested_message,
    build_profiles_completed_notification,
    build_slot_options_message,
    build_slot_options_sent_to_manager,
    build_slot_selected_notification,
    build_user_case_submitted_message,
    build_user_slot_selected_message,
)
from bot.services.slot_offers import ParsedSlotOption
from tests.test_pilot_end_to_end_flow import (
    ADMIN_ID,
    SENSITIVE_KEYS,
    _headers,
    _submit_case,
    build_pilot_context,
)

FORBIDDEN_FIELD_NAMES = {
    "passport_number",
    "birth_place",
    "residence_address",
    "storage_path",
    "bank_statement_file",
}
FORBIDDEN_SUBSTRINGS = FORBIDDEN_FIELD_NAMES | {"http://", "https://", "123456789"}


def _assert_no_forbidden(content: str) -> None:
    lowered = content.lower()
    for item in FORBIDDEN_SUBSTRINGS:
        assert item not in lowered, f"Forbidden substring found: {item}"


def _build_redaction_context(tmp_path: Path):
    ctx = build_pilot_context(tmp_path, uploads_enabled=True)
    case_id = _submit_case(ctx)
    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None

    doc_item = ctx.container.documents.create_client_request(
        case_id,
        DocumentCategory.INTERNATIONAL_PASSPORT.value,
        admin_id=ADMIN_ID,
    )
    ctx.client.post(
        f"/api/case/current/documents/{doc_item.id}/upload",
        headers=_headers(ctx.telegram_id),
        files={"file": ("passport-scan.pdf", b"%PDF-1.4 pilot", "application/pdf")},
    )
    updated_doc = ctx.container.documents.get_for_case(case_id, doc_item.id)
    assert updated_doc is not None

    _, options, _ = ctx.container.miniapp.create_slot_offer(
        case.id,
        ADMIN_ID,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30", city="Москва", provider="VMS Italy")],
    )
    ctx.container.miniapp.select_slot_option_for_user(int(ctx.telegram_id), options[0].id)
    ctx.container.miniapp.confirm_appointment(case.id, ADMIN_ID)
    case = ctx.container.miniapp.get_case_by_any_id(case_id)
    assert case is not None

    applicants = ctx.container.miniapp.list_applicants_for_case(case_id)
    doc_counts = ctx.container.documents.count_summary(case_id)
    queue_item = ManagerCaseQueueItem(visa_case=case, username=ctx.username)
    return ctx, case, applicants, doc_counts, queue_item, updated_doc


def test_manager_case_summary_redaction(tmp_path: Path) -> None:
    _, case, applicants, doc_counts, _, _ = _build_redaction_context(tmp_path)
    text = render_manager_case_summary(
        case,
        username="pilotclient",
        applicants=applicants,
        doc_counts=doc_counts,
    )
    _assert_no_forbidden(text)
    assert queue_text_contains_raw_status(text) is False
    assert format_case_public_number(case) in text
    assert str(case.telegram_id) in text
    assert "Италия" in text
    assert "Москва" in text


def test_manager_queue_item_redaction(tmp_path: Path) -> None:
    _, case, _, _, queue_item, _ = _build_redaction_context(tmp_path)
    text = render_queue_item(queue_item.visa_case)
    _assert_no_forbidden(text)
    assert queue_text_contains_raw_status(text) is False
    assert format_case_public_number(case) in text
    assert case_status_label(case.status) in text


def test_cabinet_summary_redaction(tmp_path: Path) -> None:
    ctx, case, _, _, _, _ = _build_redaction_context(tmp_path)
    response = ctx.client.get("/api/cabinet/summary", headers=_headers(ctx.telegram_id))
    assert response.status_code == 200
    serialized = json.dumps(response.json())
    _assert_no_forbidden(serialized)
    for key in SENSITIVE_KEYS:
        assert key not in serialized
    payload = response.json()
    assert payload["case"]["status_label"] == "Запись подтверждена"
    assert payload["appointment"]["confirmed"] is not None


def test_timeline_response_redaction(tmp_path: Path) -> None:
    ctx, case, _, _, _, _ = _build_redaction_context(tmp_path)
    response = ctx.client.get("/api/case/current/timeline", headers=_headers(ctx.telegram_id))
    assert response.status_code == 200
    serialized = json.dumps(response.json())
    _assert_no_forbidden(serialized)
    payload = response.json()
    assert payload["status_label"] == case_status_label(case.status)
    assert payload["status_label"] != payload["status"]


def test_document_list_api_redaction(tmp_path: Path) -> None:
    ctx, _, _, _, _, _ = _build_redaction_context(tmp_path)
    response = ctx.client.get("/api/case/current/documents", headers=_headers(ctx.telegram_id))
    assert response.status_code == 200
    serialized = json.dumps(response.json())
    _assert_no_forbidden(serialized)
    assert "passport-scan.pdf" not in serialized
    items = response.json()["items"]
    assert items
    assert items[0]["title"] == "Загранпаспорт"
    assert items[0]["status_label"]


def test_notification_texts_redaction(tmp_path: Path) -> None:
    _, case, _, _, _, updated_doc = _build_redaction_context(tmp_path)
    public_number = format_case_public_number(case)
    status_label = case_status_label(VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value)
    doc_label = document_status_label(updated_doc, has_file=True)

    notifications = [
        build_documents_requested_message(),
        build_agency_document_ready_message("Бронь отеля"),
        build_agency_document_transferred_separately_message("Приглашение"),
        build_client_uploaded_notification(public_number, "Загранпаспорт", doc_label),
        build_case_submitted_notification(
            case_id=case.id,
            telegram_id=case.telegram_id,
            username="pilotclient",
            applicants_count=1,
            country_name="Италия",
            city="Москва",
            provider="Italy visa center / provider to verify",
            travel_purpose="Туризм",
            case_status=status_label,
        ),
        build_profiles_completed_notification(
            telegram_id=case.telegram_id,
            username="pilotclient",
            applicants_count=1,
            case_status=status_label,
        ),
        build_slot_options_sent_to_manager(case.id, 2),
        build_slot_options_message(),
        build_slot_selected_notification(
            case_id=case.id,
            telegram_id=case.telegram_id,
            username="pilotclient",
            option_date="2026-07-15",
            option_time="10:30",
            city="Москва",
            provider="VMS Italy",
        ),
        build_user_case_submitted_message(),
        build_user_slot_selected_message("2026-07-15", "10:30"),
        build_appointment_confirmed_message("2026-07-15", "10:30", "Москва", "VMS Italy"),
    ]

    for text in notifications:
        _assert_no_forbidden(text)

    assert public_number in notifications[3]
    assert "Италия" in notifications[4]
    assert "2026-07-15" in notifications[8]
