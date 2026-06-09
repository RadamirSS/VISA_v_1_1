from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from bot.database import init_db
from bot.models import ClientDocumentStatus, DocumentCategory, VisaCase, VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.document_status import get_manager_queue_document_counts
from bot.services.manager_case_actions import (
    MAX_MANAGER_QUEUE_ITEMS,
    ManagerCaseQueueItem,
    QUEUE_ITEMS_LIMIT_MESSAGE,
    build_manager_queue_view,
    queue_text_contains_raw_status,
    select_actionable_queue_items,
)
from bot.services.manager_case_view import render_queue_item


def build_queue_items(tmp_path: Path, count: int) -> list[ManagerCaseQueueItem]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'queue-limits.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    user = users.upsert_from_telegram(9900, "queue", "Queue", "User")
    key = new_access_key("QUEUE-KEY", 1, "miniapp", [], count, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    items: list[ManagerCaseQueueItem] = []
    now = datetime.now(UTC).isoformat()
    for index in range(count):
        case = VisaCase(
            id=str(uuid4()),
            user_id=user.id,
            telegram_id=user.telegram_id,
            status=VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value,
            applicants_count=1,
            submitted_at=f"2026-06-{index + 1:02d}T10:00:00+00:00",
            created_at=now,
            updated_at=now,
        )
        miniapp.save_case(case)
        items.append(ManagerCaseQueueItem(visa_case=case, username="queue"))
    return items


def test_queue_limit_returns_only_first_ten_actionable_items(tmp_path: Path) -> None:
    items = build_queue_items(tmp_path, 12)
    actionable, has_more = select_actionable_queue_items(items)
    assert len(actionable) == MAX_MANAGER_QUEUE_ITEMS
    assert has_more is True


def test_back_queue_helper_uses_same_rendering_as_main_queue(tmp_path: Path) -> None:
    items = build_queue_items(tmp_path, 3)
    queue_view = build_manager_queue_view(items)
    assert "Новые на проверку" in queue_view.summary_text
    assert len(queue_view.actionable_items) == 3
    assert queue_view.has_more_items is False
    assert QUEUE_ITEMS_LIMIT_MESSAGE not in queue_view.summary_text


def test_queue_limit_message_appears_when_more_than_ten_cases(tmp_path: Path) -> None:
    items = build_queue_items(tmp_path, 11)
    queue_view = build_manager_queue_view(items)
    assert queue_view.has_more_items is True
    assert QUEUE_ITEMS_LIMIT_MESSAGE in queue_view.summary_text
    assert len(queue_view.actionable_items) == MAX_MANAGER_QUEUE_ITEMS


def test_queue_item_rendering_uses_human_labels_not_raw_codes(tmp_path: Path) -> None:
    items = build_queue_items(tmp_path, 1)
    text = render_queue_item(items[0].visa_case)
    assert "Заявка отправлена менеджеру" in text
    assert queue_text_contains_raw_status(text) is False


def test_queue_summary_includes_docs_under_review_group(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'queue-docs-review.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    documents = DocumentRepository(database_url)
    user = users.upsert_from_telegram(9910, "docsqueue", "Docs", "Queue")
    key = new_access_key("DOCQ-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.MANAGER_REVIEWING.value
    miniapp.save_case(case)
    uploaded = documents.create_client_request(case.id, DocumentCategory.PHOTO.value, admin_id=1)
    documents.update_status(uploaded.id, ClientDocumentStatus.UPLOADED_BY_CLIENT.value)
    counts = documents.count_summary(case.id)
    client_pending, client_under_review = get_manager_queue_document_counts(counts)
    queue_item = ManagerCaseQueueItem(
        visa_case=case,
        username="docsqueue",
        client_pending=client_pending,
        client_under_review=client_under_review,
    )
    queue_view = build_manager_queue_view([queue_item])
    assert client_under_review == 1
    assert "Документы на проверке" in queue_view.summary_text
