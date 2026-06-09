# Telegram Bot

Рабочий MVP Telegram-бота для клиентского взаимодействия агентства: онбординг, регистрация, активация ключа доступа, создание заявки на запись, статусы, менеджерское меню и backend API для клиентского Mini App.

## Что умеет бот

- `/start`, `/menu`, `/help`, `/status`, `/cancel`, `/admin`
- согласие на обработку данных и регистрация пользователя
- активация ключа доступа от менеджера
- кнопка `📋 Открыть личный кабинет` для запуска клиентского Mini App
- backend endpoints для country/city/provider selection и case submission
- ручной manager flow для отправки вариантов дат и подтверждения записи
- FSM-сценарий создания заявки на запись
- FastAPI backend для Mini App (`bot.api.main:app`)
- config-driven выбор страны, города подачи и окна поиска
- расчет цены с доп. заявителями
- офлайн-оплата через менеджера и manager-driven access key flow
- сохранение пользователей, заявок, заявителей, платежей и аудита в SQLite
- менеджерское меню с очередью заявок, поиском, ключами доступа, запросами клиентов, статусами, промокодами и статистикой
- `📥 Новые заявки` — группированная очередь Mini App кейсов (сводка + до 10 карточек **Открыть**) + старые order-based заявки
- **case workspace** — сводка кейса и inline-действия (анкеты, документы, даты, статус, сообщения)
- `🔎 Найти заявку` — поиск по `VISA-2026-*`, `VISA-CASE-*`, UUID, telegram_id, username
- менеджер может отправить даты из workspace или через `📅 Отправить даты`
- менеджер управляет документами из workspace или через `📎 Документы по заявке`

Документация:

- [../../docs/MANAGER_OPERATIONS_FLOW.md](../../docs/MANAGER_OPERATIONS_FLOW.md)
- [../../docs/TELEGRAM_BOT_FLOW.md](../../docs/TELEGRAM_BOT_FLOW.md)
- [../../docs/DOCUMENT_REQUEST_CHECKLIST.md](../../docs/DOCUMENT_REQUEST_CHECKLIST.md)
- [../../docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md)
- [../../docs/PILOT_QA_CHECKLIST.md](../../docs/PILOT_QA_CHECKLIST.md)
- [../../docs/PILOT_READINESS.md](../../docs/PILOT_READINESS.md)

## Безопасность и ограничения

- реальный booking API пока не подключен, `BookingProvider` работает как mock/adapter placeholder
- онлайн-оплата в боте не используется
- оплата проходит через менеджера агентства вне Telegram-бота
- бот не обещает слот, визу или доступ к внешним системам
- Telegram-бот не собирает паспортные данные
- паспортные данные теперь можно вводить только в Mini App и его backend API
- submitted case notification не содержит паспорт, адрес, место рождения и другие чувствительные поля
- slot notifications также не содержат чувствительные поля анкеты
- Telegram-бот не собирает сканы документов
- Telegram-бот не собирает банковские выписки или bank statements
- `ENABLE_SENSITIVE_FIELDS` и `SENSITIVE_DATA_ENCRYPTION_KEY` зарезервированы для будущего secure backend flow и не должны включать сбор паспортных данных в Telegram MVP
- если паспортные или документные данные когда-либо понадобятся, менеджер должен запросить их через отдельный защищенный канал или будущий secure backend/storage flow
- SQLite подходит только для MVP и внутреннего пилота; для production нужен Postgres
- production Mini App API обязан использовать HTTPS, encryption-at-rest и строгий access control
- менеджерские права задаются только через `BOT_ADMIN_IDS`

## Переменные окружения

- `BOT_TOKEN`
- `BOT_ADMIN_IDS`
- `DATABASE_URL`
- `PAYMENT_PROVIDER`
- `PAYMENT_PROVIDER_TOKEN`
- `BOOKING_API_BASE_URL`
- `BOOKING_API_TOKEN`
- `CLIENT_MINIAPP_URL`
- `MINIAPP_BOT_TOKEN`
- `MINIAPP_ALLOWED_ORIGIN`
- `MINIAPP_DEV_AUTH`
- `DOCUMENT_UPLOADS_ENABLED`
- `DOCUMENT_STORAGE_DIR`
- `DOCUMENT_MAX_FILE_MB`
- `ENABLE_SENSITIVE_FIELDS`
- `SENSITIVE_DATA_ENCRYPTION_KEY`
- `DEFAULT_CURRENCY`

## Локальный запуск

```bash
cd apps/telegram-bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m bot.main
```

Локальный запуск API:

```bash
cd apps/telegram-bot
uvicorn bot.api.main:app --host 0.0.0.0 --port 8100
```

## Проверка

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
```

CI запускает `python -m compileall bot` и `pytest` для `apps/telegram-bot` на `push` и `pull_request`.

## Manual QA

Полный пилотный сценарий: [../../docs/PILOT_QA_CHECKLIST.md](../../docs/PILOT_QA_CHECKLIST.md)

Опциональный smoke check:

```bash
cd apps/telegram-bot
python scripts/pilot_smoke_check.py
```

1. Запустить бота.
2. Выполнить `/start`.
3. Принять согласие на обработку данных.
4. Завершить регистрацию пользователя.
5. Активировать `🔑 Ввести ключ доступа`.
6. Нажать `📝 Создать заявку на запись`.
7. Выбрать страну.
8. Выбрать город подачи.
9. Выбрать цель поездки.
10. Выбрать окно поиска.
11. Добавить одного или нескольких заявителей.
12. Подтвердить заявку без оплаты в боте.
13. Проверить `/status` и `📌 Мои заявки`.
14. Открыть `/admin` под менеджерским аккаунтом.
15. Создать новый ключ доступа.
16. Проверить `📥 Новые заявки` — группы кейсов и кнопку **Открыть**.
17. Открыть case workspace, проверить сводку и действия (анкеты, документы, даты).
18. Проверить `🔎 Найти заявку` по public number и telegram_id.
19. Изменить статус кейса или отправить шаблонное сообщение клиенту.
20. Убедиться, что пользователь получил уведомление.
