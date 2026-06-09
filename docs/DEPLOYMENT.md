# Deployment

## Components

В этом MVP деплоятся:

1. `apps/web`
2. `apps/telegram-bot`
3. `apps/telegram-bot/bot/api`
4. `apps/client-miniapp`

## Required env for Mini App flow

- `CLIENT_MINIAPP_URL`
- `MINIAPP_BOT_TOKEN`
- `MINIAPP_ALLOWED_ORIGIN`
- `MINIAPP_DEV_AUTH=false` в production

## Document upload env (optional MVP)

- `DOCUMENT_UPLOADS_ENABLED=false` по умолчанию
- `DOCUMENT_STORAGE_DIR=./storage/documents`
- `DOCUMENT_MAX_FILE_MB=15`

См. [DOCUMENT_REQUEST_CHECKLIST.md](DOCUMENT_REQUEST_CHECKLIST.md) и [PILOT_READINESS.md](PILOT_READINESS.md).

## Production notes

- Mini App и API публикуются только через HTTPS
- SQLite допустим только для локального MVP и внутреннего пилота
- production rollout требует Postgres
- нужен encryption-at-rest
- нужен access control для manager-side tooling
- нельзя логировать applicant payloads
- нельзя отправлять passport/document/bank data в Telegram
- document files for MVP are stored locally under `apps/telegram-bot/storage/documents/` when upload is enabled; production requires object storage, encryption, ACL, backups, retention, audit logging
- нет прямой интеграции с внешними booking API: менеджерские слоты вводятся вручную

## Local verification

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
uvicorn bot.api.main:app --host 0.0.0.0 --port 8100
```

```bash
cd apps/client-miniapp
pnpm install
pnpm typecheck
pnpm build
pnpm dev
```
