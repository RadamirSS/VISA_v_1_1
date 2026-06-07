from bot.models import OrderStatus, PaymentStatus


def test_payment_status_constants_cover_mock_and_offline_flow():
    assert PaymentStatus.PENDING.value == "pending"
    assert PaymentStatus.PAID.value == "paid"
    assert PaymentStatus.PAID_OFFLINE.value == "paid_offline"
    assert OrderStatus.AWAITING_MANAGER_CASH_CONFIRMATION.value == "awaiting_manager_cash_confirmation"
    assert OrderStatus.REQUIRES_MANAGER_REVIEW.value == "requires_manager_review"
