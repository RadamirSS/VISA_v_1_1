from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bot.api import main as api_main
from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.case_status import UNKNOWN_STATUS_LABEL, build_case_timeline, case_status_label


def build_client(tmp_path: Path, *, with_access: bool = True, with_case: bool = True) -> tuple[TestClient, str]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'case-timeline.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    api_main._container = api_main.Container(
        settings=api_main.Settings(
            bot_token="",
            bot_admin_ids=[],
            database_url=database_url,
            client_miniapp_url="http://localhost:3001",
            miniapp_bot_token="",
            miniapp_allowed_origin="http://localhost:3001",
            miniapp_dev_auth=True,
            repo_root=repo_root,
            root_dir=repo_root / "apps" / "telegram-bot",
        ),
        users=UserRepository(database_url),
        access_keys=AccessKeyRepository(database_url),
        miniapp=MiniAppRepository(database_url, repo_root=repo_root),
    )
    container = api_main.get_container()
    user = container.users.upsert_from_telegram(7100, "timelineuser", "Time", "Line")
    if with_access:
        key = new_access_key("TIMELINE-KEY", 1, "miniapp", [], 2, None, None)
        container.access_keys.save(key)
        container.access_keys.bind_and_activate(key.code, user.id, user.telegram_id)
        if with_case:
            container.miniapp.create_case(user, key.id, key.code)
    return TestClient(api_main.app), str(user.telegram_id)


def _step_state(steps: list[dict[str, str]], key: str) -> str:
    return next(item["state"] for item in steps if item["key"] == key)


def test_profiles_in_progress_maps_correctly() -> None:
    steps = build_case_timeline(VisaCaseStatus.PROFILES_IN_PROGRESS.value, access_active=True, applicants_completed=False)
    assert _step_state(steps, "profiles") == "current"
    assert _step_state(steps, "access") == "done"


def test_submitted_for_manager_review_maps_correctly() -> None:
    steps = build_case_timeline(VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value, access_active=True, applicants_completed=True)
    assert _step_state(steps, "submitted") == "current"
    assert _step_state(steps, "profiles") == "done"


def test_slot_options_sent_maps_correctly() -> None:
    steps = build_case_timeline(VisaCaseStatus.SLOT_OPTIONS_SENT.value, access_active=True, applicants_completed=True)
    assert _step_state(steps, "slot_options") == "current"


def test_slot_selected_by_client_maps_correctly() -> None:
    steps = build_case_timeline(VisaCaseStatus.SLOT_SELECTED_BY_CLIENT.value, access_active=True, applicants_completed=True)
    assert _step_state(steps, "slot_selected") == "current"


def test_appointment_confirmed_maps_correctly() -> None:
    steps = build_case_timeline(VisaCaseStatus.APPOINTMENT_CONFIRMED.value, access_active=True, applicants_completed=True)
    assert _step_state(steps, "confirmed") == "current"
    assert _step_state(steps, "confirmation") == "done"


def test_cancelled_maps_warning_state() -> None:
    steps = build_case_timeline(VisaCaseStatus.CANCELLED.value, access_active=True, applicants_completed=True)
    warning_steps = [item for item in steps if item["state"] == "warning"]
    assert warning_steps
    assert _step_state(steps, "access") == "done"


def test_timeline_api_returns_human_status_label(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path)
    container = api_main.get_container()
    case = container.miniapp.get_case_for_telegram_user(int(telegram_id))
    case.status = VisaCaseStatus.SLOT_OPTIONS_SENT.value
    container.miniapp.save_case(case)

    response = client.get("/api/case/current/timeline", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == VisaCaseStatus.SLOT_OPTIONS_SENT.value
    assert payload["status_label"] == case_status_label(VisaCaseStatus.SLOT_OPTIONS_SENT.value)
    assert payload["status_label"] != payload["status"]
    assert payload["status_label"] != UNKNOWN_STATUS_LABEL


def test_timeline_api_requires_access_key(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path, with_access=False)

    response = client.get("/api/case/current/timeline", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 403


def test_timeline_api_returns_404_without_case(tmp_path: Path) -> None:
    client, telegram_id = build_client(tmp_path, with_case=False)

    response = client.get("/api/case/current/timeline", headers={"X-Dev-Telegram-Id": telegram_id})

    assert response.status_code == 404
