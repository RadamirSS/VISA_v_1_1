from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from bot.models import Applicant, BookingOrder, Payment


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
    access_key_code: str | None
    access_key_id: str | None
    payment_status: str
    order_status: str
    requires_manager_review: bool
    user_comment: str | None = None
    manager_note: str | None = None


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
        access_key_code=data.access_key_code,
        access_key_id=data.access_key_id,
        payment_status=data.payment_status,
        order_status=data.order_status,
        requires_manager_review=data.requires_manager_review,
        manager_note=data.manager_note,
        user_comment=data.user_comment,
        created_at=now,
        updated_at=now,
    )


def create_applicant(
    order_id: str,
    last_name: str,
    first_name: str,
    patronymic: str | None,
    birth_date: str,
    citizenship: str,
    current_location: str | None,
    relationship: str | None,
    passport_number_encrypted: str | None = None,
    passport_expiry_date: str | None = None,
) -> Applicant:
    return Applicant(
        id=str(uuid4()),
        order_id=order_id,
        last_name=last_name,
        first_name=first_name,
        patronymic=patronymic,
        birth_date=birth_date,
        citizenship=citizenship,
        current_location=current_location,
        relationship=relationship,
        passport_number_encrypted=passport_number_encrypted,
        passport_expiry_date=passport_expiry_date,
    )


def create_payment(order_id: str, provider: str, amount_rub: int, status: str, provider_payment_id: str | None = None, paid_at: str | None = None) -> Payment:
    now = datetime.now(UTC).isoformat()
    return Payment(
        id=str(uuid4()),
        order_id=order_id,
        provider=provider,
        provider_payment_id=provider_payment_id,
        amount_rub=amount_rub,
        status=status,
        created_at=now,
        updated_at=now,
        paid_at=paid_at,
    )
