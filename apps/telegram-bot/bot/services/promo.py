from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from bot.models import PromoCode, PromoCodeType


@dataclass(slots=True)
class PromoResult:
    valid: bool
    normalized_code: str
    discount_rub: int = 0
    payment_status: Optional[str] = None
    promo_type: Optional[str] = None
    error: Optional[str] = None


def normalize_code(value: str) -> str:
    return value.strip().upper()


def validate_promo(promo: PromoCode, price_rub: int, country_code: str, time_window_code: str, now: Optional[datetime] = None) -> PromoResult:
    normalized = normalize_code(promo.code)
    current = now or datetime.now(UTC)

    if not promo.active:
        return PromoResult(valid=False, normalized_code=normalized, error="Промокод неактивен.")
    if promo.max_uses <= promo.used_count:
        return PromoResult(valid=False, normalized_code=normalized, error="Промокод исчерпан.")
    if promo.expires_at and datetime.fromisoformat(promo.expires_at) < current:
        return PromoResult(valid=False, normalized_code=normalized, error="Срок действия промокода истек.")
    if promo.country_codes and country_code not in promo.country_codes:
        return PromoResult(valid=False, normalized_code=normalized, error="Промокод не подходит для выбранной страны.")
    if promo.time_window_codes and time_window_code not in promo.time_window_codes:
        return PromoResult(valid=False, normalized_code=normalized, error="Промокод не подходит для выбранного окна поиска.")

    if promo.type == PromoCodeType.FULL_DISCOUNT:
        return PromoResult(valid=True, normalized_code=normalized, discount_rub=price_rub, payment_status="paid", promo_type=promo.type)
    if promo.type == PromoCodeType.CASH_PAID:
        return PromoResult(valid=True, normalized_code=normalized, discount_rub=price_rub, payment_status="paid_offline", promo_type=promo.type)
    if promo.type == PromoCodeType.PERCENT_DISCOUNT:
        discount = int(price_rub * (promo.value / 100))
        return PromoResult(valid=True, normalized_code=normalized, discount_rub=discount, promo_type=promo.type)
    if promo.type == PromoCodeType.FIXED_DISCOUNT:
        return PromoResult(valid=True, normalized_code=normalized, discount_rub=min(price_rub, promo.value), promo_type=promo.type)

    return PromoResult(valid=True, normalized_code=normalized, discount_rub=0, promo_type=promo.type)
