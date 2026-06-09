from __future__ import annotations

from datetime import date

import pytest

from bot.services.slot_offers import parse_slot_offer_lines


def test_parse_simple_multiline_options() -> None:
    parsed = parse_slot_offer_lines("2026-07-15 10:30\n2026-07-16 14:00", today=date(2026, 7, 1))

    assert len(parsed) == 2
    assert parsed[0].option_time == "10:30"


def test_parse_extended_multiline_options() -> None:
    parsed = parse_slot_offer_lines(
        "2026-07-15 10:30 | Москва | VMS Italy | Комментарий",
        today=date(2026, 7, 1),
    )

    assert parsed[0].city == "Москва"
    assert parsed[0].provider == "VMS Italy"


@pytest.mark.parametrize(
    "raw, message",
    [
        ("2026-15-07 10:30", "Некорректная дата"),
        ("2026-07-15 25:30", "Некорректное время"),
        ("2026-06-01 10:30", "Дата уже в прошлом"),
        ("", "Введите хотя бы один вариант"),
    ],
)
def test_reject_invalid_values(raw: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_slot_offer_lines(raw, today=date(2026, 7, 1))


def test_reject_more_than_ten_options() -> None:
    raw = "\n".join([f"2026-07-{day:02d} 10:30" for day in range(1, 12)])
    with pytest.raises(ValueError, match="не более 10"):
        parse_slot_offer_lines(raw, today=date(2026, 7, 1))
