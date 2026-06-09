from __future__ import annotations

import re

from bot.models import OrderStatus, PaymentStatus

_PROVIDER_SUFFIX = re.compile(r"\s*/\s*provider to verify$", re.IGNORECASE)


PAYMENT_STATUS_LABELS: dict[str, str] = {
    PaymentStatus.NOT_REQUIRED.value: "не требуется",
    PaymentStatus.PENDING.value: "ожидает оплаты",
    PaymentStatus.PAID.value: "оплачена",
    PaymentStatus.PAID_OFFLINE.value: "оплата подтверждена агентством",
    PaymentStatus.FAILED.value: "ошибка оплаты",
    PaymentStatus.CANCELLED.value: "отменена",
    PaymentStatus.REFUNDED.value: "возврат",
}

ORDER_STATUS_LABELS: dict[str, str] = {
    OrderStatus.DRAFT.value: "черновик",
    OrderStatus.AWAITING_PAYMENT.value: "ожидает оплаты",
    OrderStatus.AWAITING_MANAGER_CASH_CONFIRMATION.value: "ожидает подтверждения оплаты",
    OrderStatus.REQUIRES_MANAGER_REVIEW.value: "на проверке менеджера",
    OrderStatus.PAID_WAITING_BOOKING.value: "в работе у менеджера",
    OrderStatus.SENT_TO_BOOKING_PROVIDER.value: "менеджер подбирает даты",
    OrderStatus.SLOT_FOUND.value: "найдены варианты дат",
    OrderStatus.SLOT_CONFIRMATION_PENDING.value: "запись подтверждается",
    OrderStatus.BOOKED.value: "запись подтверждена",
    OrderStatus.NEEDS_USER_ACTION.value: "нужны действия от вас",
    OrderStatus.CANCELLED.value: "отменена",
    OrderStatus.FAILED.value: "не выполнена",
    OrderStatus.REFUNDED.value: "возврат",
}


def format_provider_display_name(provider: str | None) -> str:
    if not provider:
        return ""
    cleaned = _PROVIDER_SUFFIX.sub("", provider).strip()
    if cleaned.lower().endswith("visa center"):
        country = cleaned.rsplit(" ", 2)[0]
        return f"Визовый центр {country}"
    return cleaned


def payment_status_label(status: str) -> str:
    return PAYMENT_STATUS_LABELS.get(status, "статус уточняется")


def order_status_label(status: str) -> str:
    return ORDER_STATUS_LABELS.get(status, "статус уточняется")
