from pathlib import Path

from bot.services.config_loader import load_countries, load_json, load_price_tiers


def test_load_json_reads_price_seed():
    path = Path(__file__).resolve().parents[1] / "data" / "seed_prices.ru.json"
    payload = load_json(path)
    assert isinstance(payload, list)
    assert payload[0]["code"] == "urgent"


def test_repo_config_loader_reads_package_data():
    repo_root = Path(__file__).resolve().parents[3]
    countries = load_countries(repo_root)
    price_tiers = load_price_tiers(repo_root)
    assert countries[0].code == "IT"
    assert price_tiers[0].additional_applicant_price_rub == 1500
