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


def test_slot_options_sent_with_available_options_returns_select_slot() -> None:
    action = case_next_action(VisaCaseStatus.SLOT_OPTIONS_SENT.value, has_applicants=True, has_slot_options=True)
    assert action["type"] == "select_slot"
    assert action["href"] == "/appointment"


def test_slot_options_sent_without_available_options_does_not_return_select_slot() -> None:
    action = case_next_action(VisaCaseStatus.SLOT_OPTIONS_SENT.value, has_applicants=True, has_slot_options=False)
    assert action["type"] != "select_slot"
    assert action["type"] == "wait_manager"
    assert action["label"] == "Менеджер подбирает даты"


def test_selected_slot_returns_wait_confirmation() -> None:
    action = case_next_action(
        VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value,
        has_applicants=True,
        has_selected_slot=True,
    )
    assert action["type"] == "wait_confirmation"
    assert action["href"] == "/status"


def test_confirmed_appointment_returns_view_appointment() -> None:
    action = case_next_action(VisaCaseStatus.APPOINTMENT_CONFIRMED.value, has_applicants=True)
    assert action["type"] == "view_appointment"
    assert action["href"] == "/appointment"


def test_no_applicants_points_to_applicants() -> None:
    action = case_next_action(VisaCaseStatus.PROFILES_IN_PROGRESS.value, has_applicants=False)
    assert action["type"] == "fill_profiles"
    assert action["href"] == "/applicants"


def test_no_city_selected_points_to_case() -> None:
    action = case_next_action(
        VisaCaseStatus.PROFILES_COMPLETED.value,
        has_applicants=True,
        has_city_selected=False,
    )
    assert action["type"] == "select_city"
    assert action["href"] == "/case"


def test_case_next_action_for_key_statuses() -> None:
    no_access = case_next_action("no_access")
    assert no_access["type"] == "enter_access_key"

    no_case = case_next_action("no_case")
    assert no_case["type"] == "create_case"
    assert no_case["href"] == "/case/new"
