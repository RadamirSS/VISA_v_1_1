from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class PromoCodeType(StrEnum):
    FULL_DISCOUNT = "full_discount"
    PERCENT_DISCOUNT = "percent_discount"
    FIXED_DISCOUNT = "fixed_discount"
    CASH_PAID = "cash_paid"
    MANAGER_OVERRIDE = "manager_override"


class PaymentStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PAID = "paid"
    PAID_OFFLINE = "paid_offline"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_PAYMENT = "awaiting_payment"
    AWAITING_MANAGER_CASH_CONFIRMATION = "awaiting_manager_cash_confirmation"
    REQUIRES_MANAGER_REVIEW = "requires_manager_review"
    PAID_WAITING_BOOKING = "paid_waiting_booking"
    SENT_TO_BOOKING_PROVIDER = "sent_to_booking_provider"
    SLOT_FOUND = "slot_found"
    SLOT_CONFIRMATION_PENDING = "slot_confirmation_pending"
    BOOKED = "booked"
    NEEDS_USER_ACTION = "needs_user_action"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass(slots=True)
class User:
    id: str
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    birth_date: Optional[str] = None
    citizenship: Optional[str] = None
    current_location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    consent_accepted_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Applicant:
    id: str
    order_id: str
    last_name: str
    first_name: str
    patronymic: Optional[str]
    birth_date: str
    citizenship: str
    current_location: Optional[str] = None
    relationship: Optional[str] = None
    passport_number_encrypted: Optional[str] = None
    passport_expiry_date: Optional[str] = None


@dataclass(slots=True)
class BookingOrder:
    id: str
    public_number: str
    user_id: str
    country_code: str
    country_name_ru: str
    submission_city: str
    provider: Optional[str]
    visa_purpose: str
    time_window_code: str
    applicants_count: int
    base_price_rub: int
    additional_applicants_price_rub: int
    discount_rub: int
    total_price_rub: int
    promo_code: Optional[str]
    payment_status: str
    order_status: str
    requires_manager_review: bool
    manager_note: Optional[str] = None
    user_comment: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Payment:
    id: str
    order_id: str
    provider: str
    amount_rub: int
    status: str
    provider_payment_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    paid_at: Optional[str] = None


@dataclass(slots=True)
class PromoCode:
    id: str
    code: str
    type: str
    value: int
    max_uses: int
    used_count: int
    active: bool
    created_by_admin_id: int
    created_at: str
    expires_at: Optional[str] = None
    country_codes: list[str] = field(default_factory=list)
    time_window_codes: list[str] = field(default_factory=list)
    note: Optional[str] = None


@dataclass(slots=True)
class AuditLog:
    id: str
    actor_type: str
    entity_type: str
    entity_id: str
    action: str
    created_at: str
    actor_id: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None


@dataclass(slots=True)
class CountryOption:
    code: str
    slug: str
    name_ru: str
    suits_for_ru: str


@dataclass(slots=True)
class ConsulateOption:
    country_code: str
    country_name_ru: str
    city: str
    provider: str
    verification_status: str


@dataclass(slots=True)
class PriceTier:
    code: str
    label_ru: str
    description_ru: str
    price_rub: int
    priority: int
    additional_applicant_price_rub: int
