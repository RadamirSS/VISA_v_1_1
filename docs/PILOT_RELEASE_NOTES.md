# Pilot Release Notes — PR-VISA-10

Закрытый пилот MVP визового агентства: личный кабинет, менеджерский workflow и документооборот без автоматического бронирования.

Связанные документы:

- [PILOT_QA_CHECKLIST.md](PILOT_QA_CHECKLIST.md) — ручной сценарий проверки
- [PILOT_READINESS.md](PILOT_READINESS.md) — готовность и ограничения
- [DEPLOYMENT.md](DEPLOYMENT.md) — деплой и env

## What is ready

- website lead flow;
- Telegram bot (клиентский и менеджерский);
- client Mini App (личный кабинет);
- manager queue / case workspace;
- document checklist (клиент + агентство);
- client document upload MVP;
- agency document delivery MVP;
- manual slot offers;
- client date selection;
- appointment confirmation;
- status timeline;
- pilot QA / E2E / trust-copy tests.

## How to use in closed pilot

1. Запустите 3–5 тестовых или первых реальных клиентов.
2. Менеджер должен контролировать каждый шаг: ключ доступа → анкеты → заявка → документы → даты → подтверждение.
3. Держите резервный канал связи (Telegram / телефон) на случай сбоев Mini App.
4. Не обещайте гарантированную визу или гарантированную запись.
5. Проверяйте все документы вручную перед передачей клиенту или в визовый центр.

## Known limitations

- local file storage only;
- no encryption-at-rest;
- no antivirus scanning;
- no production object storage;
- no audit trail for file downloads;
- no real visa-center booking API;
- no online payments;
- no PDF export;
- no full manager web dashboard.

## Verification commands

```bash
cd apps/telegram-bot
python -m compileall bot
pytest
python scripts/pilot_smoke_check.py
```

```bash
cd apps/client-miniapp
pnpm typecheck
pnpm build
```

```bash
cd apps/web
pnpm typecheck
pnpm build
```

Ожидаемый вывод smoke check: `PILOT_SMOKE_OK`

## Go / no-go criteria

### Go for closed pilot

- bot starts;
- API starts;
- Mini App builds and opens from Telegram;
- access key works;
- case creation works;
- document upload works;
- agency document download works;
- slot offer / selection works;
- appointment confirmation works;
- manager can operate case from workspace;
- client-facing copy is trust-oriented (no raw status codes, no forbidden guarantee claims).

### No-go

- Mini App does not open from Telegram;
- uploads fail;
- users can access another user's data;
- manager cannot find cases;
- statuses show raw codes to clients;
- sensitive data appears in Telegram messages.

## Recommended next package

- If pilot polish is green: **PR-VISA-11** — Closed Pilot Deployment + Monitoring Checklist
- If QA finds runtime issues: **PR-VISA-10B** — Pilot Bugfix Pack
