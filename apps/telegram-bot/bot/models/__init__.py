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


class AccessKeyStatus(StrEnum):
    ACTIVE = "active"
    ACTIVATED = "activated"
    CONSUMED = "consumed"
    REVOKED = "revoked"
    EXPIRED = "expired"


class SupportRequestStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class ApplicantProfileStatus(StrEnum):
    DRAFT = "draft"
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    APPROVED_BY_MANAGER = "approved_by_manager"


class VisaCaseStatus(StrEnum):
    ACCESS_ACTIVATED = "access_activated"
    DRAFT = "draft"
    PROFILES_NOT_STARTED = "profiles_not_started"
    PROFILES_IN_PROGRESS = "profiles_in_progress"
    PROFILES_COMPLETED = "profiles_completed"
    CITY_SELECTION_IN_PROGRESS = "city_selection_in_progress"
    SUBMITTED_FOR_MANAGER_REVIEW = "submitted_for_manager_review"
    NEEDS_MANAGER_CONSULTATION = "needs_manager_consultation"
    WAITING_MANAGER_REVIEW = "waiting_manager_review"
    NEEDS_CLARIFICATION = "needs_clarification"
    MANAGER_REVIEWING = "manager_reviewing"
    READY_FOR_CITY_SELECTION = "ready_for_city_selection"
    READY_FOR_SLOT_SEARCH = "ready_for_slot_search"
    SLOT_OPTIONS_SENT = "slot_options_sent"
    SLOT_SELECTED_BY_CLIENT = "slot_selected_by_client"
    APPOINTMENT_CONFIRMATION_PENDING = "appointment_confirmation_pending"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class AppointmentSlotOfferStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentSlotOptionStatus(StrEnum):
    AVAILABLE = "available"
    SELECTED = "selected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class DocumentSourceType(StrEnum):
    CLIENT_REQUIRED = "client_required"
    AGENCY_PREPARED = "agency_prepared"


class DocumentCategory(StrEnum):
    INTERNATIONAL_PASSPORT = "international_passport"
    PHOTO = "photo"
    BANK_STATEMENT = "bank_statement"
    INSURANCE_OWN = "insurance_own"
    EMPLOYMENT_CERTIFICATE = "employment_certificate"
    STUDENT_CERTIFICATE = "student_certificate"
    MARRIAGE_CERTIFICATE = "marriage_certificate"
    CHILD_BIRTH_CERTIFICATE = "child_birth_certificate"
    PREVIOUS_VISAS = "previous_visas"
    OTHER_CLIENT_DOCUMENT = "other_client_document"
    HOTEL_BOOKING = "hotel_booking"
    TRANSPORT_BOOKING = "transport_booking"
    INVITATION = "invitation"
    TRAVEL_PLAN = "travel_plan"
    FILLED_APPLICATION_FORM = "filled_application_form"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    INSURANCE_AGENCY_PREPARED = "insurance_agency_prepared"
    COVER_LETTER = "cover_letter"
    OTHER_AGENCY_DOCUMENT = "other_agency_document"


class ClientDocumentStatus(StrEnum):
    REQUESTED = "requested"
    UPLOADED_BY_CLIENT = "uploaded_by_client"
    RECEIVED_BY_MANAGER = "received_by_manager"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_NEEDED = "not_needed"


class AgencyDocumentStatus(StrEnum):
    PLANNED = "planned"
    PREPARING_BY_AGENCY = "preparing_by_agency"
    READY_FOR_CLIENT = "ready_for_client"
    SHARED_WITH_CLIENT = "shared_with_client"
    NOT_NEEDED = "not_needed"


class DocumentFileStatus(StrEnum):
    ACTIVE = "active"
    REPLACED = "replaced"
    DELETED = "deleted"


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
    access_key_code: Optional[str]
    access_key_id: Optional[str]
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
class AccessKey:
    id: str
    code: str
    status: str
    max_uses: int
    used_count: int
    created_by_admin_id: int
    created_at: str
    updated_at: str
    bound_user_id: Optional[str] = None
    bound_telegram_id: Optional[int] = None
    country_codes: list[str] = field(default_factory=list)
    service_type: Optional[str] = None
    max_applicants: Optional[int] = None
    expires_at: Optional[str] = None
    note: Optional[str] = None


@dataclass(slots=True)
class VisaCase:
    id: str
    user_id: str
    telegram_id: int
    status: str
    applicants_count: int
    created_at: str
    updated_at: str
    access_key_id: Optional[str] = None
    access_key_code: Optional[str] = None
    desired_country_code: Optional[str] = None
    desired_country_name_ru: Optional[str] = None
    preferred_submission_city: Optional[str] = None
    submission_provider: Optional[str] = None
    submission_provider_type: Optional[str] = None
    submission_jurisdiction: Optional[str] = None
    submission_verification_status: Optional[str] = None
    travel_purpose: Optional[str] = None
    approximate_travel_start_date: Optional[str] = None
    approximate_travel_end_date: Optional[str] = None
    client_comment: Optional[str] = None
    submitted_at: Optional[str] = None
    manager_reviewed_at: Optional[str] = None
    selected_slot_option_id: Optional[str] = None
    selected_appointment_date: Optional[str] = None
    selected_appointment_time: Optional[str] = None
    selected_appointment_city: Optional[str] = None
    selected_appointment_provider: Optional[str] = None
    appointment_confirmed_at: Optional[str] = None


@dataclass(slots=True)
class ApplicantProfile:
    id: str
    user_id: str
    telegram_id: int
    position: int
    status: str
    completion_percent: int
    created_at: str
    updated_at: str
    case_id: Optional[str] = None
    role: Optional[str] = None
    last_name_latin: Optional[str] = None
    first_name_latin: Optional[str] = None
    last_name_cyrillic: Optional[str] = None
    first_name_cyrillic: Optional[str] = None
    patronymic: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    citizenship: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    residence_country: Optional[str] = None
    residence_city: Optional[str] = None
    residence_address: Optional[str] = None
    postal_code: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issue_date: Optional[str] = None
    passport_expiry_date: Optional[str] = None
    passport_issuing_authority: Optional[str] = None
    passport_issuing_country: Optional[str] = None
    desired_country_code: Optional[str] = None
    desired_country_name_ru: Optional[str] = None
    travel_purpose: Optional[str] = None
    approximate_travel_dates: Optional[str] = None
    entries_count: Optional[str] = None
    preferred_submission_city: Optional[str] = None


@dataclass(slots=True)
class MiniAppIdentity:
    telegram_id: int
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@dataclass(slots=True)
class AppointmentSlotOffer:
    id: str
    case_id: str
    created_by_admin_id: int
    status: str
    created_at: str
    updated_at: str
    message: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass(slots=True)
class AppointmentSlotOption:
    id: str
    offer_id: str
    case_id: str
    option_date: str
    option_time: str
    status: str
    created_at: str
    updated_at: str
    city: Optional[str] = None
    provider: Optional[str] = None
    address: Optional[str] = None
    comment: Optional[str] = None


@dataclass(slots=True)
class SupportRequest:
    id: str
    user_id: str
    telegram_id: int
    status: str
    created_at: str
    updated_at: str
    username: Optional[str] = None
    message: Optional[str] = None


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
    type: str
    jurisdiction: str
    status: str
    verification_status: str
    last_checked_at: str
    source_note: str


@dataclass(slots=True)
class PriceTier:
    code: str
    label_ru: str
    description_ru: str
    price_rub: int
    priority: int
    additional_applicant_price_rub: int


@dataclass(slots=True)
class DocumentItem:
    id: str
    case_id: str
    source_type: str
    category: str
    title: str
    status: str
    required: bool
    visible_to_client: bool
    created_at: str
    updated_at: str
    applicant_id: Optional[str] = None
    description: Optional[str] = None
    requested_by_admin_id: Optional[int] = None
    requested_at: Optional[str] = None
    due_date: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[str] = None
    reviewed_by_admin_id: Optional[int] = None
    reviewed_at: Optional[str] = None
    manager_comment: Optional[str] = None
    client_comment: Optional[str] = None


@dataclass(slots=True)
class DocumentFile:
    id: str
    document_item_id: str
    case_id: str
    uploaded_by: str
    original_filename: str
    storage_path: str
    status: str
    created_at: str
    applicant_id: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
