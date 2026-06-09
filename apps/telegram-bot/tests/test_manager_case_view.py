from __future__ import annotations

from pathlib import Path

from bot.database import init_db
from bot.models import (
    AgencyDocumentStatus,
    ApplicantProfile,
    ApplicantProfileStatus,
    ClientDocumentStatus,
    DocumentCategory,
    DocumentSourceType,
    VisaCase,
    VisaCaseStatus,
)
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.manager_case_view import (
    SENSITIVE_SUBSTRINGS,
    render_applicants_summary,
    render_manager_case_summary,
)


def build_context(tmp_path: Path) -> tuple[VisaCase, list[ApplicantProfile], dict]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'manager-case-view.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    documents = DocumentRepository(database_url)
    user = users.upsert_from_telegram(9500, "caseview", "Case", "View")
    key = new_access_key("VIEW-KEY", 1, "miniapp", [], 3, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.MANAGER_REVIEWING.value
    case.desired_country_name_ru = "Италия"
    case.preferred_submission_city = "Москва"
    case.submission_provider = "VMS Italy"
    case.travel_purpose = "Туризм"
    case.applicants_count = 2
    miniapp.save_case(case)
    applicants = [
        ApplicantProfile(
            id="app-1",
            user_id=user.id,
            telegram_id=user.telegram_id,
            case_id=case.id,
            position=1,
            role="primary",
            status=ApplicantProfileStatus.COMPLETED.value,
            completion_percent=100,
            last_name_cyrillic="Иванов",
            first_name_cyrillic="Иван",
            birth_place="Москва",
            residence_address="ул. Пример, 1",
            passport_number="123456789",
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        ),
        ApplicantProfile(
            id="app-2",
            user_id=user.id,
            telegram_id=user.telegram_id,
            case_id=case.id,
            position=2,
            role="child",
            status=ApplicantProfileStatus.DRAFT.value,
            completion_percent=72,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    client_pending = documents.create_client_request(case.id, DocumentCategory.PHOTO.value, admin_id=1)
    documents.update_status(client_pending.id, ClientDocumentStatus.REQUESTED.value)
    client_review = documents.create_client_request(case.id, DocumentCategory.INTERNATIONAL_PASSPORT.value, admin_id=1)
    documents.update_status(client_review.id, ClientDocumentStatus.UPLOADED_BY_CLIENT.value)
    agency_item = documents.create_agency_item(case.id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
    documents.update_status(agency_item.id, AgencyDocumentStatus.PREPARING_BY_AGENCY.value)
    agency_ready = documents.create_agency_item(case.id, DocumentCategory.COVER_LETTER.value, admin_id=1)
    (tmp_path / "cover-letter.pdf").write_bytes(b"%PDF-1.4")
    documents.save_file_metadata(
        document_item_id=agency_ready.id,
        case_id=case.id,
        uploaded_by="admin:1",
        original_filename="cover-letter.pdf",
        storage_path=str(tmp_path / "cover-letter.pdf"),
        mime_type="application/pdf",
        size_bytes=10,
    )
    documents.update_status(agency_ready.id, AgencyDocumentStatus.READY_FOR_CLIENT.value)
    doc_counts = documents.count_summary(case.id)
    return case, applicants, doc_counts


def test_manager_case_summary_includes_required_fields(tmp_path: Path) -> None:
    case, applicants, doc_counts = build_context(tmp_path)
    text = render_manager_case_summary(case, username="caseview", applicants=applicants, doc_counts=doc_counts)

    assert "VISA-CASE-" in text
    assert case.id in text
    assert "@caseview" in text
    assert "Италия" in text
    assert "Москва" in text
    assert "VMS Italy" in text
    assert "Туризм" in text
    assert "Анкеты: 1/2 заполнено" in text
    assert "1 ожидают / 1 на проверке" in text
    assert "1 в работе / 1 готов" in text
    assert "Менеджер проверяет данные" in text


def test_manager_case_summary_excludes_sensitive_fields(tmp_path: Path) -> None:
    case, applicants, doc_counts = build_context(tmp_path)
    text = render_manager_case_summary(case, username="caseview", applicants=applicants, doc_counts=doc_counts).lower()

    assert "123456789" not in text
    assert "passport" not in text
    assert "место рождения" not in text
    assert "адрес" not in text
    assert "storage_path" not in text
    for marker in SENSITIVE_SUBSTRINGS:
        if marker.isdigit() or "." in marker:
            continue
        assert marker.replace("_", " ") not in text or marker == "passport.pdf"


def test_applicants_summary_lists_completion_without_sensitive_fields(tmp_path: Path) -> None:
    _, applicants, _ = build_context(tmp_path)
    text = render_applicants_summary(applicants)

    assert "Заявители: 2" in text
    assert "Иванов Иван" in text
    assert "100%" in text
    assert "72%" in text
    assert "123456789" not in text
    assert "ул. Пример" not in text
