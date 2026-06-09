from __future__ import annotations

from pathlib import Path

from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.slot_offers import ParsedSlotOption


def build_repo(tmp_path: Path) -> tuple[MiniAppRepository, int, str]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'case-slot-status.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    repo = MiniAppRepository(database_url, repo_root=repo_root)
    user = users.upsert_from_telegram(9200, "statususer", "Status", "User")
    key = new_access_key("STATUS-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = repo.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    repo.save_case(case)
    return repo, user.telegram_id, case.id


def test_sending_offers_updates_case_status(tmp_path: Path) -> None:
    repo, _, case_id = build_repo(tmp_path)
    _, _, visa_case = repo.create_slot_offer(case_id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])

    assert visa_case.status == VisaCaseStatus.SLOT_OPTIONS_SENT.value


def test_selecting_option_updates_case_status(tmp_path: Path) -> None:
    repo, telegram_id, case_id = build_repo(tmp_path)
    _, options, _ = repo.create_slot_offer(case_id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])

    visa_case, _ = repo.select_slot_option_for_user(telegram_id, options[0].id)

    assert visa_case.status == VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value


def test_confirming_appointment_updates_case_status(tmp_path: Path) -> None:
    repo, telegram_id, case_id = build_repo(tmp_path)
    _, options, _ = repo.create_slot_offer(case_id, 1, [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")])
    repo.select_slot_option_for_user(telegram_id, options[0].id)

    visa_case = repo.confirm_appointment(case_id, 1)

    assert visa_case.status == VisaCaseStatus.APPOINTMENT_CONFIRMED.value
