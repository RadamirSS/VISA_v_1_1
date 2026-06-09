# VISA_v_1_1

Репозиторий разделен на два отдельных приложения:

- `apps/web` — маркетинговый сайт и короткая форма первичной заявки.
- `apps/telegram-bot` — Telegram-бот для клиентского онбординга, ключей доступа, заявок на запись и менеджерского workflow.

## Структура

```text
apps/
  web/
  telegram-bot/
packages/
  visa-config/
docs/
```

## Быстрый старт

### Website

```bash
pnpm install
pnpm dev:web
```

Для production-сборки сайта:

```bash
cd apps/web
pnpm install
pnpm lint
pnpm typecheck
pnpm build
```

### Telegram bot

```bash
cd apps/telegram-bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bot.main
```

Проверка бота:

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
```

CI для бота находится в [`.github/workflows/telegram-bot-ci.yml`](/Users/Radamir/Documents/VISA_v1/.github/workflows/telegram-bot-ci.yml).

## Важные ограничения

- сайт не собирает паспортные данные, сканы документов и банковскую информацию
- сайт сохраняет лиды на сервере в `apps/web/storage/leads.jsonl` до попытки Telegram-уведомления
- бот не делает реальную запись через внешний booking API
- бот не использует онлайн-оплату; оплата проходит через менеджера агентства
- доступ к созданию заявки в боте открывается через ключ доступа от менеджера
- Telegram-бот не собирает паспортные данные
- Telegram-бот не собирает сканы документов
- Telegram-бот не собирает банковские выписки или bank statements
- `ENABLE_SENSITIVE_FIELDS` и `SENSITIVE_DATA_ENCRYPTION_KEY` зарезервированы для будущего secure backend flow и не должны включать сбор паспортных данных в текущем MVP
- в репозитории нет реальных секретов, токенов и платежных ключей
- финальные решения всегда принимают консульства и уполномоченные визовые органы
