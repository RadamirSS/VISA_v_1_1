from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
from pathlib import Path

from bot.database import sqlite_path_from_url
from bot.models import BookingOrder


class OrderRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def next_sequence(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM orders").fetchone()
            return int(row[0]) + 1

    def save(self, order: BookingOrder) -> None:
        payload = asdict(order)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orders (
                  id, public_number, user_id, country_code, country_name_ru, submission_city,
                  provider, visa_purpose, time_window_code, applicants_count, base_price_rub,
                  additional_applicants_price_rub, discount_rub, total_price_rub, promo_code,
                  payment_status, order_status, requires_manager_review, manager_note, user_comment,
                  created_at, updated_at
                ) VALUES (
                  :id, :public_number, :user_id, :country_code, :country_name_ru, :submission_city,
                  :provider, :visa_purpose, :time_window_code, :applicants_count, :base_price_rub,
                  :additional_applicants_price_rub, :discount_rub, :total_price_rub, :promo_code,
                  :payment_status, :order_status, :requires_manager_review, :manager_note, :user_comment,
                  :created_at, :updated_at
                )
                """,
                payload,
            )
            connection.commit()

    def list_recent(self) -> list[dict]:
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT public_number, country_name_ru, submission_city, time_window_code, payment_status, order_status FROM orders ORDER BY created_at DESC LIMIT 10"
            )
            return [
                {
                    "public_number": row[0],
                    "country_name_ru": row[1],
                    "submission_city": row[2],
                    "time_window_code": row[3],
                    "payment_status": row[4],
                    "order_status": row[5],
                }
                for row in cursor.fetchall()
            ]
