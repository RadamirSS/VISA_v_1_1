from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import User


class UserRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            patronymic=row["patronymic"],
            birth_date=row["birth_date"],
            citizenship=row["citizenship"],
            current_location=row["current_location"],
            phone=row["phone"],
            email=row["email"],
            consent_accepted_at=row["consent_accepted_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def upsert_from_telegram(self, telegram_id: int, username: str | None, first_name: str | None, last_name: str | None) -> User:
        existing = self.get_by_telegram_id(telegram_id)
        now = datetime.now(UTC).isoformat()
        if existing is not None:
            existing.username = username or existing.username
            existing.first_name = first_name or existing.first_name
            existing.last_name = last_name or existing.last_name
            existing.updated_at = now
            self.save(existing)
            return existing

        user = User(
            id=str(uuid4()),
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=now,
            updated_at=now,
        )
        self.save(user)
        return user

    def save(self, user: User) -> None:
        payload = asdict(user)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (
                  id, telegram_id, username, first_name, last_name, patronymic, birth_date,
                  citizenship, current_location, phone, email, consent_accepted_at, created_at, updated_at
                ) VALUES (
                  :id, :telegram_id, :username, :first_name, :last_name, :patronymic, :birth_date,
                  :citizenship, :current_location, :phone, :email, :consent_accepted_at, :created_at, :updated_at
                )
                ON CONFLICT(telegram_id) DO UPDATE SET
                  username = excluded.username,
                  first_name = excluded.first_name,
                  last_name = excluded.last_name,
                  patronymic = excluded.patronymic,
                  birth_date = excluded.birth_date,
                  citizenship = excluded.citizenship,
                  current_location = excluded.current_location,
                  phone = excluded.phone,
                  email = excluded.email,
                  consent_accepted_at = excluded.consent_accepted_at,
                  updated_at = excluded.updated_at
                """,
                payload,
            )
            connection.commit()

    def mark_consent(self, telegram_id: int, username: str | None, first_name: str | None, last_name: str | None) -> User:
        user = self.upsert_from_telegram(telegram_id, username, first_name, last_name)
        user.consent_accepted_at = datetime.now(UTC).isoformat()
        user.updated_at = datetime.now(UTC).isoformat()
        self.save(user)
        return user

    def is_registered(self, user: User | None) -> bool:
        if user is None or not user.consent_accepted_at:
            return False
        required = [user.last_name, user.first_name, user.birth_date, user.citizenship, user.current_location, user.phone]
        return all(value and str(value).strip() for value in required)
