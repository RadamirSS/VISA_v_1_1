from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TelegramValidationResponse(BaseModel):
    ok: bool
    mode: str
    telegram_id: int
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class MeResponse(BaseModel):
    telegram_id: int
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    has_active_access: bool
    active_access_key_code: Optional[str] = None
    current_case_status: Optional[str] = None
    has_case: bool = False


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    telegram_id: int
    access_key_id: Optional[str] = None
    access_key_code: Optional[str] = None
    status: str
    applicants_count: int
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
    created_at: str
    updated_at: str


class CountryOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    slug: str
    name_ru: str
    suits_for_ru: str


class ConsulateOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class CreateCaseResponse(BaseModel):
    case: CaseResponse
    incomplete_applicants: list[str]


class CasePayload(BaseModel):
    desired_country_code: Optional[str] = None
    desired_country_name_ru: Optional[str] = None
    preferred_submission_city: Optional[str] = None
    submission_provider: Optional[str] = None
    travel_purpose: Optional[str] = None
    approximate_travel_start_date: Optional[str] = None
    approximate_travel_end_date: Optional[str] = None
    client_comment: Optional[str] = None


class CaseSubmitResponse(BaseModel):
    case: CaseResponse
    incomplete_applicants: list[ApplicantResponse]


class SlotOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    offer_id: str
    case_id: str
    option_date: str
    option_time: str
    city: Optional[str] = None
    provider: Optional[str] = None
    address: Optional[str] = None
    comment: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class SlotOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    created_by_admin_id: int
    status: str
    message: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str
    updated_at: str
    options: list[SlotOptionResponse]


class ApplicantsCountPayload(BaseModel):
    applicants_count: int = Field(ge=1, le=12)


class ApplicantProfilePayload(BaseModel):
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


class ApplicantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    telegram_id: int
    case_id: Optional[str] = None
    position: int
    role: Optional[str] = None
    status: str
    completion_percent: int
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
    created_at: str
    updated_at: str


class NextActionResponse(BaseModel):
    type: str
    label: str
    href: str


class CabinetUserSummary(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    username: Optional[str] = None


class CabinetAccessSummary(BaseModel):
    active: bool
    status_label: str


class CabinetCaseSummary(BaseModel):
    id: str
    public_number: str
    status: str
    status_label: str
    desired_country_name_ru: Optional[str] = None
    preferred_submission_city: Optional[str] = None
    submission_provider: Optional[str] = None
    applicants_count: int
    next_action: NextActionResponse


class CabinetApplicantsSummary(BaseModel):
    total: int
    completed: int
    incomplete: int


class AppointmentSelectedSummary(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    city: Optional[str] = None
    provider: Optional[str] = None


class AppointmentConfirmedSummary(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    city: Optional[str] = None
    provider: Optional[str] = None


class CabinetAppointmentSummary(BaseModel):
    has_options: bool
    selected: Optional[AppointmentSelectedSummary] = None
    confirmed: Optional[AppointmentConfirmedSummary] = None


class CabinetDocumentsSummary(BaseModel):
    has_items: bool
    client_pending: int
    client_uploaded: int
    agency_in_progress: int
    agency_ready: int
    agency_shared: int = 0


class CabinetSummaryResponse(BaseModel):
    user: CabinetUserSummary
    access: CabinetAccessSummary
    case: Optional[CabinetCaseSummary] = None
    next_action: Optional[NextActionResponse] = None
    applicants: CabinetApplicantsSummary
    appointment: CabinetAppointmentSummary
    documents: Optional[CabinetDocumentsSummary] = None


class DocumentItemResponse(BaseModel):
    id: str
    source_type: str
    category: str
    title: str
    description: Optional[str] = None
    status: str
    status_label: str
    required: bool
    manager_comment: Optional[str] = None
    client_comment: Optional[str] = None
    can_upload: bool
    can_download: bool
    has_file: bool
    uploads_enabled: bool
    transferred_separately: bool = False


class DocumentsListResponse(BaseModel):
    items: list[DocumentItemResponse]
    uploads_enabled: bool


class DocumentCommentPayload(BaseModel):
    comment: str
    no_insurance: bool = False


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    status_label: str
    has_file: bool


class TimelineStepResponse(BaseModel):
    key: str
    label: str
    state: str


class CaseTimelineResponse(BaseModel):
    status: str
    status_label: str
    steps: list[TimelineStepResponse]
