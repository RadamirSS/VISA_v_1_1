from __future__ import annotations

from bot.models import VisaCaseStatus
from bot.services.case_status import UNKNOWN_STATUS_LABEL, case_next_action, case_status_label


def test_every_known_case_status_returns_human_label() -> None:
    for status in VisaCaseStatus:
        label = case_status_label(status.value)
        assert label
        assert label != status.value


def test_raw_status_is_not_returned_as_label() -> None:
    for status in VisaCaseStatus:
        assert case_status_label(status.value) != status.value


def test_unknown_status_returns_safe_fallback() -> None:
    assert case_status_label("totally_unknown_status") == UNKNOWN_STATUS_LABEL
    assert case_status_label("totally_unknown_status") != "totally_unknown_status"


def test_case_next_action_for_key_statuses() -> None:
    slot_action = case_next_action(VisaCaseStatus.SLOT_OPTIONS_SENT.value)
    assert slot_action["type"] == "select_slot"
    assert slot_action["href"] == "/appointment"

    no_access = case_next_action("no_access")
    assert no_access["type"] == "enter_access_key"

    no_case = case_next_action("no_case")
    assert no_case["type"] == "create_case"
    assert no_case["href"] == "/case/new"
