from bot.services.order_factory import OrderInput, create_order


def test_create_order_generates_public_number():
    order = create_order(
        OrderInput(
            user_id="user-1",
            country_code="IT",
            country_name_ru="Италия",
            submission_city="Москва",
            provider="Provider",
            visa_purpose="Туризм",
            time_window_code="two_weeks",
            applicants_count=2,
            base_price_rub=14900,
            additional_applicants_price_rub=1500,
            discount_rub=0,
            total_price_rub=16400,
            promo_code=None,
            payment_status="pending",
            order_status="awaiting_payment",
            requires_manager_review=False,
        ),
        sequence=123,
    )
    assert order.public_number.endswith("000123")
    assert order.total_price_rub == 16400
    assert order.manager_note is None
