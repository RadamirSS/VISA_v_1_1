from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from bot.models import BookingOrder


@dataclass(slots=True)
class BookingProviderResponse:
    ok: bool
    status: str
    message: str


@dataclass(slots=True)
class Slot:
    slot_id: str
    label_ru: str


class BookingProvider(Protocol):
    async def create_request(self, order: BookingOrder) -> BookingProviderResponse: ...
    async def check_slots(self, country_code: str, city: str, time_window_code: str) -> list[Slot]: ...
    async def confirm_slot(self, order_id: str, slot_id: str) -> BookingProviderResponse: ...


class MockBookingProvider:
    async def create_request(self, order: BookingOrder) -> BookingProviderResponse:
        return BookingProviderResponse(
            ok=True,
            status="sent_to_booking_provider",
            message="Заявка переведена на внутренний mock-этап обработки. Реальный booking API пока не подключен.",
        )

    async def check_slots(self, country_code: str, city: str, time_window_code: str) -> list[Slot]:
        return []

    async def confirm_slot(self, order_id: str, slot_id: str) -> BookingProviderResponse:
        return BookingProviderResponse(ok=True, status="slot_confirmation_pending", message="Реальное подтверждение слота будет подключено позже.")
