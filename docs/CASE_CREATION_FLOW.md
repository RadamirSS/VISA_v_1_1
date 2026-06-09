# Case Creation Flow

## Цель

PR-VISA-07B связывает applicant profiles с реальным `visa_case` workflow.

## Этапы

1. Клиент завершает анкеты всех заявителей.
2. Открывает `/case/new`.
3. Выбирает страну Шенгена.
4. Выбирает город подачи и визовый центр из shared config.
5. Выбирает цель поездки.
6. Добавляет примерные даты и комментарий.
7. Проверяет summary на `/case/review`.
8. Отправляет кейс менеджеру.

## Consultation path

Если клиент выбирает:

- `Не знаю, нужна консультация`
- `Другая страна`

то кейс переходит в `needs_manager_consultation`, и выбор города не обязателен.

## Data sources

- `countries.ru.json`
- `consulates.ru.json`

## validation rules

- без access key кейс создать нельзя
- без completed applicant profiles кейс отправить нельзя
- без страны кейс отправить нельзя
- без города и провайдера нельзя отправить обычный case
- для consultation case город не обязателен
- без travel purpose кейс отправить нельзя
- locked case statuses не редактируются клиентом

## Manager notification

Менеджер получает только:

- case id
- telegram username / id
- applicants count
- country
- city
- provider
- travel purpose
- status

Чувствительные applicant fields в уведомление не попадают.

## Что происходит дальше

После создания и отправки кейса менеджер вручную ищет доступные даты записи вне системы. Этот поток описан в `MANAGER_SLOT_OFFERS_FLOW.md`.
