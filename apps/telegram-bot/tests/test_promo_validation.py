from datetime import UTC, datetime, timedelta

from bot.models import PromoCode, PromoCodeType
from bot.services.promo import validate_promo


def make_promo(**overrides):
    payload = {
        "id": "promo-1",
        "code": "sale20",
        "type": PromoCodeType.PERCENT_DISCOUNT,
        "value": 20,
        "max_uses": 5,
        "used_count": 0,
        "active": True,
        "created_by_admin_id": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "country_codes": [],
        "time_window_codes": [],
        "note": None,
    }
    payload.update(overrides)
    return PromoCode(**payload)


def test_percent_discount_promo():
    promo = make_promo()
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is True
    assert result.discount_rub == 2000


def test_expired_promo_rejected():
    promo = make_promo(expires_at=(datetime.now(UTC) - timedelta(days=1)).isoformat())
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is False


def test_inactive_promo_rejected():
    promo = make_promo(active=False)
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is False


def test_overused_promo_rejected():
    promo = make_promo(used_count=5, max_uses=5)
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is False


def test_cash_paid_promo_changes_payment_status():
    promo = make_promo(type=PromoCodeType.CASH_PAID, value=0)
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is True
    assert result.payment_status == "paid_offline"


def test_full_discount_sets_payable_amount_to_zero():
    promo = make_promo(type=PromoCodeType.FULL_DISCOUNT, value=0)
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is True
    assert result.discount_rub == 10000
    assert result.payment_status == "paid"


def test_country_restricted_promo_rejects_wrong_country():
    promo = make_promo(country_codes=["FR"])
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is False


def test_time_window_restricted_promo_rejects_wrong_tier():
    promo = make_promo(time_window_codes=["urgent"])
    result = validate_promo(promo, 10000, "IT", "two_weeks")
    assert result.valid is False
