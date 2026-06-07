from bot.services.pricing import calculate_total


def test_price_calculation_with_additional_applicant():
    result = calculate_total(14900, applicants_count=2, additional_applicant_fee_rub=1500, discount_rub=0)
    assert result.base_price_rub == 14900
    assert result.additional_applicants_price_rub == 1500
    assert result.total_price_rub == 16400


def test_price_calculation_marks_manual_review_for_large_group():
    result = calculate_total(4900, applicants_count=5, additional_applicant_fee_rub=1500, discount_rub=0)
    assert result.requires_manager_review is True


def test_price_calculation_applies_discount():
    result = calculate_total(14900, applicants_count=2, additional_applicant_fee_rub=1500, discount_rub=2000)
    assert result.discount_rub == 2000
    assert result.total_price_rub == 14400
