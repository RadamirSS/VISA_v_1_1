from __future__ import annotations

from pathlib import Path

import pytest

from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.manager_case_actions import get_allowed_statuses_for_case, validate_status_transition
from bot.services.manager_case_view import manager_case_status_label
from bot.services.slot_offers import ParsedSlotOption


def build_repo(tmp_path: Path) -> tuple[MiniAppRepository, str]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'admin-case-status.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    repo = MiniAppRepository(database_url, repo_root=repo_root)
    user = users.upsert_from_telegram(9800, "status", "Status", "User")
    key = new_access_key("STAT-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = repo.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    repo.save_case(case)
    return repo, case.id


def test_cannot_confirm_appointment_without_selected_slot(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    visa_case = repo.get_case_by_any_id(case_id)
    assert visa_case is not None
    error = validate_status_transition(
        visa_case,
        VisaCaseStatus.APPOINTMENT_CONFIRMED.value,
        has_slot_options=False,
        has_selected_slot=False,
    )
    assert error is not None
    with pytest.raises(ValueError):
        repo.confirm_appointment(case_id, 1)


def test_cannot_mark_slot_options_sent_without_options(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    visa_case = repo.get_case_by_any_id(case_id)
    assert visa_case is not None
    error = validate_status_transition(
        visa_case,
        VisaCaseStatus.SLOT_OPTIONS_SENT.value,
        has_slot_options=False,
        has_selected_slot=False,
    )
    assert error is not None


def test_can_mark_manager_reviewing(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    updated = repo.update_manager_case_status(case_id, VisaCaseStatus.MANAGER_REVIEWING.value, 1)
    assert updated.status == VisaCaseStatus.MANAGER_REVIEWING.value
    assert updated.manager_reviewed_at is not None


def test_can_mark_needs_clarification(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    updated = repo.update_manager_case_status(case_id, VisaCaseStatus.NEEDS_CLARIFICATION.value, 1)
    assert updated.status == VisaCaseStatus.NEEDS_CLARIFICATION.value


def test_cancelled_and_closed_produce_safe_labels(tmp_path: Path) -> None:
    assert manager_case_status_label(VisaCaseStatus.CANCELLED.value) == "Заявка отменена"
    assert manager_case_status_label(VisaCaseStatus.CLOSED.value) == "Заявка закрыта"


def test_slot_options_sent_allowed_after_offer_created(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    repo.create_slot_offer(case_id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])
    visa_case = repo.get_case_by_any_id(case_id)
    assert visa_case is not None
    allowed = get_allowed_statuses_for_case(
        visa_case,
        has_slot_options=repo.has_slot_offers(case_id),
        has_selected_slot=repo.has_selected_slot(visa_case),
    )
    allowed_values = {value for value, _ in allowed}
    assert VisaCaseStatus.SLOT_OPTIONS_SENT.value in allowed_values
