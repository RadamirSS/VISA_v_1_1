from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime


@dataclass(slots=True)
class ParsedSlotOption:
    option_date: str
    option_time: str
    city: str | None = None
    provider: str | None = None
    comment: str | None = None


def _parse_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Некорректная дата: {raw}. Используйте формат YYYY-MM-DD.") from exc


def _parse_time(raw: str) -> str:
    try:
        return datetime.strptime(raw, "%H:%M").strftime("%H:%M")
    except ValueError as exc:
        raise ValueError(f"Некорректное время: {raw}. Используйте формат HH:MM.") from exc


def parse_slot_offer_lines(raw: str, *, today: date | None = None) -> list[ParsedSlotOption]:
    base_date = today or datetime.now(UTC).date()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Введите хотя бы один вариант даты.")
    if len(lines) > 10:
        raise ValueError("Можно отправить не более 10 вариантов за один раз.")

    seen: set[tuple[str, str, str | None, str | None]] = set()
    parsed: list[ParsedSlotOption] = []
    for line in lines:
        parts = [item.strip() for item in line.split("|")]
        head = parts[0].split()
        if len(head) != 2:
            raise ValueError(f"Не удалось разобрать строку: {line}")
        option_date = _parse_date(head[0])
        if option_date < base_date:
            raise ValueError(f"Дата уже в прошлом: {head[0]}")
        option_time = _parse_time(head[1])
        city = parts[1] if len(parts) > 1 and parts[1] else None
        provider = parts[2] if len(parts) > 2 and parts[2] else None
        comment = parts[3] if len(parts) > 3 and parts[3] else None
        dedupe_key = (option_date.isoformat(), option_time, city, provider)
        if dedupe_key in seen:
            raise ValueError(f"Обнаружен дубликат варианта: {head[0]} {head[1]}")
        seen.add(dedupe_key)
        parsed.append(
            ParsedSlotOption(
                option_date=option_date.isoformat(),
                option_time=option_time,
                city=city,
                provider=provider,
                comment=comment,
            )
        )
    return parsed
