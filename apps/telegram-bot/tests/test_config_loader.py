from pathlib import Path

from bot.services.config_loader import load_json


def test_load_json_reads_price_seed():
    path = Path(__file__).resolve().parents[1] / "data" / "seed_prices.ru.json"
    payload = load_json(path)
    assert isinstance(payload, list)
    assert payload[0]["code"] == "urgent"
