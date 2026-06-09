from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from bot.models import DocumentCategory, DocumentSourceType


@dataclass(frozen=True, slots=True)
class DocumentTemplate:
    category: str
    source_type: str
    title: str
    description: str
    required: bool = True


CLIENT_REQUIRED_TEMPLATES: tuple[DocumentTemplate, ...] = (
    DocumentTemplate(
        category=DocumentCategory.INTERNATIONAL_PASSPORT.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Загранпаспорт",
        description="Загрузите разворот с фото.",
        required=True,
    ),
    DocumentTemplate(
        category=DocumentCategory.PHOTO.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Фото",
        description="Требования уточнит менеджер.",
        required=True,
    ),
    DocumentTemplate(
        category=DocumentCategory.BANK_STATEMENT.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Выписка из банка",
        description="Загрузите актуальную выписку по счёту.",
        required=True,
    ),
    DocumentTemplate(
        category=DocumentCategory.INSURANCE_OWN.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Страховка",
        description=(
            "Если у вас уже есть своя страховка, загрузите её. "
            "Если страховки нет, агентство может подготовить её отдельно."
        ),
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.EMPLOYMENT_CERTIFICATE.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Справка с работы",
        description="Загрузите справку с места работы.",
        required=True,
    ),
    DocumentTemplate(
        category=DocumentCategory.STUDENT_CERTIFICATE.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Справка из учебного заведения",
        description="Загрузите справку из учебного заведения.",
        required=True,
    ),
    DocumentTemplate(
        category=DocumentCategory.MARRIAGE_CERTIFICATE.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Свидетельство о браке",
        description="Загрузите свидетельство о браке.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.CHILD_BIRTH_CERTIFICATE.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Свидетельство о рождении ребёнка",
        description="Загрузите свидетельство о рождении ребёнка.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.PREVIOUS_VISAS.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Предыдущие визы",
        description="Загрузите копии предыдущих виз при наличии.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.OTHER_CLIENT_DOCUMENT.value,
        source_type=DocumentSourceType.CLIENT_REQUIRED.value,
        title="Другой документ",
        description="Загрузите документ по запросу менеджера.",
        required=False,
    ),
)

AGENCY_PREPARED_TEMPLATES: tuple[DocumentTemplate, ...] = (
    DocumentTemplate(
        category=DocumentCategory.HOTEL_BOOKING.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Бронь отеля",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.TRANSPORT_BOOKING.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Бронь транспорта",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.INVITATION.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Приглашение",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.TRAVEL_PLAN.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="План поездки",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.FILLED_APPLICATION_FORM.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Заполненная анкета",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.APPOINTMENT_CONFIRMATION.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Подтверждение записи",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.INSURANCE_AGENCY_PREPARED.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Страховка от агентства",
        description="Страховку подготовит агентство.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.COVER_LETTER.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Сопроводительное письмо",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
    DocumentTemplate(
        category=DocumentCategory.OTHER_AGENCY_DOCUMENT.value,
        source_type=DocumentSourceType.AGENCY_PREPARED.value,
        title="Другой документ агентства",
        description="Документ готовит агентство и добавит его по мере готовности.",
        required=False,
    ),
)

_MANAGER_CLIENT_PICKS = (
    DocumentCategory.INTERNATIONAL_PASSPORT,
    DocumentCategory.PHOTO,
    DocumentCategory.BANK_STATEMENT,
    DocumentCategory.INSURANCE_OWN,
    DocumentCategory.EMPLOYMENT_CERTIFICATE,
    DocumentCategory.OTHER_CLIENT_DOCUMENT,
)

_MANAGER_AGENCY_PICKS = (
    DocumentCategory.HOTEL_BOOKING,
    DocumentCategory.TRANSPORT_BOOKING,
    DocumentCategory.INVITATION,
    DocumentCategory.FILLED_APPLICATION_FORM,
    DocumentCategory.INSURANCE_AGENCY_PREPARED,
    DocumentCategory.OTHER_AGENCY_DOCUMENT,
)

_TEMPLATES_BY_CATEGORY = {
    template.category: template for template in (*CLIENT_REQUIRED_TEMPLATES, *AGENCY_PREPARED_TEMPLATES)
}


def get_template(category: str) -> Optional[DocumentTemplate]:
    return _TEMPLATES_BY_CATEGORY.get(category)


def list_client_templates() -> list[DocumentTemplate]:
    return list(CLIENT_REQUIRED_TEMPLATES)


def list_agency_templates() -> list[DocumentTemplate]:
    return list(AGENCY_PREPARED_TEMPLATES)


def list_manager_client_picks() -> list[DocumentTemplate]:
    return [get_template(category.value) for category in _MANAGER_CLIENT_PICKS if get_template(category.value)]


def list_manager_agency_picks() -> list[DocumentTemplate]:
    return [get_template(category.value) for category in _MANAGER_AGENCY_PICKS if get_template(category.value)]


def resolve_title(category: str, custom_title: Optional[str] = None) -> str:
    template = get_template(category)
    if custom_title and category in {
        DocumentCategory.OTHER_CLIENT_DOCUMENT.value,
        DocumentCategory.OTHER_AGENCY_DOCUMENT.value,
    }:
        return custom_title.strip()
    return template.title if template else category
