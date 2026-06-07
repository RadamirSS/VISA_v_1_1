from datetime import UTC, datetime
from pathlib import Path

from bot.database import init_db
from bot.models import OrderStatus, PaymentStatus, User
from bot.repositories.orders import OrderRepository
from bot.repositories.users import UserRepository
from bot.services.order_factory import OrderInput, create_applicant, create_order, create_payment


def test_order_creation_persists_order_and_payment(tmp_path: Path):
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
            payment_status=PaymentStatus.PAID.value,
            order_status=OrderStatus.PAID_WAITING_BOOKING.value,
            requires_manager_review=False,
        ),
        sequence=1,
    )
    applicant = create_applicant(order.id, "Иванов", "Иван", "Иванович", "1990-01-01", "Россия", "Москва", None)
    payment = create_payment(order.id, "mock", 14900, PaymentStatus.PAID.value, provider_payment_id="mock_1", paid_at=datetime.now(UTC).isoformat())
    orders.create_order(order, [applicant], payment, actor_type="user", actor_id="111")
    user_orders = orders.list_user_orders(111)
    assert user_orders[0]["public_number"] == order.public_number
    details = orders.get_order_details(order.public_number)
    assert details is not None
    assert details["payment"]["status"] == PaymentStatus.PAID.value
