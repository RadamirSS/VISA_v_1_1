from __future__ import annotations

from pathlib import Path

from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.models import DocumentCategory
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.manager_case_view import render_document_summary_for_manager
from bot.services.manager_case_actions import (
    ManagerCaseQueueItem,
    build_manager_queue_groups,
    get_allowed_statuses_for_case,
    get_case_template_text,
    is_terminal_case_status,
)


def build_case(tmp_path: Path, status: str):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'manager-case-actions.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    user = users.upsert_from_telegram(9600, "actions", "Actions", "User")
    key = new_access_key("ACT-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    case.status = status
    miniapp.save_case(case)
    return miniapp, case


def test_queue_groups_assign_cases_by_stage(tmp_path: Path) -> None:
    _, review_case = build_case(tmp_path, VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value)
    _, docs_case = build_case(tmp_path, VisaCaseStatus.MANAGER_REVIEWING.value)
    _, slot_case = build_case(tmp_path, VisaCaseStatus.READY_FOR_SLOT_SEARCH.value)

    groups = build_manager_queue_groups(
        [
            ManagerCaseQueueItem(visa_case=review_case, username="a"),
            ManagerCaseQueueItem(visa_case=docs_case, username="b", client_pending=2),
            ManagerCaseQueueItem(visa_case=slot_case, username="c"),
        ]
    )
    by_key = {group.key: group for group in groups}

    assert review_case.id in {item.visa_case.id for item in by_key["new_review"].items}
    assert docs_case.id in {item.visa_case.id for item in by_key["needs_documents"].items}
    assert docs_case.id in {item.visa_case.id for item in by_key["awaiting_client_docs"].items}
    assert slot_case.id in {item.visa_case.id for item in by_key["slot_search"].items}


def test_case_templates_are_safe() -> None:
    text = get_case_template_text("reviewing", "VISA-CASE-2026-000123").lower()
    assert "visa-case-2026-000123" in text
    assert "passport" not in text
    assert "адрес" not in text


def test_allowed_statuses_exclude_invalid_slot_options_sent(tmp_path: Path) -> None:
    _, case = build_case(tmp_path, VisaCaseStatus.MANAGER_REVIEWING.value)
    allowed = get_allowed_statuses_for_case(case, has_slot_options=False, has_selected_slot=False)
    allowed_values = {value for value, _ in allowed}
    assert VisaCaseStatus.SLOT_OPTIONS_SENT.value not in allowed_values
    assert VisaCaseStatus.MANAGER_REVIEWING.value in allowed_values


def test_document_summary_counts_client_and_agency_separately(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'manager-doc-summary.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    documents = DocumentRepository(database_url)
    user = users.upsert_from_telegram(9650, "docs", "Docs", "User")
    key = new_access_key("DOC-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    documents.create_client_request(case.id, DocumentCategory.PHOTO.value, admin_id=1)
    documents.create_agency_item(case.id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
    counts = documents.count_summary(case.id)
    text = render_document_summary_for_manager(counts)
    assert "Документы от клиента" in text
    assert "Документы агентства" in text
    assert int(counts["client_pending"]) == 1
    assert int(counts["agency_in_progress"]) == 1


def test_terminal_statuses_hide_active_actions(tmp_path: Path) -> None:
    _, case = build_case(tmp_path, VisaCaseStatus.CANCELLED.value)
    assert is_terminal_case_status(case.status)
    allowed = get_allowed_statuses_for_case(case, has_slot_options=True, has_selected_slot=True)
    allowed_values = {value for value, _ in allowed}
    assert VisaCaseStatus.MANAGER_REVIEWING.value not in allowed_values
    assert VisaCaseStatus.CLOSED.value in allowed_values
