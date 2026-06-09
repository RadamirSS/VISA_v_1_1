from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import SupportRequest, SupportRequestStatus


class SupportRequestRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, user_id: str, telegram_id: int, username: str | None, message: str | None) -> SupportRequest:
        now = datetime.now(UTC).isoformat()
        request = SupportRequest(
            id=f"SR-{uuid4().hex[:8].upper()}",
            user_id=user_id,
            telegram_id=telegram_id,
            username=username,
            message=message,
            status=SupportRequestStatus.OPEN.value,
            created_at=now,
            updated_at=now,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO support_requests (
                  id, user_id, telegram_id, username, message, status, created_at, updated_at
                ) VALUES (
                  :id, :user_id, :telegram_id, :username, :message, :status, :created_at, :updated_at
                )
                """,
                asdict(request),
            )
            connection.commit()
        return request

    def list_open(self, limit: int = 20) -> list[SupportRequest]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM support_requests WHERE status IN (?, ?) ORDER BY created_at DESC LIMIT ?",
                (SupportRequestStatus.OPEN.value, SupportRequestStatus.IN_PROGRESS.value, limit),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, request_id: str) -> SupportRequest | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM support_requests WHERE id = ?", (request_id,)).fetchone()
        return self._from_row(row) if row else None

    def update_status(self, request_id: str, status: str) -> SupportRequest | None:
        existing = self.get(request_id)
        if existing is None:
            return None
        existing.status = status
        existing.updated_at = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                "UPDATE support_requests SET status = ?, updated_at = ? WHERE id = ?",
                (existing.status, existing.updated_at, request_id),
            )
            connection.commit()
        return existing

    def _from_row(self, row: sqlite3.Row) -> SupportRequest:
        return SupportRequest(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            message=row["message"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
