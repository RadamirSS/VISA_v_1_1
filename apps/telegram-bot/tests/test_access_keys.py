from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from bot.database import init_db
from bot.models import AccessKeyStatus, User
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.users import UserRepository
from bot.services.access_keys import validate_access_key


def test_create_and_validate_active_access_key(tmp_path: Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'access_keys.db'}"
    init_db(db_url)
    repository = AccessKeyRepository(db_url)
    access_key = new_access_key(
        code="VISA-ABCD-1234",
        created_by_admin_id=1,
        service_type="appointment_request",
        country_codes=["IT"],
        max_applicants=2,
        expires_at=(datetime.now(UTC) + timedelta(days=7)).isoformat(),
        note=None,
    )
    repository.save(access_key)
    loaded = repository.get_by_code("visa-abcd-1234")
    assert loaded is not None
    result = validate_access_key(loaded, telegram_id=111, country_code="IT", applicants_count=2, service_type="appointment_request")
    assert result.valid is True


def test_reject_expired_and_revoked_access_keys(tmp_path: Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'access_keys.db'}"
    init_db(db_url)
    repository = AccessKeyRepository(db_url)
    expired = new_access_key(
        code="VISA-EXPIRED-1",
        created_by_admin_id=1,
        service_type="appointment_request",
        country_codes=[],
        max_applicants=None,
        expires_at=(datetime.now(UTC) - timedelta(days=1)).isoformat(),
        note=None,
    )
    revoked = new_access_key(
        code="VISA-REVOKED-1",
        created_by_admin_id=1,
        service_type="appointment_request",
        country_codes=[],
        max_applicants=None,
        expires_at=None,
        note=None,
    )
    revoked.status = AccessKeyStatus.REVOKED.value
    repository.save(expired)
    repository.save(revoked)
    assert validate_access_key(repository.get_by_code(expired.code), telegram_id=111).valid is False
    assert validate_access_key(repository.get_by_code(revoked.code), telegram_id=111).valid is False


def test_bind_and_reject_other_user_and_consume(tmp_path: Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'access_keys.db'}"
    init_db(db_url)
    users = UserRepository(db_url)
    repository = AccessKeyRepository(db_url)
    user = User(id="user-1", telegram_id=111, created_at=datetime.now(UTC).isoformat(), updated_at=datetime.now(UTC).isoformat())
    users.save(user)
    access_key = new_access_key(
        code="VISA-ONE-0001",
        created_by_admin_id=1,
        service_type="appointment_request",
        country_codes=[],
        max_applicants=1,
        expires_at=None,
        note=None,
    )
    repository.save(access_key)
    bound = repository.bind_and_activate(access_key.code, user.id, user.telegram_id)
    assert bound is not None
    assert bound.bound_telegram_id == 111
    assert validate_access_key(repository.get_by_code(access_key.code), telegram_id=222).valid is False
    consumed = repository.consume_for_order(bound.id, "order-1")
    assert consumed is not None
    assert consumed.used_count == 1
    assert consumed.status == AccessKeyStatus.CONSUMED.value
