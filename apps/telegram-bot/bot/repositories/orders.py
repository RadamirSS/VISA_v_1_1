from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
import json
import sqlite3
from typing import Any
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import Applicant, AuditLog, BookingOrder, OrderStatus, Payment, PaymentStatus


class OrderRepository:
    def __init__(self, database_url: str):
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def next_sequence(self) -> int:
        year = datetime.now(UTC).year
        prefix = f"VISA-{year}-%"
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS cnt FROM orders WHERE public_number LIKE ?", (prefix,)).fetchone()
            return int(row["cnt"]) + 1

    def create_order(self, order: BookingOrder, applicants: list[Applicant], payment: Payment | None, actor_type: str, actor_id: str | None) -> None:
        order_payload = asdict(order)
        payment_payload = asdict(payment) if payment else None
        applicant_payloads = [asdict(applicant) for applicant in applicants]
        audit = AuditLog(
            id=str(uuid4()),
            actor_type=actor_type,
            actor_id=actor_id,
            entity_type="order",
            entity_id=order.id,
            action="create_order",
            before=None,
            after=json.dumps(
                {
                    "order": order_payload,
                    "applicants": applicant_payloads,
                    "payment": payment_payload,
                },
                ensure_ascii=False,
            ),
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orders (
                  id, public_number, user_id, country_code, country_name_ru, submission_city,
                  provider, visa_purpose, time_window_code, applicants_count, base_price_rub,
                  additional_applicants_price_rub, discount_rub, total_price_rub, promo_code, access_key_code, access_key_id,
                  payment_status, order_status, requires_manager_review, manager_note, user_comment,
                  created_at, updated_at
                ) VALUES (
                  :id, :public_number, :user_id, :country_code, :country_name_ru, :submission_city,
                  :provider, :visa_purpose, :time_window_code, :applicants_count, :base_price_rub,
                  :additional_applicants_price_rub, :discount_rub, :total_price_rub, :promo_code, :access_key_code, :access_key_id,
                  :payment_status, :order_status, :requires_manager_review, :manager_note, :user_comment,
                  :created_at, :updated_at
                )
                """,
                order_payload,
            )
            for applicant_payload in applicant_payloads:
                connection.execute(
                    """
                    INSERT INTO applicants (
                      id, order_id, last_name, first_name, patronymic, birth_date, citizenship,
                      current_location, relationship, passport_number_encrypted, passport_expiry_date
                    ) VALUES (
                      :id, :order_id, :last_name, :first_name, :patronymic, :birth_date, :citizenship,
                      :current_location, :relationship, :passport_number_encrypted, :passport_expiry_date
                    )
                    """,
                    applicant_payload,
                )
            if payment_payload is not None:
                connection.execute(
                    """
                    INSERT INTO payments (
                      id, order_id, provider, provider_payment_id, amount_rub, status, created_at, updated_at, paid_at
                    ) VALUES (
                      :id, :order_id, :provider, :provider_payment_id, :amount_rub, :status, :created_at, :updated_at, :paid_at
                    )
                    """,
                    payment_payload,
                )
            connection.execute(
                """
                INSERT INTO audit_log (
                  id, actor_type, actor_id, entity_type, entity_id, action, before, after, created_at
                ) VALUES (
                  :id, :actor_type, :actor_id, :entity_type, :entity_id, :action, :before, :after, :created_at
                )
                """,
                asdict(audit),
            )
            connection.commit()

    def list_user_orders(self, telegram_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT o.public_number, o.country_name_ru, o.submission_city, o.time_window_code,
                       o.payment_status, o.order_status, o.created_at, o.access_key_code
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE u.telegram_id = ?
                ORDER BY o.created_at DESC
                """,
                (telegram_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_admin_queue(self) -> list[dict[str, Any]]:
        statuses = (
            OrderStatus.PAID_WAITING_BOOKING.value,
            OrderStatus.AWAITING_MANAGER_CASH_CONFIRMATION.value,
            OrderStatus.REQUIRES_MANAGER_REVIEW.value,
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT public_number, country_name_ru, submission_city, payment_status, order_status, created_at
                FROM orders
                WHERE order_status IN (?, ?, ?)
                ORDER BY created_at DESC
                LIMIT 20
                """,
                statuses,
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_order_details(self, public_number: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT o.*, u.telegram_id, u.username, u.first_name AS user_first_name, u.last_name AS user_last_name
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.public_number = ?
                """,
                (public_number,),
            ).fetchone()
            if row is None:
                return None
            applicants = connection.execute(
                """
                SELECT last_name, first_name, patronymic, birth_date, citizenship, current_location, relationship
                FROM applicants
                WHERE order_id = ?
                ORDER BY rowid ASC
                """,
                (row["id"],),
            ).fetchall()
            payment = connection.execute(
                """
                SELECT provider, provider_payment_id, amount_rub, status, created_at, paid_at
                FROM payments
                WHERE order_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (row["id"],),
            ).fetchone()
        payload = dict(row)
        payload["applicants"] = [dict(item) for item in applicants]
        payload["payment"] = dict(payment) if payment else None
        return payload

    def _write_audit(self, connection: sqlite3.Connection, actor_type: str, actor_id: str | None, entity_id: str, action: str, before: dict[str, Any], after: dict[str, Any]) -> None:
        audit = AuditLog(
            id=str(uuid4()),
            actor_type=actor_type,
            actor_id=actor_id,
            entity_type="order",
            entity_id=entity_id,
            action=action,
            before=json.dumps(before, ensure_ascii=False),
            after=json.dumps(after, ensure_ascii=False),
            created_at=datetime.now(UTC).isoformat(),
        )
        connection.execute(
            """
            INSERT INTO audit_log (
              id, actor_type, actor_id, entity_type, entity_id, action, before, after, created_at
            ) VALUES (
              :id, :actor_type, :actor_id, :entity_type, :entity_id, :action, :before, :after, :created_at
            )
            """,
            asdict(audit),
        )

    def update_order_status(
        self,
        public_number: str,
        actor_id: int,
        order_status: str,
        payment_status: str | None = None,
        manager_note: str | None = None,
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            current = connection.execute("SELECT * FROM orders WHERE public_number = ?", (public_number,)).fetchone()
            if current is None:
                return None
            updated = dict(current)
            updated["order_status"] = order_status
            updated["updated_at"] = datetime.now(UTC).isoformat()
            if payment_status is not None:
                updated["payment_status"] = payment_status
            if manager_note is not None:
                updated["manager_note"] = manager_note
            connection.execute(
                """
                UPDATE orders
                SET order_status = :order_status,
                    payment_status = :payment_status,
                    manager_note = :manager_note,
                    updated_at = :updated_at
                WHERE public_number = :public_number
                """,
                {
                    "order_status": updated["order_status"],
                    "payment_status": updated["payment_status"],
                    "manager_note": updated["manager_note"],
                    "updated_at": updated["updated_at"],
                    "public_number": public_number,
                },
            )
            if payment_status is not None:
                connection.execute(
                    "UPDATE payments SET status = ?, updated_at = ?, paid_at = COALESCE(paid_at, ?) WHERE order_id = ?",
                    (
                        payment_status,
                        updated["updated_at"],
                        updated["updated_at"] if payment_status in {PaymentStatus.PAID.value, PaymentStatus.PAID_OFFLINE.value} else None,
                        updated["id"],
                    ),
                )
            self._write_audit(connection, "admin", str(actor_id), updated["id"], "update_order_status", dict(current), updated)
            connection.commit()
        return self.get_order_details(public_number)

    def mark_cash_confirmed(self, public_number: str, actor_id: int) -> dict[str, Any] | None:
        return self.update_order_status(
            public_number=public_number,
            actor_id=actor_id,
            order_status=OrderStatus.PAID_WAITING_BOOKING.value,
            payment_status=PaymentStatus.PAID_OFFLINE.value,
        )

    def stats(self) -> dict[str, int]:
        with self._connect() as connection:
            orders_total = connection.execute("SELECT COUNT(*) AS cnt FROM orders").fetchone()["cnt"]
            users_total = connection.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()["cnt"]
            paid_total = connection.execute("SELECT COUNT(*) AS cnt FROM orders WHERE payment_status IN (?, ?)", (PaymentStatus.PAID.value, PaymentStatus.PAID_OFFLINE.value)).fetchone()["cnt"]
            review_total = connection.execute("SELECT COUNT(*) AS cnt FROM orders WHERE order_status = ?", (OrderStatus.REQUIRES_MANAGER_REVIEW.value,)).fetchone()["cnt"]
        return {
            "orders_total": int(orders_total),
            "users_total": int(users_total),
            "paid_total": int(paid_total),
            "review_total": int(review_total),
        }
