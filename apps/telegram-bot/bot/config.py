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
    client_miniapp_url: str = ""
    miniapp_bot_token: str = ""
    miniapp_allowed_origin: str = ""
    miniapp_dev_auth: bool = False
    payment_provider: str = "mock"
    payment_provider_token: str = ""
    booking_api_base_url: str = ""
    booking_api_token: str = ""
    enable_sensitive_fields: bool = False
    sensitive_data_encryption_key: str = ""
    document_uploads_enabled: bool = False
    document_storage_dir: Path = Path("./storage/documents")
    document_max_file_mb: int = 15
    default_currency: str = "RUB"
    root_dir: Path = Path(".")
    repo_root: Path = Path(".")


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
        client_miniapp_url=os.getenv("CLIENT_MINIAPP_URL", ""),
        miniapp_bot_token=os.getenv("MINIAPP_BOT_TOKEN", ""),
        miniapp_allowed_origin=os.getenv("MINIAPP_ALLOWED_ORIGIN", ""),
        miniapp_dev_auth=parse_bool(os.getenv("MINIAPP_DEV_AUTH"), False),
        payment_provider=os.getenv("PAYMENT_PROVIDER", "mock"),
        payment_provider_token=os.getenv("PAYMENT_PROVIDER_TOKEN", ""),
        booking_api_base_url=os.getenv("BOOKING_API_BASE_URL", ""),
        booking_api_token=os.getenv("BOOKING_API_TOKEN", ""),
        enable_sensitive_fields=parse_bool(os.getenv("ENABLE_SENSITIVE_FIELDS"), False),
        sensitive_data_encryption_key=os.getenv("SENSITIVE_DATA_ENCRYPTION_KEY", ""),
        document_uploads_enabled=parse_bool(os.getenv("DOCUMENT_UPLOADS_ENABLED"), False),
        document_storage_dir=Path(os.getenv("DOCUMENT_STORAGE_DIR", str(root_dir / "storage" / "documents"))),
        document_max_file_mb=int(os.getenv("DOCUMENT_MAX_FILE_MB", "15")),
        default_currency=os.getenv("DEFAULT_CURRENCY", "RUB"),
        root_dir=root_dir,
        repo_root=repo_root,
    )
