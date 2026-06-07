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
