from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from random import choices
from string import ascii_uppercase, digits

from bot.models import AccessKey, AccessKeyStatus


@dataclass(slots=True)
class AccessKeyValidationResult:
    valid: bool
    error: str | None = None


def generate_access_key(prefix: str = "VISA") -> str:
    first = "".join(choices(ascii_uppercase, k=4))
    second = "".join(choices(ascii_uppercase + digits, k=4))
    return f"{prefix}-{first}-{second}"


def normalize_access_key(value: str) -> str:
    return value.strip().upper()


def validate_access_key(
    access_key: AccessKey | None,
    telegram_id: int,
    country_code: str | None = None,
    applicants_count: int | None = None,
    service_type: str | None = None,
    now: datetime | None = None,
) -> AccessKeyValidationResult:
    current = now or datetime.now(UTC)
    if access_key is None:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа не найден.")
    if access_key.status == AccessKeyStatus.REVOKED.value:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа отозван.")
    if access_key.status == AccessKeyStatus.CONSUMED.value:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа уже использован.")
    if access_key.expires_at and datetime.fromisoformat(access_key.expires_at) < current:
        return AccessKeyValidationResult(valid=False, error="Срок действия ключа доступа истек.")
    if access_key.used_count >= access_key.max_uses:
        return AccessKeyValidationResult(valid=False, error="Лимит использований ключа доступа исчерпан.")
    if access_key.bound_telegram_id and access_key.bound_telegram_id != telegram_id:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа уже привязан к другому Telegram-пользователю.")
    if country_code and access_key.country_codes and country_code not in access_key.country_codes:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа не подходит для выбранной страны.")
    if applicants_count and access_key.max_applicants and applicants_count > access_key.max_applicants:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа не покрывает такое количество заявителей.")
    if service_type and access_key.service_type and access_key.service_type != service_type:
        return AccessKeyValidationResult(valid=False, error="Ключ доступа не подходит для выбранной услуги.")
    if access_key.status == AccessKeyStatus.EXPIRED.value:
        return AccessKeyValidationResult(valid=False, error="Срок действия ключа доступа истек.")
    return AccessKeyValidationResult(valid=True)
