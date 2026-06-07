from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from bot.models import BookingOrder


@dataclass(slots=True)
class OrderInput:
    user_id: str
    country_code: str
    country_name_ru: str
    submission_city: str
    provider: str | None
    visa_purpose: str
    time_window_code: str
    applicants_count: int
    base_price_rub: int
    additional_applicants_price_rub: int
    discount_rub: int
    total_price_rub: int
    promo_code: str | None
    payment_status: str
    order_status: str
    requires_manager_review: bool
    user_comment: str | None = None


def create_public_number(sequence: int) -> str:
    year = datetime.now(UTC).year
    return f"VISA-{year}-{sequence:06d}"


def create_order(data: OrderInput, sequence: int) -> BookingOrder:
    now = datetime.now(UTC).isoformat()
    return BookingOrder(
        id=str(uuid4()),
        public_number=create_public_number(sequence),
        user_id=data.user_id,
        country_code=data.country_code,
        country_name_ru=data.country_name_ru,
        submission_city=data.submission_city,
        provider=data.provider,
        visa_purpose=data.visa_purpose,
        time_window_code=data.time_window_code,
        applicants_count=data.applicants_count,
        base_price_rub=data.base_price_rub,
        additional_applicants_price_rub=data.additional_applicants_price_rub,
        discount_rub=data.discount_rub,
        total_price_rub=data.total_price_rub,
        promo_code=data.promo_code,
        payment_status=data.payment_status,
        order_status=data.order_status,
        requires_manager_review=data.requires_manager_review,
        user_comment=data.user_comment,
        created_at=now,
        updated_at=now,
    )
