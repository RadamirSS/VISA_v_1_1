from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from bot.config import Settings
from bot.models import MiniAppIdentity
from bot.repositories.users import UserRepository


def _parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def _build_data_check_string(parsed: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()) if key != "hash")


def validate_init_data(init_data: str, bot_token: str) -> dict[str, str]:
    parsed = _parse_init_data(init_data)
    expected_hash = parsed.get("hash")
    if not expected_hash:
        raise HTTPException(status_code=401, detail="Telegram initData is missing hash.")
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    check_string = _build_data_check_string(parsed)
    calculated = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, expected_hash):
        raise HTTPException(status_code=401, detail="Telegram initData validation failed.")
    return parsed


def resolve_identity(
    settings: Settings,
    users: UserRepository,
    authorization: str | None,
    x_telegram_init_data: str | None,
    x_dev_telegram_id: str | None,
    x_dev_username: str | None,
    x_dev_first_name: str | None,
    x_dev_last_name: str | None,
) -> MiniAppIdentity:
    init_data = x_telegram_init_data
    if authorization and authorization.lower().startswith("tma "):
        init_data = authorization[4:]
    if init_data:
        if not settings.miniapp_bot_token:
            raise HTTPException(status_code=500, detail="MINIAPP_BOT_TOKEN is not configured.")
        parsed = validate_init_data(init_data, settings.miniapp_bot_token)
        user_blob = parsed.get("user")
        if not user_blob:
            raise HTTPException(status_code=401, detail="Telegram initData has no user payload.")
        user_data = json.loads(user_blob)
        user = users.upsert_from_telegram(
            telegram_id=int(user_data["id"]),
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
        )
        return MiniAppIdentity(
            telegram_id=user.telegram_id,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    if settings.miniapp_dev_auth:
        if not x_dev_telegram_id:
            raise HTTPException(status_code=401, detail="Dev auth requires X-Dev-Telegram-Id.")
        user = users.upsert_from_telegram(
            telegram_id=int(x_dev_telegram_id),
            username=x_dev_username,
            first_name=x_dev_first_name,
            last_name=x_dev_last_name,
        )
        return MiniAppIdentity(
            telegram_id=user.telegram_id,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    raise HTTPException(status_code=401, detail="Mini App authentication is required.")


def identity_to_dict(identity: MiniAppIdentity) -> dict[str, str | int | None]:
    return asdict(identity)


async def get_identity(
    authorization: str | None = Header(default=None),
    x_telegram_init_data: str | None = Header(default=None),
    x_dev_telegram_id: str | None = Header(default=None),
    x_dev_username: str | None = Header(default=None),
    x_dev_first_name: str | None = Header(default=None),
    x_dev_last_name: str | None = Header(default=None),
):
    from bot.api.main import get_container

    container = get_container()
    return resolve_identity(
        container.settings,
        container.users,
        authorization,
        x_telegram_init_data,
        x_dev_telegram_id,
        x_dev_username,
        x_dev_first_name,
        x_dev_last_name,
    )
