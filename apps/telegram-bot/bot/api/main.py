from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from bot.api.auth import get_identity
from bot.api.schemas import (
    ApplicantProfilePayload,
    ApplicantResponse,
    ApplicantsCountPayload,
    AppointmentConfirmedSummary,
    AppointmentSelectedSummary,
    CabinetAccessSummary,
    CabinetApplicantsSummary,
    CabinetAppointmentSummary,
    CabinetCaseSummary,
    CabinetDocumentsSummary,
    CabinetSummaryResponse,
    CabinetUserSummary,
    CasePayload,
    CaseResponse,
    CaseSubmitResponse,
    CaseTimelineResponse,
    ConsulateOptionResponse,
    CountryOptionResponse,
    CreateCaseResponse,
    DocumentCommentPayload,
    DocumentItemResponse,
    DocumentsListResponse,
    DocumentUploadResponse,
    MeResponse,
    NextActionResponse,
    SlotOfferResponse,
    SlotOptionResponse,
    TelegramValidationResponse,
    TimelineStepResponse,
)
from bot.config import Settings, get_settings
from bot.database import init_db
from bot.models import ApplicantProfileStatus, MiniAppIdentity, User, VisaCase, VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import CONSULTATION_COUNTRY_CODE, MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.case_status import (
    access_status_label,
    build_case_timeline,
    case_next_action,
    case_status_label,
    format_case_public_number,
)
from bot.services.document_status import (
    can_client_download,
    can_client_upload,
    document_status_label,
    is_transferred_separately,
)
from bot.services.document_storage import DocumentStorageService
from bot.services.notifications import (
    build_agency_document_ready_message,
    build_appointment_confirmed_message,
    build_case_submitted_notification,
    build_client_uploaded_notification,
    build_documents_requested_message,
    build_profiles_completed_notification,
    build_slot_selected_notification,
    build_user_case_submitted_message,
    build_user_slot_selected_message,
    notify_admins,
)


@dataclass(slots=True)
class Container:
    settings: Settings
    users: UserRepository
    access_keys: AccessKeyRepository
    miniapp: MiniAppRepository
    documents: DocumentRepository
    document_storage: DocumentStorageService


_container: Container | None = None


def _build_document_storage(settings: Settings, documents: DocumentRepository) -> DocumentStorageService:
    return DocumentStorageService(
        repository=documents,
        storage_dir=settings.document_storage_dir,
        max_file_mb=settings.document_max_file_mb,
        enabled=settings.document_uploads_enabled,
    )


def get_container() -> Container:
    global _container
    if _container is None:
        settings = get_settings()
        init_db(settings.database_url)
        documents = DocumentRepository(settings.database_url)
        _container = Container(
            settings=settings,
            users=UserRepository(settings.database_url),
            access_keys=AccessKeyRepository(settings.database_url),
            miniapp=MiniAppRepository(settings.database_url, repo_root=settings.repo_root),
            documents=documents,
            document_storage=_build_document_storage(settings, documents),
        )
    return _container


def _active_access_code(container: Container, telegram_id: int):
    return container.access_keys.get_active_for_telegram_user(telegram_id)


def _ensure_access_key(container: Container, identity: MiniAppIdentity):
    access_key = _active_access_code(container, identity.telegram_id)
    if access_key is None:
        raise HTTPException(status_code=403, detail="Для создания заявки нужен ключ доступа от менеджера. Вернитесь в бот и введите ключ доступа.")
    return access_key


def _ensure_user(container: Container, identity: MiniAppIdentity) -> User:
    user = container.users.get_by_telegram_id(identity.telegram_id)
    if user is None:
        user = container.users.upsert_from_telegram(identity.telegram_id, identity.username, identity.first_name, identity.last_name)
    return user


def _applicant_counts(container: Container, telegram_id: int) -> CabinetApplicantsSummary:
    applicants = container.miniapp.list_applicants(telegram_id)
    completed = sum(1 for item in applicants if item.status == ApplicantProfileStatus.COMPLETED.value)
    total = len(applicants)
    return CabinetApplicantsSummary(total=total, completed=completed, incomplete=total - completed)


def _has_available_slot_options(container: Container, telegram_id: int) -> bool:
    return container.miniapp.has_available_slot_options_for_user(telegram_id)


def _has_city_selected(visa_case: VisaCase) -> bool:
    if not visa_case.desired_country_code:
        return False
    if visa_case.desired_country_code in {CONSULTATION_COUNTRY_CODE, "OTHER"}:
        return True
    return bool(visa_case.preferred_submission_city)


def _build_appointment_summary(container: Container, telegram_id: int, visa_case: VisaCase | None) -> CabinetAppointmentSummary:
    has_options = _has_available_slot_options(container, telegram_id) if visa_case else False
    selected = None
    confirmed = None
    if visa_case and visa_case.selected_appointment_date:
        selected = AppointmentSelectedSummary(
            date=visa_case.selected_appointment_date,
            time=visa_case.selected_appointment_time,
            city=visa_case.selected_appointment_city,
            provider=visa_case.selected_appointment_provider,
        )
    if visa_case and visa_case.appointment_confirmed_at:
        confirmed = AppointmentConfirmedSummary(
            date=visa_case.selected_appointment_date,
            time=visa_case.selected_appointment_time,
            city=visa_case.selected_appointment_city,
            provider=visa_case.selected_appointment_provider,
        )
    return CabinetAppointmentSummary(has_options=has_options, selected=selected, confirmed=confirmed)


def _build_documents_summary(container: Container, visa_case: VisaCase | None) -> CabinetDocumentsSummary | None:
    if visa_case is None:
        return None
    counts = container.documents.count_summary(visa_case.id)
    return CabinetDocumentsSummary(
        has_items=bool(counts["has_items"]),
        client_pending=int(counts["client_pending"]),
        client_uploaded=int(counts["client_uploaded"]),
        agency_in_progress=int(counts["agency_in_progress"]),
        agency_ready=int(counts["agency_ready"]),
        agency_shared=int(counts["agency_shared"]),
    )


def _pending_document_uploads(container: Container, visa_case: VisaCase | None) -> int:
    if visa_case is None:
        return 0
    counts = container.documents.count_summary(visa_case.id)
    return int(counts["client_pending"])


def _document_item_response(container: Container, item) -> DocumentItemResponse:
    has_file = container.documents.has_active_file(item.id)
    return DocumentItemResponse(
        id=item.id,
        source_type=item.source_type,
        category=item.category,
        title=item.title,
        description=item.description,
        status=item.status,
        status_label=document_status_label(item, has_file=has_file),
        required=item.required,
        manager_comment=item.manager_comment,
        client_comment=item.client_comment,
        can_upload=can_client_upload(item) and container.document_storage.enabled,
        can_download=can_client_download(item, has_file=has_file),
        has_file=has_file,
        uploads_enabled=container.document_storage.enabled,
        transferred_separately=is_transferred_separately(item),
    )


def _get_current_case(container: Container, identity: MiniAppIdentity) -> VisaCase:
    _ensure_access_key(container, identity)
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    if visa_case is None:
        raise HTTPException(status_code=404, detail="У вас пока нет визовой заявки.")
    return visa_case


def _build_cabinet_case_summary(
    container: Container,
    identity: MiniAppIdentity,
    visa_case: VisaCase,
) -> CabinetCaseSummary:
    has_slot_options = _has_available_slot_options(container, identity.telegram_id)
    has_selected_slot = bool(visa_case.selected_slot_option_id or visa_case.selected_appointment_date)
    applicants = container.miniapp.list_applicants(identity.telegram_id)
    pending_docs = _pending_document_uploads(container, visa_case)
    return CabinetCaseSummary(
        id=visa_case.id,
        public_number=format_case_public_number(visa_case),
        status=visa_case.status,
        status_label=case_status_label(visa_case.status),
        desired_country_name_ru=visa_case.desired_country_name_ru,
        preferred_submission_city=visa_case.preferred_submission_city,
        submission_provider=visa_case.submission_provider,
        applicants_count=visa_case.applicants_count,
        next_action=NextActionResponse.model_validate(
            case_next_action(
                visa_case.status,
                has_applicants=bool(applicants),
                has_slot_options=has_slot_options,
                has_selected_slot=has_selected_slot,
                has_city_selected=_has_city_selected(visa_case),
                pending_document_uploads=pending_docs,
            )
        ),
    )


def _build_cabinet_summary(container: Container, identity: MiniAppIdentity) -> CabinetSummaryResponse:
    access_key = _active_access_code(container, identity.telegram_id)
    access_active = access_key is not None
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    if access_active and visa_case is not None:
        visa_case = container.miniapp.refresh_case_status(identity.telegram_id)

    applicants_summary = _applicant_counts(container, identity.telegram_id)
    appointment = _build_appointment_summary(container, identity.telegram_id, visa_case)

    case_summary = None
    top_level_next_action = None
    if access_active and visa_case is not None:
        case_summary = _build_cabinet_case_summary(container, identity, visa_case)
    elif not access_active:
        top_level_next_action = NextActionResponse.model_validate(case_next_action("no_access"))
    else:
        top_level_next_action = NextActionResponse.model_validate(case_next_action("no_case"))

    return CabinetSummaryResponse(
        user=CabinetUserSummary(
            telegram_id=identity.telegram_id,
            first_name=identity.first_name,
            username=identity.username,
        ),
        access=CabinetAccessSummary(
            active=access_active,
            status_label=access_status_label(access_active),
        ),
        case=case_summary,
        next_action=top_level_next_action,
        applicants=applicants_summary,
        appointment=appointment,
        documents=_build_documents_summary(container, visa_case),
    )


async def _notify_client_uploaded(container: Container, identity: MiniAppIdentity, visa_case: VisaCase, title: str, status: str) -> None:
    if not container.settings.miniapp_bot_token:
        return
    bot = Bot(token=container.settings.miniapp_bot_token)
    try:
        await notify_admins(
            bot,
            container.settings,
            build_client_uploaded_notification(format_case_public_number(visa_case), title, status),
        )
    finally:
        await bot.session.close()


async def _notify_if_profiles_completed(container: Container, identity: MiniAppIdentity) -> None:
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    if visa_case is None or visa_case.status != VisaCaseStatus.PROFILES_COMPLETED.value or not container.settings.miniapp_bot_token:
        return
    bot = Bot(token=container.settings.miniapp_bot_token)
    try:
        await notify_admins(
            bot,
            container.settings,
            build_profiles_completed_notification(
                telegram_id=identity.telegram_id,
                username=identity.username,
                applicants_count=visa_case.applicants_count,
                case_status=visa_case.status,
            ),
        )
    finally:
        await bot.session.close()


async def _notify_case_submitted(container: Container, identity: MiniAppIdentity, visa_case: CaseResponse) -> None:
    if not container.settings.miniapp_bot_token:
        return
    bot = Bot(token=container.settings.miniapp_bot_token)
    try:
        await notify_admins(
            bot,
            container.settings,
            build_case_submitted_notification(
                case_id=visa_case.id,
                telegram_id=identity.telegram_id,
                username=identity.username,
                applicants_count=visa_case.applicants_count,
                country_name=visa_case.desired_country_name_ru,
                city=visa_case.preferred_submission_city,
                provider=visa_case.submission_provider,
                travel_purpose=visa_case.travel_purpose,
                case_status=visa_case.status,
            ),
        )
        await bot.send_message(identity.telegram_id, build_user_case_submitted_message())
    finally:
        await bot.session.close()


async def _notify_slot_selected(container: Container, identity: MiniAppIdentity, visa_case: CaseResponse) -> None:
    if not container.settings.miniapp_bot_token:
        return
    bot = Bot(token=container.settings.miniapp_bot_token)
    try:
        await notify_admins(
            bot,
            container.settings,
            build_slot_selected_notification(
                visa_case.id,
                identity.telegram_id,
                identity.username,
                visa_case.selected_appointment_date or "-",
                visa_case.selected_appointment_time or "-",
                visa_case.selected_appointment_city,
                visa_case.selected_appointment_provider,
            ),
        )
        await bot.send_message(
            identity.telegram_id,
            build_user_slot_selected_message(
                visa_case.selected_appointment_date or "-",
                visa_case.selected_appointment_time or "-",
            ),
        )
    finally:
        await bot.session.close()


app = FastAPI(title="Visa Mini App API", version="0.2.0")

settings = get_settings()
allowed_origins = [settings.miniapp_allowed_origin] if settings.miniapp_allowed_origin else (["*"] if settings.miniapp_dev_auth else [])
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/telegram/validate", response_model=TelegramValidationResponse)
async def validate_telegram(identity: MiniAppIdentity = Depends(get_identity)) -> TelegramValidationResponse:
    container = get_container()
    return TelegramValidationResponse(
        ok=True,
        mode="dev" if container.settings.miniapp_dev_auth else "telegram",
        telegram_id=identity.telegram_id,
        user_id=identity.user_id,
        username=identity.username,
        first_name=identity.first_name,
        last_name=identity.last_name,
    )


@app.get("/api/cabinet/summary", response_model=CabinetSummaryResponse)
async def cabinet_summary(identity: MiniAppIdentity = Depends(get_identity)) -> CabinetSummaryResponse:
    container = get_container()
    return _build_cabinet_summary(container, identity)


@app.get("/api/case/current/timeline", response_model=CaseTimelineResponse)
async def current_case_timeline(identity: MiniAppIdentity = Depends(get_identity)) -> CaseTimelineResponse:
    container = get_container()
    _ensure_access_key(container, identity)
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    if visa_case is None:
        raise HTTPException(status_code=404, detail="У вас пока нет визовой заявки.")
    visa_case = container.miniapp.refresh_case_status(identity.telegram_id)
    applicants = container.miniapp.list_applicants(identity.telegram_id)
    applicants_completed = bool(applicants) and all(
        item.status == ApplicantProfileStatus.COMPLETED.value for item in applicants
    )
    steps = build_case_timeline(visa_case.status, access_active=True, applicants_completed=applicants_completed)
    return CaseTimelineResponse(
        status=visa_case.status,
        status_label=case_status_label(visa_case.status),
        steps=[TimelineStepResponse.model_validate(step) for step in steps],
    )


@app.get("/api/me", response_model=MeResponse)
async def me(identity: MiniAppIdentity = Depends(get_identity)) -> MeResponse:
    container = get_container()
    access_key = _active_access_code(container, identity.telegram_id)
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    return MeResponse(
        telegram_id=identity.telegram_id,
        user_id=identity.user_id,
        username=identity.username,
        first_name=identity.first_name,
        last_name=identity.last_name,
        has_active_access=access_key is not None,
        active_access_key_code=access_key.code if access_key else None,
        current_case_status=visa_case.status if visa_case else None,
        has_case=visa_case is not None,
    )


@app.get("/api/config/countries", response_model=list[CountryOptionResponse])
async def config_countries(identity: MiniAppIdentity = Depends(get_identity)) -> list[CountryOptionResponse]:
    del identity
    container = get_container()
    return [CountryOptionResponse.model_validate(item) for item in container.miniapp.list_countries()]


@app.get("/api/config/consulates", response_model=list[ConsulateOptionResponse])
async def config_consulates(countryCode: str = Query(...), identity: MiniAppIdentity = Depends(get_identity)) -> list[ConsulateOptionResponse]:
    del identity
    container = get_container()
    return [ConsulateOptionResponse.model_validate(item) for item in container.miniapp.list_consulates(countryCode)]


@app.get("/api/case/current", response_model=CaseResponse)
async def current_case(identity: MiniAppIdentity = Depends(get_identity)) -> CaseResponse:
    container = get_container()
    _ensure_access_key(container, identity)
    visa_case = container.miniapp.get_case_for_telegram_user(identity.telegram_id)
    if visa_case is None:
        raise HTTPException(status_code=404, detail="У вас пока нет визовой заявки.")
    visa_case = container.miniapp.refresh_case_status(identity.telegram_id)
    return CaseResponse.model_validate(visa_case)


@app.post("/api/case", response_model=CreateCaseResponse)
async def create_case(identity: MiniAppIdentity = Depends(get_identity)) -> CreateCaseResponse:
    container = get_container()
    access_key = _ensure_access_key(container, identity)
    user = _ensure_user(container, identity)
    visa_case = container.miniapp.create_case(user, access_key.id, access_key.code)
    incomplete = [
        f"{item.last_name_cyrillic or item.first_name_cyrillic or f'Заявитель {item.position}'} — {item.completion_percent}%"
        for item in container.miniapp.list_incomplete_applicants(identity.telegram_id)
    ]
    return CreateCaseResponse(case=CaseResponse.model_validate(visa_case), incomplete_applicants=incomplete)


@app.patch("/api/case/current", response_model=CaseResponse)
async def update_case(payload: CasePayload, identity: MiniAppIdentity = Depends(get_identity)) -> CaseResponse:
    container = get_container()
    _ensure_access_key(container, identity)
    try:
        visa_case = container.miniapp.update_case(identity.telegram_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if visa_case is None:
        raise HTTPException(status_code=404, detail="У вас пока нет визовой заявки.")
    return CaseResponse.model_validate(visa_case)


@app.post("/api/case/current/submit", response_model=CaseSubmitResponse)
async def submit_case(identity: MiniAppIdentity = Depends(get_identity)) -> CaseSubmitResponse:
    container = get_container()
    _ensure_access_key(container, identity)
    try:
        visa_case, _ = container.miniapp.submit_case(identity.telegram_id)
    except ValueError as exc:
        incomplete = [ApplicantResponse.model_validate(item) for item in container.miniapp.list_incomplete_applicants(identity.telegram_id)]
        raise HTTPException(status_code=400, detail={"message": str(exc), "incompleteApplicants": [item.model_dump() for item in incomplete]}) from exc
    response_case = CaseResponse.model_validate(visa_case)
    await _notify_case_submitted(container, identity, response_case)
    return CaseSubmitResponse(
        case=response_case,
        incomplete_applicants=[ApplicantResponse.model_validate(item) for item in container.miniapp.list_incomplete_applicants(identity.telegram_id)],
    )


@app.get("/api/case/current/slot-offers", response_model=list[SlotOfferResponse])
async def current_case_slot_offers(identity: MiniAppIdentity = Depends(get_identity)) -> list[SlotOfferResponse]:
    container = get_container()
    _ensure_access_key(container, identity)
    grouped = container.miniapp.list_slot_offers_for_user(identity.telegram_id)
    return [
        SlotOfferResponse(
            id=offer.id,
            case_id=offer.case_id,
            created_by_admin_id=offer.created_by_admin_id,
            status=offer.status,
            message=offer.message,
            expires_at=offer.expires_at,
            created_at=offer.created_at,
            updated_at=offer.updated_at,
            options=[SlotOptionResponse.model_validate(option) for option in options],
        )
        for offer, options in grouped
    ]


@app.post("/api/case/current/slot-options/{option_id}/select", response_model=CaseResponse)
async def select_slot_option(option_id: str, identity: MiniAppIdentity = Depends(get_identity)) -> CaseResponse:
    container = get_container()
    _ensure_access_key(container, identity)
    try:
        visa_case, _ = container.miniapp.select_slot_option_for_user(identity.telegram_id, option_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = CaseResponse.model_validate(visa_case)
    await _notify_slot_selected(container, identity, response)
    return response


@app.post("/api/case/applicants-count", response_model=CaseResponse)
async def set_applicants_count(payload: ApplicantsCountPayload, identity: MiniAppIdentity = Depends(get_identity)) -> CaseResponse:
    container = get_container()
    access_key = _ensure_access_key(container, identity)
    user = _ensure_user(container, identity)
    visa_case = container.miniapp.ensure_case(user, access_key.id, access_key.code)
    updated = container.miniapp.set_applicants_count(visa_case, payload.applicants_count)
    return CaseResponse.model_validate(updated)


@app.get("/api/applicants", response_model=list[ApplicantResponse])
async def list_applicants(identity: MiniAppIdentity = Depends(get_identity)) -> list[ApplicantResponse]:
    container = get_container()
    return [ApplicantResponse.model_validate(item) for item in container.miniapp.list_applicants(identity.telegram_id)]


@app.post("/api/applicants", response_model=ApplicantResponse)
async def create_applicant(identity: MiniAppIdentity = Depends(get_identity)) -> ApplicantResponse:
    container = get_container()
    access_key = _ensure_access_key(container, identity)
    user = _ensure_user(container, identity)
    visa_case = container.miniapp.ensure_case(user, access_key.id, access_key.code)
    profile = container.miniapp.create_applicant(visa_case)
    return ApplicantResponse.model_validate(profile)


@app.get("/api/applicants/{applicant_id}", response_model=ApplicantResponse)
async def get_applicant(applicant_id: str, identity: MiniAppIdentity = Depends(get_identity)) -> ApplicantResponse:
    container = get_container()
    profile = container.miniapp.get_applicant(identity.telegram_id, applicant_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Applicant profile not found.")
    return ApplicantResponse.model_validate(profile)


@app.patch("/api/applicants/{applicant_id}", response_model=ApplicantResponse)
async def update_applicant(applicant_id: str, payload: ApplicantProfilePayload, identity: MiniAppIdentity = Depends(get_identity)) -> ApplicantResponse:
    container = get_container()
    profile = container.miniapp.update_applicant(identity.telegram_id, applicant_id, payload.model_dump())
    if profile is None:
        raise HTTPException(status_code=404, detail="Applicant profile not found.")
    await _notify_if_profiles_completed(container, identity)
    return ApplicantResponse.model_validate(profile)


@app.post("/api/applicants/{applicant_id}/copy-from-primary", response_model=ApplicantResponse)
async def copy_from_primary(applicant_id: str, identity: MiniAppIdentity = Depends(get_identity)) -> ApplicantResponse:
    container = get_container()
    profile = container.miniapp.copy_from_primary(identity.telegram_id, applicant_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Applicant profile not found.")
    return ApplicantResponse.model_validate(profile)


@app.get("/api/case/current/documents", response_model=DocumentsListResponse)
async def current_case_documents(identity: MiniAppIdentity = Depends(get_identity)) -> DocumentsListResponse:
    container = get_container()
    visa_case = _get_current_case(container, identity)
    items = container.documents.list_by_case(visa_case.id, visible_to_client_only=True)
    return DocumentsListResponse(
        items=[_document_item_response(container, item) for item in items],
        uploads_enabled=container.document_storage.enabled,
    )


@app.get("/api/case/current/documents/summary", response_model=CabinetDocumentsSummary)
async def current_case_documents_summary(identity: MiniAppIdentity = Depends(get_identity)) -> CabinetDocumentsSummary:
    container = get_container()
    visa_case = _get_current_case(container, identity)
    summary = _build_documents_summary(container, visa_case)
    assert summary is not None
    return summary


@app.post("/api/case/current/documents/{document_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    document_id: str,
    file: UploadFile = File(...),
    identity: MiniAppIdentity = Depends(get_identity),
) -> DocumentUploadResponse:
    from io import BytesIO

    container = get_container()
    if not container.document_storage.enabled:
        raise HTTPException(status_code=501, detail="Загрузка файлов пока недоступна. Свяжитесь с менеджером.")
    visa_case = _get_current_case(container, identity)
    item = container.documents.get_for_case(visa_case.id, document_id)
    if item is None or not item.visible_to_client:
        raise HTTPException(status_code=404, detail="Документ не найден.")
    if not can_client_upload(item):
        raise HTTPException(status_code=400, detail="Этот документ сейчас нельзя загрузить.")

    content = await file.read()
    try:
        container.document_storage.save_upload(
            case_id=visa_case.id,
            document_item_id=document_id,
            uploaded_by=str(identity.telegram_id),
            filename=file.filename or "upload.bin",
            content_type=file.content_type,
            content=BytesIO(content),
            size_bytes=len(content),
            applicant_id=item.applicant_id,
        )
        updated = container.documents.mark_uploaded_by_client(document_id, str(identity.telegram_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _notify_client_uploaded(
        container,
        identity,
        visa_case,
        updated.title,
        updated.status,
    )
    return DocumentUploadResponse(
        document_id=updated.id,
        status=updated.status,
        status_label=document_status_label(updated),
        has_file=True,
    )


@app.post("/api/case/current/documents/{document_id}/comment", response_model=DocumentItemResponse)
async def comment_document(
    document_id: str,
    payload: DocumentCommentPayload,
    identity: MiniAppIdentity = Depends(get_identity),
) -> DocumentItemResponse:
    container = get_container()
    visa_case = _get_current_case(container, identity)
    item = container.documents.get_for_case(visa_case.id, document_id)
    if item is None or not item.visible_to_client:
        raise HTTPException(status_code=404, detail="Документ не найден.")

    try:
        if payload.no_insurance:
            updated, _ = container.documents.mark_insurance_not_available(
                visa_case.id,
                document_id,
                payload.comment or "У клиента нет своей страховки.",
            )
        else:
            updated = container.documents.add_client_comment(
                document_id,
                payload.comment,
                str(identity.telegram_id),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _document_item_response(container, updated)


@app.get("/api/case/current/documents/{document_id}/download")
async def download_document(document_id: str, identity: MiniAppIdentity = Depends(get_identity)) -> FileResponse:
    container = get_container()
    visa_case = _get_current_case(container, identity)
    item = container.documents.get_for_case(visa_case.id, document_id)
    if item is None or not item.visible_to_client:
        raise HTTPException(status_code=404, detail="Документ не найден.")

    active_file = container.documents.get_latest_active_file(document_id)
    has_file = active_file is not None
    if not can_client_download(item, has_file=has_file):
        raise HTTPException(status_code=403, detail="Документ пока недоступен для скачивания.")

    assert active_file is not None
    try:
        path = container.document_storage.open_file(active_file)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Файл не найден.") from exc

    return FileResponse(
        path,
        media_type=active_file.mime_type or "application/octet-stream",
        filename=active_file.original_filename,
    )
