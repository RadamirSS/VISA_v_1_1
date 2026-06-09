from __future__ import annotations

import asyncio

from bot.handlers.order import summary as summary_module
from bot.models import PaymentStatus


class DummyState:
    def __init__(self, data: dict):
        self.data = data
        self.cleared = False
        self.next_state = None

    async def get_data(self):
        return self.data

    async def clear(self):
        self.cleared = True

    async def set_state(self, state):
        self.next_state = state


class DummyMessage:
    def __init__(self, text: str):
        self.text = text
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


def test_summary_confirmation_finalizes_paid_offline_without_payment_provider(monkeypatch):
    captured = {}

    async def fake_finalize_order(message, state, payment_status, order_status, payment_provider_name="mock", provider_payment_id=None, paid_at=None, manager_note=None):
        captured["payment_status"] = payment_status
        captured["order_status"] = order_status
        captured["payment_provider_name"] = payment_provider_name
        captured["provider_payment_id"] = provider_payment_id
        captured["manager_note"] = manager_note

    monkeypatch.setattr(summary_module, "finalize_order", fake_finalize_order)
    state = DummyState(
        {
            "requires_manager_review": False,
            "access_key_code": "VISA-ABCD-1234",
            "access_key_id": "ak-1",
            "country_name_ru": "Италия",
            "submission_city": "Москва",
            "visa_purpose": "Туризм",
            "time_window_label": "За 2-3 недели",
            "applicants_count": 1,
            "base_price_rub": 14900,
            "additional_applicants_price_rub": 0,
            "discount_rub": 0,
            "total_price_rub": 14900,
        }
    )
    message = DummyMessage("✅ Подтвердить заявку")
    asyncio.run(summary_module.summary_step(message, state))
    assert captured["payment_status"] == PaymentStatus.PAID_OFFLINE.value
    assert captured["payment_provider_name"] == "offline_manager"
    assert captured["provider_payment_id"] == "VISA-ABCD-1234"
