#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.database import init_db
from bot.models import DocumentCategory, VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.slot_offers import ParsedSlotOption


def main() -> int:
    repo_root = ROOT.parents[1]
    with tempfile.TemporaryDirectory(prefix="pilot-smoke-") as temp_dir:
        database_url = f"sqlite+aiosqlite:///{Path(temp_dir) / 'pilot_smoke.db'}"
        init_db(database_url)

        users = UserRepository(database_url)
        keys = AccessKeyRepository(database_url)
        miniapp = MiniAppRepository(database_url, repo_root=repo_root)
        documents = DocumentRepository(database_url)

        user = users.upsert_from_telegram(88001, "smokeuser", "Smoke", "User")
        key = new_access_key("SMOKE-KEY", 1, "miniapp", [], 2, None, None)
        keys.save(key)
        keys.bind_and_activate(key.code, user.id, user.telegram_id)

        case = miniapp.create_case(user, key.id, key.code)
        case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
        case.desired_country_name_ru = "Италия"
        case.preferred_submission_city = "Москва"
        case.submission_provider = "Italy visa center / provider to verify"
        miniapp.save_case(case)

        documents.create_client_request(case.id, DocumentCategory.PHOTO.value, admin_id=1)
        documents.create_agency_item(case.id, DocumentCategory.HOTEL_BOOKING.value, admin_id=1)
        miniapp.create_slot_offer(
            case.id,
            1,
            [
                ParsedSlotOption(option_date="2026-08-01", option_time="10:00"),
                ParsedSlotOption(option_date="2026-08-02", option_time="11:00"),
            ],
        )

    print("PILOT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
