from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import AccessKey, AccessKeyStatus


class AccessKeyRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def save(self, access_key: AccessKey) -> None:
        payload = asdict(access_key)
        payload["country_codes"] = json.dumps(payload["country_codes"], ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO access_keys (
                  id, code, status, max_uses, used_count, bound_user_id, bound_telegram_id,
                  country_codes, service_type, max_applicants, expires_at, created_by_admin_id,
                  created_at, updated_at, note
                ) VALUES (
                  :id, :code, :status, :max_uses, :used_count, :bound_user_id, :bound_telegram_id,
                  :country_codes, :service_type, :max_applicants, :expires_at, :created_by_admin_id,
                  :created_at, :updated_at, :note
                )
                ON CONFLICT(code) DO UPDATE SET
                  status = excluded.status,
                  max_uses = excluded.max_uses,
                  used_count = excluded.used_count,
                  bound_user_id = excluded.bound_user_id,
                  bound_telegram_id = excluded.bound_telegram_id,
                  country_codes = excluded.country_codes,
                  service_type = excluded.service_type,
                  max_applicants = excluded.max_applicants,
                  expires_at = excluded.expires_at,
                  updated_at = excluded.updated_at,
                  note = excluded.note
                """,
                payload,
            )
            connection.commit()

    def get_by_code(self, code: str) -> AccessKey | None:
        normalized = code.strip().upper()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM access_keys WHERE UPPER(code) = ?", (normalized,)).fetchone()
        return self._from_row(row)

    def list_recent(self, limit: int = 20) -> list[AccessKey]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM access_keys ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._from_row(row) for row in rows if row is not None]

    def list_for_telegram_user(self, telegram_id: int) -> list[AccessKey]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM access_keys WHERE bound_telegram_id = ? ORDER BY created_at DESC",
                (telegram_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows if row is not None]

    def get_active_for_telegram_user(self, telegram_id: int) -> AccessKey | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM access_keys
                WHERE bound_telegram_id = ?
                  AND status IN (?, ?)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (telegram_id, AccessKeyStatus.ACTIVE.value, AccessKeyStatus.ACTIVATED.value),
            ).fetchone()
        return self._from_row(row)

    def bind_and_activate(self, code: str, user_id: str, telegram_id: int) -> AccessKey | None:
        access_key = self.get_by_code(code)
        if access_key is None:
            return None
        access_key.bound_user_id = access_key.bound_user_id or user_id
        access_key.bound_telegram_id = access_key.bound_telegram_id or telegram_id
        access_key.status = AccessKeyStatus.ACTIVATED.value
        access_key.updated_at = datetime.now(UTC).isoformat()
        self.save(access_key)
        return access_key

    def consume_for_order(self, access_key_id: str, order_id: str) -> AccessKey | None:
        del order_id
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM access_keys WHERE id = ?", (access_key_id,)).fetchone()
            if row is None:
                return None
            access_key = self._from_row(row)
            access_key.used_count += 1
            access_key.updated_at = datetime.now(UTC).isoformat()
            if access_key.used_count >= access_key.max_uses:
                access_key.status = AccessKeyStatus.CONSUMED.value
            elif access_key.status == AccessKeyStatus.ACTIVE.value:
                access_key.status = AccessKeyStatus.ACTIVATED.value
            self.save(access_key)
            return access_key

    def revoke(self, code: str) -> AccessKey | None:
        access_key = self.get_by_code(code)
        if access_key is None:
            return None
        access_key.status = AccessKeyStatus.REVOKED.value
        access_key.updated_at = datetime.now(UTC).isoformat()
        self.save(access_key)
        return access_key

    def _from_row(self, row: sqlite3.Row | None) -> AccessKey | None:
        if row is None:
            return None
        return AccessKey(
            id=row["id"],
            code=row["code"],
            status=row["status"],
            max_uses=row["max_uses"],
            used_count=row["used_count"],
            bound_user_id=row["bound_user_id"],
            bound_telegram_id=row["bound_telegram_id"],
            country_codes=json.loads(row["country_codes"]) if row["country_codes"] else [],
            service_type=row["service_type"],
            max_applicants=row["max_applicants"],
            expires_at=row["expires_at"],
            created_by_admin_id=row["created_by_admin_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            note=row["note"],
        )


def new_access_key(
    code: str,
    created_by_admin_id: int,
    service_type: str,
    country_codes: list[str],
    max_applicants: int | None,
    expires_at: str | None,
    note: str | None,
    max_uses: int = 1,
) -> AccessKey:
    now = datetime.now(UTC).isoformat()
    return AccessKey(
        id=str(uuid4()),
        code=code.strip().upper(),
        status=AccessKeyStatus.ACTIVE.value,
        max_uses=max_uses,
        used_count=0,
        bound_user_id=None,
        bound_telegram_id=None,
        country_codes=country_codes,
        service_type=service_type,
        max_applicants=max_applicants,
        expires_at=expires_at,
        created_by_admin_id=created_by_admin_id,
        created_at=now,
        updated_at=now,
        note=note,
    )
