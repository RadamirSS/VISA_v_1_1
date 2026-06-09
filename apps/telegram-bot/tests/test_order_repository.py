from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from bot.database import init_db, sqlite_path_from_url
from bot.models import OrderStatus, PaymentStatus, User
from bot.repositories.orders import OrderRepository
from bot.repositories.users import UserRepository
from bot.services.order_factory import OrderInput, create_applicant, create_order, create_payment


def test_order_repository_end_to_end(tmp_path: Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'orders.db'}"
    init_db(db_url)
    users = UserRepository(db_url)
    orders = OrderRepository(db_url)

    user = User(
        id="user-1",
        telegram_id=111,
        username="tester",
        first_name="Иван",
        last_name="Иванов",
        patronymic="Иванович",
        birth_date="1990-01-01",
        citizenship="Россия",
        current_location="Москва",
        phone="+70000000000",
        email="ivan@example.com",
        consent_accepted_at=datetime.now(UTC).isoformat(),
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    users.save(user)

    order = create_order(
        OrderInput(
            user_id=user.id,
            country_code="IT",
            country_name_ru="Италия",
            submission_city="Москва",
            provider="mock",
            visa_purpose="Туризм",
            time_window_code="two_weeks",
            applicants_count=1,
            base_price_rub=14900,
            additional_applicants_price_rub=0,
            discount_rub=0,
            total_price_rub=14900,
            promo_code=None,
            payment_status=PaymentStatus.PENDING.value,
            order_status=OrderStatus.AWAITING_PAYMENT.value,
            requires_manager_review=False,
        ),
        sequence=1,
    )
    applicant = create_applicant(order.id, "Иванов", "Иван", "Иванович", "1990-01-01", "Россия", "Москва", None)
    payment = create_payment(order.id, "mock", 14900, PaymentStatus.PENDING.value, provider_payment_id="mock_1")

    orders.create_order(order, [applicant], payment, actor_type="user", actor_id=str(user.telegram_id))

    user_orders = orders.list_user_orders(user.telegram_id)
    assert len(user_orders) == 1
    assert user_orders[0]["public_number"] == order.public_number

    details = orders.get_order_details(order.public_number)
    assert details is not None
    assert details["payment"]["status"] == PaymentStatus.PENDING.value
    assert details["applicants"][0]["last_name"] == "Иванов"

    updated = orders.update_order_status(order.public_number, 999, OrderStatus.PAID_WAITING_BOOKING.value, PaymentStatus.PAID.value)
    assert updated is not None
    assert updated["order_status"] == OrderStatus.PAID_WAITING_BOOKING.value
    assert updated["payment_status"] == PaymentStatus.PAID.value

    connection = sqlite3.connect(sqlite_path_from_url(db_url))
    connection.row_factory = sqlite3.Row
    try:
        audit_rows = connection.execute("SELECT action FROM audit_log WHERE entity_id = ? ORDER BY created_at", (order.id,)).fetchall()
    finally:
        connection.close()
    assert [row["action"] for row in audit_rows] == ["create_order", "update_order_status"]
