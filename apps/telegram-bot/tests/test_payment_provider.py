from __future__ import annotations

import asyncio

from bot.services.payment_provider import MockPaymentProvider


def test_mock_payment_creation_returns_pending():
    provider = MockPaymentProvider()
    result = asyncio.run(provider.create_payment("order-1", 14900))
    assert result.ok is True
    assert result.status == "pending"
    assert result.payment_id


def test_mock_payment_check_returns_paid():
    provider = MockPaymentProvider()
    result = asyncio.run(provider.check_payment("mock_123"))
    assert result.ok is True
    assert result.status == "paid"
    assert result.payment_id == "mock_123"
