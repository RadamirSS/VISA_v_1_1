from __future__ import annotations

import re
from pathlib import Path

from bot.handlers import admin as admin_handlers
from bot.handlers.order import shared as order_shared
from bot.handlers import status as status_handlers
from bot.services.notifications import (
    build_appointment_confirmed_message,
    build_documents_requested_message,
    build_slot_options_message,
    build_user_case_submitted_message,
    build_user_slot_selected_message,
)
from bot.services.trust_display import format_provider_display_name, order_status_label, payment_status_label
from bot.texts import common as common_texts

REPO_ROOT = Path(__file__).resolve().parents[3]
MINIAPP_SRC = REPO_ROOT / "apps" / "client-miniapp" / "src"

FORBIDDEN_POSITIVE_CLAIMS = [
    "гарантируем визу",
    "гарантированная виза",
    "гарантируем запись",
    "обход очереди",
    "официальный доступ",
    "100%",
    "автоматически записываем",
]

FORBIDDEN_TECHNICAL_TOKENS = [
    "mock",
    "debug",
    "provider to verify",
    "submitted_for_manager_review",
    "slot_options_sent",
    "appointment_confirmed",
    "case flow",
    "booking api",
]

NEGATION_PREFIXES = ("не ", "нет ", "not ")


def _assert_no_positive_forbidden(text: str) -> None:
    lowered = text.lower()
    for phrase in FORBIDDEN_POSITIVE_CLAIMS:
        if phrase in lowered:
            index = lowered.index(phrase)
            prefix = lowered[max(0, index - 4) : index]
            if any(prefix.endswith(prefix_item) for prefix_item in NEGATION_PREFIXES):
                continue
            raise AssertionError(f"Forbidden positive claim '{phrase}' found in: {text!r}")


def _assert_no_technical_tokens(text: str) -> None:
    lowered = text.lower()
    for token in FORBIDDEN_TECHNICAL_TOKENS:
        assert token not in lowered, f"Forbidden technical token '{token}' found in: {text!r}"


def _client_notification_samples() -> list[str]:
    return [
        common_texts.PRIVACY_NOTE,
        common_texts.HOW_IT_WORKS,
        common_texts.SENSITIVE_NOTE,
        build_user_case_submitted_message(),
        build_slot_options_message(),
        build_user_slot_selected_message("2026-07-15", "10:30"),
        build_appointment_confirmed_message(
            "2026-07-15",
            "10:30",
            "Москва",
            "Italy visa center / provider to verify",
        ),
        build_documents_requested_message(),
    ]


def test_client_notification_builders_are_trust_safe() -> None:
    for text in _client_notification_samples():
        _assert_no_positive_forbidden(text)
        _assert_no_technical_tokens(text)


def test_admin_client_dm_strings_do_not_leak_mock_or_raw_status() -> None:
    source = Path(admin_handlers.__file__).read_text(encoding="utf-8")
    client_dm_fragments = [
        line.strip()
        for line in source.splitlines()
        if "send_message" in line and "telegram_id" in line and "f\"" in line
    ]
    assert client_dm_fragments, "Expected client DM strings in admin handlers"
    for fragment in client_dm_fragments:
        _assert_no_technical_tokens(fragment)
        assert "mock" not in fragment.lower()


def test_finalize_order_message_uses_human_status_labels() -> None:
    source = Path(order_shared.__file__).read_text(encoding="utf-8")
    assert "payment_status_label" in source
    assert "order_status_label" in source
    assert "{order.payment_status}" not in source
    assert "{order.order_status}" not in source


def test_status_handler_uses_human_labels() -> None:
    source = Path(status_handlers.__file__).read_text(encoding="utf-8")
    assert "payment_status_label" in source
    assert "order_status_label" in source
    assert 'f"Оплата: {order[\'payment_status\']}"' not in source
    assert 'f"Статус: {order[\'order_status\']}"' not in source


def test_format_provider_display_name_strips_placeholder_suffix() -> None:
    assert format_provider_display_name("Italy visa center / provider to verify") == "Визовый центр Italy"
    assert format_provider_display_name("France visa center / provider to verify") == "Визовый центр France"
    assert "provider to verify" not in format_provider_display_name("Spain visa center / provider to verify").lower()


def test_order_and_payment_status_labels_are_human_readable() -> None:
    assert "_" not in payment_status_label("paid_offline")
    assert "_" not in order_status_label("requires_manager_review")
    assert order_status_label("paid_waiting_booking") == "в работе у менеджера"


def test_miniapp_source_has_no_forbidden_client_tokens() -> None:
    patterns = [
        *FORBIDDEN_TECHNICAL_TOKENS,
        "Telegram Mini App",
        "case flow",
    ]
    skip_paths = {
        MINIAPP_SRC / "lib" / "cabinet.ts",
        MINIAPP_SRC / "lib" / "types.ts",
    }
    for path in MINIAPP_SRC.rglob("*"):
        if path.suffix not in {".tsx", ".ts"} or path in skip_paths:
            continue
        content = path.read_text(encoding="utf-8").lower()
        for pattern in patterns:
            assert pattern not in content, f"{pattern!r} found in {path.relative_to(REPO_ROOT)}"


def test_miniapp_source_has_no_positive_forbidden_claims() -> None:
    for path in MINIAPP_SRC.rglob("*"):
        if path.suffix not in {".tsx", ".ts"}:
            continue
        _assert_no_positive_forbidden(path.read_text(encoding="utf-8"))


def test_how_it_works_mentions_visa_systems_not_booking_api() -> None:
    text = common_texts.HOW_IT_WORKS.lower()
    assert "booking api" not in text
    assert "визовых систем" in text
