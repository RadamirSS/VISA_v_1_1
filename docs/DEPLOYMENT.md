# Deployment

## Website

1. Перейти в `apps/web`
2. Установить зависимости через `pnpm install`
3. Настроить `.env.local` по примеру `.env.example`
4. Запустить `pnpm build` и `pnpm start`

Переменные:

- `LEADS_TELEGRAM_BOT_TOKEN`
- `LEADS_TELEGRAM_CHAT_ID`
- `NEXT_PUBLIC_SITE_URL`

## Telegram bot

1. Перейти в `apps/telegram-bot`
2. Создать окружение Python
3. Установить зависимости `pip install -e .`
4. Настроить `.env` по примеру `.env.example`
5. Запустить `python -m bot.main`

Переменные:

- `BOT_TOKEN`
- `BOT_ADMIN_IDS`
- `DATABASE_URL`
- `PAYMENT_PROVIDER`
- `BOOKING_API_BASE_URL`
- `BOOKING_API_TOKEN`
- `ENABLE_SENSITIVE_FIELDS`
