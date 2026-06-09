from __future__ import annotations

from pathlib import Path

from bot.database import init_db
from bot.models import VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository, new_access_key
from bot.repositories.miniapp import MiniAppRepository
from bot.models import OrderStatus, PaymentStatus
from bot.repositories.orders import OrderRepository
from bot.repositories.users import UserRepository
from bot.services.case_status import format_case_public_number
from bot.services.order_factory import OrderInput, create_applicant, create_order, create_payment


def build_search_context(tmp_path: Path) -> tuple[MiniAppRepository, OrderRepository, str, str, int]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'admin-case-search.db'}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    users = UserRepository(database_url)
    keys = AccessKeyRepository(database_url)
    miniapp = MiniAppRepository(database_url, repo_root=repo_root)
    orders = OrderRepository(database_url)
    user = users.upsert_from_telegram(9700, "searchuser", "Search", "User")
    key = new_access_key("SRCH-KEY", 1, "miniapp", [], 2, None, None)
    keys.save(key)
    keys.bind_and_activate(key.code, user.id, user.telegram_id)
    case = miniapp.create_case(user, key.id, key.code)
    case.status = VisaCaseStatus.SUBMITTED_FOR_MANAGER_REVIEW.value
    miniapp.save_case(case)
    public_number = format_case_public_number(case)
    return miniapp, orders, case.id, public_number, user.telegram_id


def test_resolve_case_by_internal_id(tmp_path: Path) -> None:
    miniapp, _, case_id, _, _ = build_search_context(tmp_path)
    found = miniapp.resolve_case_lookup(case_id)
    assert found is not None
    assert found.id == case_id


def test_resolve_case_by_public_number(tmp_path: Path) -> None:
    miniapp, _, case_id, public_number, _ = build_search_context(tmp_path)
    found = miniapp.resolve_case_lookup(public_number)
    assert found is not None
    assert found.id == case_id


def test_resolve_case_by_telegram_id(tmp_path: Path) -> None:
    miniapp, _, case_id, _, telegram_id = build_search_context(tmp_path)
    found = miniapp.resolve_case_lookup(str(telegram_id))
    assert found is not None
    assert found.id == case_id


def test_resolve_case_by_username(tmp_path: Path) -> None:
    miniapp, _, case_id, _, _ = build_search_context(tmp_path)
    found = miniapp.resolve_case_lookup("@searchuser")
    assert found is not None
    assert found.id == case_id


def test_order_search_still_available(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'admin-case-search-orders.db'}"
    init_db(database_url)
    users = UserRepository(database_url)
    orders = OrderRepository(database_url)
    user = users.upsert_from_telegram(9701, "orderuser", "Order", "User")
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
            access_key_code=None,
            access_key_id=None,
            payment_status=PaymentStatus.PAID.value,
            order_status=OrderStatus.PAID_WAITING_BOOKING.value,
            requires_manager_review=False,
        ),
        sequence=1,
    )
    applicant = create_applicant(order.id, "Иванов", "Иван", "Иванович", "1990-01-01", "Россия", "Москва", None)
    payment = create_payment(order.id, "mock", 14900, PaymentStatus.PAID.value, provider_payment_id="mock_1")
    orders.create_order(order, [applicant], payment, actor_type="user", actor_id=str(user.telegram_id))

    details = orders.get_order_details(order.public_number)
    assert details is not None
    assert details["public_number"] == order.public_number
