from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class PaymentProviderResponse:
    ok: bool
    status: str
    message: str


class PaymentProvider(Protocol):
    async def create_payment(self, order_id: str, amount_rub: int) -> PaymentProviderResponse: ...


class MockPaymentProvider:
    async def create_payment(self, order_id: str, amount_rub: int) -> PaymentProviderResponse:
        return PaymentProviderResponse(ok=True, status="pending", message=f"Создан mock-платеж на {amount_rub} ₽.")
