from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict

from bot.database import sqlite_path_from_url
from bot.models import PromoCode


class PromoRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def save(self, promo: PromoCode) -> None:
        payload = asdict(promo)
        payload["country_codes"] = json.dumps(payload["country_codes"], ensure_ascii=False)
        payload["time_window_codes"] = json.dumps(payload["time_window_codes"], ensure_ascii=False)
        payload["active"] = 1 if payload["active"] else 0
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO promo_codes (
                  id, code, type, value, max_uses, used_count, active, expires_at, created_by_admin_id, created_at, country_codes, time_window_codes, note
                ) VALUES (
                  :id, :code, :type, :value, :max_uses, :used_count, :active, :expires_at, :created_by_admin_id, :created_at, :country_codes, :time_window_codes, :note
                )
                """,
                payload,
            )
            connection.commit()

    def get_by_code(self, code: str) -> PromoCode | None:
        normalized = code.strip().upper()
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM promo_codes WHERE UPPER(code) = ?", (normalized,)).fetchone()
        if row is None:
            return None
        return PromoCode(
            id=row["id"],
            code=row["code"],
            type=row["type"],
            value=row["value"],
            max_uses=row["max_uses"],
            used_count=row["used_count"],
            active=bool(row["active"]),
            expires_at=row["expires_at"],
            created_by_admin_id=row["created_by_admin_id"],
            created_at=row["created_at"],
            country_codes=json.loads(row["country_codes"]) if row["country_codes"] else [],
            time_window_codes=json.loads(row["time_window_codes"]) if row["time_window_codes"] else [],
            note=row["note"],
        )

    def increment_used_count(self, code: str) -> None:
        normalized = code.strip().upper()
        with self._connect() as connection:
            connection.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE UPPER(code) = ?", (normalized,))
            connection.commit()
