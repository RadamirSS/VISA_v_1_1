from __future__ import annotations

from pathlib import Path

from bot.database import init_db
from bot.models import SupportRequestStatus
from bot.repositories.support_requests import SupportRequestRepository


def test_create_list_and_update_support_request(tmp_path: Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'support.db'}"
    init_db(db_url)
    repository = SupportRequestRepository(db_url)
    request = repository.create(
        user_id="user-1",
        telegram_id=111,
        username="tester",
        message="Нужна связь с менеджером",
    )
    open_requests = repository.list_open()
    assert len(open_requests) == 1
    assert open_requests[0].id == request.id
    updated = repository.update_status(request.id, SupportRequestStatus.IN_PROGRESS.value)
    assert updated is not None
    assert updated.status == SupportRequestStatus.IN_PROGRESS.value
