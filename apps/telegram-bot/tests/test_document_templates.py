from __future__ import annotations

from bot.models import DocumentCategory, DocumentSourceType
from bot.services.document_templates import (
    AGENCY_PREPARED_TEMPLATES,
    CLIENT_REQUIRED_TEMPLATES,
    get_template,
    list_agency_templates,
    list_client_templates,
)


def test_client_required_templates_exist() -> None:
    assert len(list_client_templates()) >= 10


def test_agency_prepared_templates_exist() -> None:
    assert len(list_agency_templates()) >= 9


def test_passport_photo_bank_insurance_are_client_required() -> None:
    for category in (
        DocumentCategory.INTERNATIONAL_PASSPORT,
        DocumentCategory.PHOTO,
        DocumentCategory.BANK_STATEMENT,
        DocumentCategory.INSURANCE_OWN,
    ):
        template = get_template(category.value)
        assert template is not None
        assert template.source_type == DocumentSourceType.CLIENT_REQUIRED.value


def test_hotel_invitation_form_are_agency_prepared() -> None:
    for category in (
        DocumentCategory.HOTEL_BOOKING,
        DocumentCategory.INVITATION,
        DocumentCategory.FILLED_APPLICATION_FORM,
    ):
        template = get_template(category.value)
        assert template is not None
        assert template.source_type == DocumentSourceType.AGENCY_PREPARED.value


def test_all_templates_have_titles() -> None:
    for template in (*CLIENT_REQUIRED_TEMPLATES, *AGENCY_PREPARED_TEMPLATES):
        assert template.title
        assert template.category
