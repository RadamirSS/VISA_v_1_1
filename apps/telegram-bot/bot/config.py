from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import os


@dataclass(slots=True)
class Settings:
    bot_token: str
    bot_admin_ids: List[int]
    database_url: str
    payment_provider: str
    payment_provider_token: str
    booking_api_base_url: str
    booking_api_token: str
    enable_sensitive_fields: bool
    sensitive_data_encryption_key: str
    default_currency: str
    root_dir: Path
    repo_root: Path


def parse_admin_ids(raw: str) -> List[int]:
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[3]
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        bot_admin_ids=parse_admin_ids(os.getenv("BOT_ADMIN_IDS", "")),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./visa_bot.db"),
        payment_provider=os.getenv("PAYMENT_PROVIDER", "mock"),
        payment_provider_token=os.getenv("PAYMENT_PROVIDER_TOKEN", ""),
        booking_api_base_url=os.getenv("BOOKING_API_BASE_URL", ""),
        booking_api_token=os.getenv("BOOKING_API_TOKEN", ""),
        enable_sensitive_fields=parse_bool(os.getenv("ENABLE_SENSITIVE_FIELDS"), False),
        sensitive_data_encryption_key=os.getenv("SENSITIVE_DATA_ENCRYPTION_KEY", ""),
        default_currency=os.getenv("DEFAULT_CURRENCY", "RUB"),
        root_dir=root_dir,
        repo_root=repo_root,
    )
