# Pilot QA Checklist

Пошаговый сценарий для внутреннего пилота MVP визового агентства.

Связанные документы:

- [PILOT_READINESS.md](PILOT_READINESS.md) — готовность и ограничения пилота
- [PILOT_RELEASE_NOTES.md](PILOT_RELEASE_NOTES.md) — release notes и go/no-go
- [MANAGER_OPERATIONS_FLOW.md](MANAGER_OPERATIONS_FLOW.md) — менеджерский workflow
- [CLIENT_MINIAPP_FLOW.md](CLIENT_MINIAPP_FLOW.md) — клиентский Mini App flow

Автоматические тесты:

- `apps/telegram-bot/tests/test_pilot_end_to_end_flow.py`
- `apps/telegram-bot/tests/test_pilot_security_redaction.py`
- `apps/telegram-bot/tests/test_pilot_readiness_checks.py`
- `apps/telegram-bot/tests/test_trust_copy_safety.py`
- `apps/telegram-bot/tests/test_pilot_release_readiness.py`

## Setup

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
```

```bash
cd apps/client-miniapp
pnpm typecheck
pnpm build
```

## Local run

Терминал 1 — Telegram bot:

```bash
cd apps/telegram-bot
python -m bot.main
```

Терминал 2 — Mini App API:

```bash
cd apps/telegram-bot
uvicorn bot.api.main:app --host 0.0.0.0 --port 8100
```

Терминал 3 — Client Mini App:

```bash
cd apps/client-miniapp
pnpm dev
```

Перед пилотом проверьте `.env` бота: `BOT_TOKEN`, `BOT_ADMIN_IDS`, `CLIENT_MINIAPP_URL`, `MINIAPP_BOT_TOKEN`, `MINIAPP_ALLOWED_ORIGIN`, `MINIAPP_DEV_AUTH=true` (только для локального теста).

## Website lead flow

1. Запустите сайт: `pnpm dev:web` (или проверьте production build).
2. Откройте `/apply` и убедитесь, что на странице есть disclaimer о том, что виза и запись не гарантируются.
3. Отправьте тестовую заявку с минимально необходимыми полями.
4. Проверьте запись в `apps/web/storage/leads.jsonl`.
5. Опционально: при настроенных `LEADS_TELEGRAM_BOT_TOKEN` и `LEADS_TELEGRAM_CHAT_ID` проверьте уведомление в Telegram.

```bash
cd apps/web
pnpm typecheck
pnpm build
```

## Manager flow

1. Откройте бота под admin-аккаунтом.
2. Откройте `/admin`.
3. Создайте ключ доступа.
4. Отправьте ключ тестовому клиенту.
5. Откройте **📥 Новые заявки**.
6. Найдите кейс по публичному номеру через **🔎 Найти заявку**.
7. Откройте case workspace.
8. Запросите документы (паспорт / фото).
9. Добавьте документ агентства (бронь отеля / приглашение).
10. Отправьте варианты дат записи.
11. Подтвердите запись после выбора клиента.

## Client flow

1. Откройте бота обычным пользователем.
2. Введите ключ доступа.
3. Откройте Mini App.
4. Заполните анкеты заявителей.
5. Создайте визовую заявку.
6. Выберите страну, город подачи и визовый центр.
7. Загрузите запрошенные документы.
8. Проверьте документы агентства в разделе «Документы».
9. Выберите дату записи из предложенных вариантов.
10. Убедитесь, что запись подтверждена в личном кабинете.

## Expected result

В конце клиент должен видеть в timeline / личном кабинете:

- Анкеты заполнены
- Заявка отправлена менеджеру
- Документы запрошены / загружены
- Даты отправлены
- Дата выбрана
- Запись подтверждена

## Smoke check (optional)

```bash
cd apps/telegram-bot
python scripts/pilot_smoke_check.py
```

Ожидаемый вывод: `PILOT_SMOKE_OK`
