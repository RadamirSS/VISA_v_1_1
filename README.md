# VISA_v_1_1

Репозиторий разделен на три приложения:

- `apps/web` — маркетинговый сайт и короткая форма первичной заявки.
- `apps/telegram-bot` — Telegram-бот для клиентского онбординга, ключей доступа, заявок на запись и менеджерского workflow.
- `apps/client-miniapp` — клиентский Telegram Mini App для заполнения профилей заявителей и создания визового кейса.

## Структура

```text
apps/
  web/
  telegram-bot/
  client-miniapp/
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

### Client Mini App

```bash
cd apps/client-miniapp
pnpm install
pnpm dev
```

Mini App backend API запускается отдельно:

```bash
cd apps/telegram-bot
uvicorn bot.api.main:app --host 0.0.0.0 --port 8100
```

Ключевой Mini App flow:

1. Клиент активирует ключ доступа в боте.
2. Заполняет анкеты заявителей в `apps/client-miniapp`.
3. Создает визовую заявку.
4. Выбирает страну, город подачи и визовый центр из `packages/visa-config`.
5. Менеджер вручную находит возможные даты записи вне системы.
6. Клиент получает варианты дат и выбирает один.
7. Менеджер подтверждает финальную запись.

Проверка бота:

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
```

Проверка Mini App:

```bash
cd apps/client-miniapp
pnpm typecheck
pnpm build
```

CI для бота находится в [telegram-bot-ci.yml](/Users/Radamir/Documents/VISA_v1/.github/workflows/telegram-bot-ci.yml), а для Mini App в [client-miniapp-ci.yml](/Users/Radamir/Documents/VISA_v1/.github/workflows/client-miniapp-ci.yml).

## Важные ограничения

- сайт не собирает паспортные данные, сканы документов и банковскую информацию
- сайт сохраняет лиды на сервере в `apps/web/storage/leads.jsonl` до попытки Telegram-уведомления
- бот не делает реальную запись через внешний booking API
- бот не использует онлайн-оплату; оплата проходит через менеджера агентства
- доступ к созданию заявки в боте открывается через ключ доступа от менеджера
- Telegram-бот не собирает паспортные данные
- паспортные данные для MVP вводятся только в `apps/client-miniapp` и хранятся только в backend database
- выбор страны и города подачи загружается из `packages/visa-config`, а не хардкодится во frontend
- Telegram-бот не собирает сканы документов
- Telegram-бот не собирает банковские выписки или bank statements
- Mini App API не должен логировать сырые анкеты, не должен отправлять чувствительные поля в Telegram и в production обязан работать через HTTPS
- менеджер получает только non-sensitive summary при отправке кейса
- Telegram уведомления по слотам содержат только case id, username/telegram_id, country/city/provider и дату/время
- `ENABLE_SENSITIVE_FIELDS` и `SENSITIVE_DATA_ENCRYPTION_KEY` зарезервированы для будущего secure backend flow и не должны включать сбор паспортных данных в Telegram-чате
- в репозитории нет реальных секретов, токенов и платежных ключей
- финальные решения всегда принимают консульства и уполномоченные визовые органы
