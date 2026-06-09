from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bot.models import ConsulateOption, CountryOption, PriceTier


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_countries(repo_root: Path) -> list[CountryOption]:
    payload = load_json(repo_root / "packages" / "visa-config" / "countries.ru.json")
    return [
        CountryOption(
            code=item["code"],
            slug=item["slug"],
            name_ru=item["nameRu"],
            suits_for_ru=item["suitsForRu"],
        )
        for item in payload
    ]


def load_consulates(repo_root: Path) -> list[ConsulateOption]:
    payload = load_json(repo_root / "packages" / "visa-config" / "consulates.ru.json")
    return [
        ConsulateOption(
            country_code=item["countryCode"],
            country_name_ru=item["countryNameRu"],
            city=item["city"],
            provider=item["provider"],
            type=item["type"],
            jurisdiction=item["jurisdiction"],
            status=item["status"],
            verification_status=item["verificationStatus"],
            last_checked_at=item["lastCheckedAt"],
            source_note=item["sourceNote"],
        )
        for item in payload
    ]


def load_price_tiers(repo_root: Path) -> list[PriceTier]:
    payload = load_json(repo_root / "packages" / "visa-config" / "price-tiers.ru.json")
    return [
        PriceTier(
            code=item["code"],
            label_ru=item["labelRu"],
            description_ru=item["descriptionRu"],
            price_rub=item["priceRub"],
            priority=item["priority"],
            additional_applicant_price_rub=item["additionalApplicantPriceRub"],
        )
        for item in payload
    ]


def find_country_by_name(countries: list[CountryOption], name_ru: str) -> CountryOption | None:
    return next((country for country in countries if country.name_ru == name_ru), None)


def find_consulates_by_country(consulates: list[ConsulateOption], country_code: str) -> list[ConsulateOption]:
    return [item for item in consulates if item.country_code == country_code]


def find_price_tier(price_tiers: list[PriceTier], code: str) -> PriceTier | None:
    return next((tier for tier in price_tiers if tier.code == code), None)
