from pathlib import Path

from bot.services.config_loader import load_consulates, load_countries, load_price_tiers


def test_countries_load_from_shared_config():
    repo_root = Path(__file__).resolve().parents[3]
    countries = load_countries(repo_root)
    assert countries
    assert countries[0].code


def test_consulates_load_from_shared_config():
    repo_root = Path(__file__).resolve().parents[3]
    consulates = load_consulates(repo_root)
    assert consulates
    assert consulates[0].city


def test_price_tiers_load_from_shared_config():
    repo_root = Path(__file__).resolve().parents[3]
    price_tiers = load_price_tiers(repo_root)
    assert price_tiers
    assert price_tiers[0].code


def test_each_price_tier_has_additional_applicant_price():
    repo_root = Path(__file__).resolve().parents[3]
    price_tiers = load_price_tiers(repo_root)
    assert all(tier.additional_applicant_price_rub >= 0 for tier in price_tiers)
