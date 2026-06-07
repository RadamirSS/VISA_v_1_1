from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


@dataclass(slots=True)
class PaymentProviderResponse:
    ok: bool
    status: str
    message: str
    payment_id: str | None = None
    paid_at: str | None = None


class PaymentProvider(Protocol):
    async def create_payment(self, order_id: str, amount_rub: int) -> PaymentProviderResponse: ...
    async def check_payment(self, payment_id: str) -> PaymentProviderResponse: ...


class MockPaymentProvider:
    async def create_payment(self, order_id: str, amount_rub: int) -> PaymentProviderResponse:
        return PaymentProviderResponse(ok=True, status="pending", message=f"Создан mock-платеж на {amount_rub} ₽.", payment_id=f"mock_{uuid4().hex[:12]}")

    async def check_payment(self, payment_id: str) -> PaymentProviderResponse:
        return PaymentProviderResponse(ok=True, status="paid", message="Mock-платеж подтвержден в режиме разработки.", payment_id=payment_id, paid_at=datetime.now(UTC).isoformat())
