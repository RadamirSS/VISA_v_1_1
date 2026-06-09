# Pilot Readiness

Документ описывает, что готово для внутреннего пилота и что ещё не является production-ready.

Связанные документы:

- [PILOT_QA_CHECKLIST.md](PILOT_QA_CHECKLIST.md) — ручной сценарий проверки
- [DEPLOYMENT.md](DEPLOYMENT.md) — деплой и env

## Ready for internal pilot

- website lead flow;
- manager-driven access keys;
- Mini App applicant profiles;
- visa case creation;
- city/provider selection;
- manager queue/workspace;
- documents checklist;
- client document upload MVP;
- agency document upload MVP;
- manual slot offers;
- client date selection;
- appointment confirmation;
- status timeline.

## Not production-ready yet

- local file storage only;
- no encryption-at-rest;
- no antivirus scanning;
- no production object storage;
- no full audit trail for file downloads;
- no real visa-center API;
- no online payments;
- no automated booking;
- no PDF export;
- no full manager web dashboard;
- no SLA/slot/visa guarantees.

## Pilot limitations copy

Сервис помогает агентству организовать сбор данных, документов и коммуникацию с клиентом.

Доступность дат зависит от внешних визовых систем.

Финальное решение по визе принимает консульство или уполномоченный визовый орган.

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

Автоматические pilot-тесты:

- `apps/telegram-bot/tests/test_pilot_end_to_end_flow.py`
- `apps/telegram-bot/tests/test_pilot_security_redaction.py`
- `apps/telegram-bot/tests/test_pilot_readiness_checks.py`
