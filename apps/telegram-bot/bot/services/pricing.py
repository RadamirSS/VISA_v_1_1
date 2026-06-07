from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PriceCalculation:
    base_price_rub: int
    additional_applicants_price_rub: int
    discount_rub: int
    total_price_rub: int
    requires_manager_review: bool


def calculate_total(base_price_rub: int, applicants_count: int, additional_applicant_fee_rub: int, discount_rub: int = 0, max_applicants_before_manual_review: int = 4) -> PriceCalculation:
    additional_count = max(applicants_count - 1, 0)
    additional_price = additional_count * additional_applicant_fee_rub
    subtotal = base_price_rub + additional_price
    total = max(subtotal - discount_rub, 0)
    return PriceCalculation(
        base_price_rub=base_price_rub,
        additional_applicants_price_rub=additional_price,
        discount_rub=min(discount_rub, subtotal),
        total_price_rub=total,
        requires_manager_review=applicants_count > max_applicants_before_manual_review,
    )
