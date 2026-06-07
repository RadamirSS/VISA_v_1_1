# VISA_v_1_1

Репозиторий разделен на два отдельных приложения:

- `apps/web` — маркетинговый сайт и короткая форма первичной заявки.
- `apps/telegram-bot` — фундамент Telegram-бота для рабочих заявок на поиск записи.

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

### Telegram bot

```bash
cd apps/telegram-bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bot.main
```

## Важные ограничения

- сайт не собирает паспортные данные, сканы документов и банковскую информацию
- бот не делает реальную запись через внешний booking API
- в репозитории нет реальных секретов, токенов и платежных ключей
- финальные решения всегда принимают консульства и уполномоченные визовые органы
