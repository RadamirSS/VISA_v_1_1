# Client Mini App Flow

## Зачем нужен Mini App

Mini App становится главным клиентским кабинетом. В нем клиент:

1. заполняет анкеты заявителей
2. создает визовую заявку
3. выбирает страну, город подачи и визовый центр
4. отправляет кейс менеджеру на ручную проверку

Это уводит длинные анкеты и чувствительные поля из Telegram-чата.

## Личный кабинет (главная)

Главная страница Mini App (`/`) использует backend source-of-truth API:

- `GET /api/cabinet/summary` — доступ, заявка, прогресс анкет, запись, следующий шаг
- `GET /api/case/current/timeline` — компактный preview хода заявки

На главной отображаются:

1. приветствие и статус доступа
2. основная визовая заявка (без сырых backend status codes)
3. карточка следующего шага
4. прогресс заполнения анкет
5. статус записи на подачу
6. подсказка о работе менеджера
7. preview timeline с переходом на `/status`

Пользователь **не видит** технические статусы вроде `slot_options_sent` или `profiles_completed` — только человекочитаемые `status_label` с backend.

## Основной пользовательский путь

1. Клиент получает ключ доступа от менеджера.
2. Активирует его в Telegram-боте.
3. Открывает `📋 Открыть личный кабинет`.
4. Заполняет анкеты заявителей.
5. Открывает `/case/new`.
6. Выбирает страну, город подачи, визовый центр, цель поездки и примерные даты.
7. Проверяет summary на `/case/review`.
8. Отправляет заявку менеджеру.
9. Получает варианты дат в Telegram и в `/appointment`.
10. Выбирает одну дату.
11. Ждет финального подтверждения менеджера.
12. Открывает `/documents` для чек-листа документов (загрузка от клиента и статусы документов агентства).

Нижняя навигация: **Главная · Анкеты · Заявка · Запись · Документы**. Настройки доступны по ссылке на главной (`/settings`).

## Telegram initData auth

- production использует `initData` от Telegram Mini App
- backend валидирует `initData` через `MINIAPP_BOT_TOKEN`
- API всегда ограничивает данные текущим Telegram ID
- dev auth допустим только при `MINIAPP_DEV_AUTH=true`

## Источники country/city/provider data

- страны загружаются из `packages/visa-config/countries.ru.json`
- города и визовые центры загружаются из `packages/visa-config/consulates.ru.json`
- frontend не должен хардкодить эти списки

## verificationStatus

- `verified` означает, что текущий вариант уже подтвержден в seed config
- `needs_verification` означает, что менеджер должен дополнительно проверить актуальность города или визового центра

Mini App показывает предупреждение для `needs_verification` и не скрывает такие опции.

## Безопасность

- паспортные и адресные данные вводятся только в Mini App
- они не отправляются в Telegram-сообщения
- manager notification содержит только case summary
- raw applicant payload нельзя логировать
- production требует HTTPS, encryption-at-rest, access control и Postgres

## Ограничения текущего этапа

- нет real booking integration
- нет online payment integration
- document upload через Mini App API доступен только при `DOCUMENT_UPLOADS_ENABLED=true` (локальное хранилище для MVP)
- нет PDF generation
- нет manager dashboard
- SQLite используется только как MVP storage
- выбранная дата не считается финально подтвержденной, пока менеджер не подтвердит запись

См. также [DOCUMENT_REQUEST_CHECKLIST.md](DOCUMENT_REQUEST_CHECKLIST.md).

## Pilot QA

- [PILOT_QA_CHECKLIST.md](PILOT_QA_CHECKLIST.md)
- [PILOT_READINESS.md](PILOT_READINESS.md)
