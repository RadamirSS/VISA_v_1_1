from __future__ import annotations

from pathlib import Path

import pytest

from bot.database import init_db
from bot.models import AppointmentSlotOptionStatus, VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.slot_offers import ParsedSlotOption


def build_repo(tmp_path: Path) -> tuple[MiniAppRepository, str]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'slot-offers.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    repo = MiniAppRepository(database_url, repo_root=repo_root)
    user = users.upsert_from_telegram(9100, "slotuser", "Slot", "User")
    key = new_access_key("SLOT-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = repo.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    repo.save_case(case)
    return repo, case.id


def test_create_offer_and_options_and_list(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    offer, options, visa_case = repo.create_slot_offer(
        case_id,
        1,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30"), ParsedSlotOption(option_date="2026-07-16", option_time="14:00")],
    )

    grouped = repo.list_slot_offers_for_case(case_id)

    assert offer.id
    assert len(options) == 2
    assert grouped[0][0].id == offer.id
    assert visa_case.status == VisaCaseStatus.SLOT_OPTIONS_SENT.value


def test_select_option_marks_case_fields_and_confirm(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    offer, options, _ = repo.create_slot_offer(
        case_id,
        1,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30"), ParsedSlotOption(option_date="2026-07-16", option_time="14:00")],
    )
    case = repo.get_case_by_any_id(case_id)
    assert case is not None

    updated_case, selected = repo.select_slot_option_for_user(case.telegram_id, options[0].id)
    confirmed = repo.confirm_appointment(case_id, 1)

    assert selected.status == AppointmentSlotOptionStatus.SELECTED.value
    assert updated_case.selected_slot_option_id == options[0].id
    assert confirmed.status == VisaCaseStatus.APPOINTMENT_CONFIRMED.value


def test_prevent_selecting_option_for_another_user(tmp_path: Path) -> None:
    repo, case_id = build_repo(tmp_path)
    _, options, _ = repo.create_slot_offer(
        case_id,
        1,
        [ParsedSlotOption(option_date="2026-07-15", option_time="10:30")],
    )

    with pytest.raises(ValueError):
        repo.select_slot_option_for_user(9999, options[0].id)
