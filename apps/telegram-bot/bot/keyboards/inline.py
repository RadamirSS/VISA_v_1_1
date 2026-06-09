from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен, продолжить", callback_data="consent:accept")],
            [InlineKeyboardButton(text="❓ Подробнее", callback_data="consent:details")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="consent:cancel")],
        ]
    )


def admin_order_actions_keyboard(public_number: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Взять в работу", callback_data=f"admin:take:{public_number}")],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"admin:status:{public_number}")],
            [InlineKeyboardButton(text="💳 Подтвердить оплату наличными", callback_data=f"admin:cash:{public_number}")],
            [InlineKeyboardButton(text="✉️ Написать клиенту шаблонное сообщение", callback_data=f"admin:message:{public_number}")],
            [InlineKeyboardButton(text="❌ Отменить заявку", callback_data=f"admin:cancel:{public_number}")],
        ]
    )


def admin_status_keyboard(public_number: str) -> InlineKeyboardMarkup:
    statuses = [
        ("paid_waiting_booking", "Ожидает обработки"),
        ("sent_to_booking_provider", "Передана в обработку"),
        ("slot_found", "Слот найден"),
        ("slot_confirmation_pending", "Ждет подтверждения"),
        ("booked", "Записано"),
        ("needs_user_action", "Нужно действие клиента"),
        ("failed", "Неуспешно"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"admin:setstatus:{public_number}:{value}")]
            for value, label in statuses
        ]
    )


def admin_message_templates_keyboard(target_kind: str, target_id: str) -> InlineKeyboardMarkup:
    templates = [
        ("Проверяем заявку", "reviewing"),
        ("Нужны уточнения", "clarify"),
        ("Ожидаем слот", "waiting_slot"),
        ("Слот найден", "slot_found"),
        ("Запись подтверждена", "booked"),
        ("Свяжитесь с менеджером", "contact_manager"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"admin:template:{target_kind}:{target_id}:{template_code}",
                )
            ]
            for label, template_code in templates
        ]
    )


def support_request_actions_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏳ В работу", callback_data=f"support:status:{request_id}:in_progress")],
            [InlineKeyboardButton(text="✅ Закрыть", callback_data=f"support:status:{request_id}:closed")],
            [InlineKeyboardButton(text="✉️ Отправить шаблон", callback_data=f"support:message:{request_id}")],
        ]
    )


def slot_options_keyboard(options: list[tuple[str, str]], miniapp_url: str | None = None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=label, callback_data=f"slotselect:{option_id}")]
        for option_id, label in options
    ]
    if miniapp_url:
        keyboard.append([InlineKeyboardButton(text="Открыть в личном кабинете", url=miniapp_url)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def document_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Показать документы", callback_data="doc:action:list")],
            [InlineKeyboardButton(text="📥 Запросить у клиента", callback_data="doc:action:request")],
            [InlineKeyboardButton(text="🏢 Добавить документ агентства", callback_data="doc:action:agency")],
            [InlineKeyboardButton(text="📤 Загрузить файл агентства", callback_data="doc:action:upload")],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data="doc:action:status")],
            [InlineKeyboardButton(text="💬 Комментарий", callback_data="doc:action:comment")],
        ]
    )


def document_client_template_keyboard() -> InlineKeyboardMarkup:
    from bot.services.document_templates import list_manager_client_picks

    rows = [
        [InlineKeyboardButton(text=template.title, callback_data=f"doc:req:{template.category}")]
        for template in list_manager_client_picks()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def document_agency_template_keyboard() -> InlineKeyboardMarkup:
    from bot.services.document_templates import list_manager_agency_picks

    rows = [
        [InlineKeyboardButton(text=template.title, callback_data=f"doc:agency:{template.category}")]
        for template in list_manager_agency_picks()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def document_items_keyboard(items: list[tuple[str, str]], prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"doc:{prefix}:{item_id}")]
            for item_id, label in items
        ]
    )


def document_status_keyboard(source_type: str) -> InlineKeyboardMarkup:
    from bot.models import AgencyDocumentStatus, ClientDocumentStatus, DocumentSourceType

    if source_type == DocumentSourceType.CLIENT_REQUIRED.value:
        statuses = [
            (ClientDocumentStatus.REQUESTED.value, "Ожидаем от клиента"),
            (ClientDocumentStatus.RECEIVED_BY_MANAGER.value, "Получено менеджером"),
            (ClientDocumentStatus.APPROVED.value, "Принято"),
            (ClientDocumentStatus.REJECTED.value, "Нужно заменить"),
            (ClientDocumentStatus.NOT_NEEDED.value, "Не требуется"),
        ]
    else:
        statuses = [
            (AgencyDocumentStatus.PLANNED.value, "Запланировано"),
            (AgencyDocumentStatus.PREPARING_BY_AGENCY.value, "Готовит агентство"),
            (AgencyDocumentStatus.READY_FOR_CLIENT.value, "Готово"),
            (AgencyDocumentStatus.SHARED_WITH_CLIENT.value, "Передано клиенту"),
            (AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value, "Передан отдельно"),
            (AgencyDocumentStatus.NOT_NEEDED.value, "Не требуется"),
        ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"doc:setstatus:{status}")]
            for status, label in statuses
        ]
    )
