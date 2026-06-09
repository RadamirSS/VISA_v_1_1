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

Хранилище лидов:

- `apps/web/storage/leads.jsonl`
- файл создается автоматически при первой успешной записи
- если Telegram недоступен, статус уведомления фиксируется в следующей записи с тем же `id`

## Telegram bot

1. Перейти в `apps/telegram-bot`
2. Создать окружение Python
3. Установить зависимости `pip install -e .`
4. Настроить `.env` по примеру `.env.example`
5. Запустить `python -m bot.main`
6. Для проверки перед запуском использовать `python -m compileall bot` и `pytest`
7. Для CI в GitHub используется workflow `telegram-bot-ci.yml`

Переменные:

- `BOT_TOKEN`
- `BOT_ADMIN_IDS`
- `DATABASE_URL`
- `PAYMENT_PROVIDER`
- `BOOKING_API_BASE_URL`
- `BOOKING_API_TOKEN`
- `ENABLE_SENSITIVE_FIELDS`
- `SENSITIVE_DATA_ENCRYPTION_KEY`
- `NEXT_PUBLIC_SITE_URL`

Примечания по runtime:

- `PAYMENT_PROVIDER=mock` должен оставаться значением по умолчанию для внутреннего пилота
- booking-переходы сейчас mock-only и не выполняют реальное бронирование
- если включить `ENABLE_SENSITIVE_FIELDS=true` без `SENSITIVE_DATA_ENCRYPTION_KEY`, бот не должен собирать паспортные данные

## Manual QA перед деплоем

1. Запустить бота локально или на staging.
2. Пройти `/start`, consent и регистрацию.
3. Создать новую заявку.
4. Проверить ветку без промокода.
5. Проверить ветку с валидным промокодом.
6. Завершить mock payment.
7. Проверить `/status`.
8. Под админом открыть `/admin`.
9. Просмотреть `📥 Новые заявки`.
10. Изменить статус заявки и проверить пользовательское уведомление.
