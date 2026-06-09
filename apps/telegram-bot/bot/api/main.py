from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from bot.api.auth import get_identity
from bot.api.schemas import (
    ApplicantProfilePayload,
    ApplicantResponse,
    ApplicantsCountPayload,
    CasePayload,
    CaseResponse,
    CaseSubmitResponse,
    ConsulateOptionResponse,
    CountryOptionResponse,
    CreateCaseResponse,
    MeResponse,
    SlotOfferResponse,
    SlotOptionResponse,
    TelegramValidationResponse,
)
from bot.config import Settings, get_settings
from bot.database import init_db
from bot.models import MiniAppIdentity, User, VisaCaseStatus
from bot.repositories.access_keys import AccessKeyRepository
from bot.repositories.miniapp import CONSULTATION_COUNTRY_CODE, MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.notifications import (
    build_appointment_confirmed_message,
    build_case_submitted_notification,
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


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        settings = get_settings()
        init_db(settings.database_url)
        _container = Container(
            settings=settings,
            users=UserRepository(settings.database_url),
            access_keys=AccessKeyRepository(settings.database_url),
            miniapp=MiniAppRepository(settings.database_url, repo_root=settings.repo_root),
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
