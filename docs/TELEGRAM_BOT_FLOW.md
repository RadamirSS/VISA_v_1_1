# Telegram Bot Flow

Бот является отдельным deployable-приложением и главным интерфейсом для workflow по заявкам на поиск записи.

## Основные этапы

1. `/start` и онбординг
2. согласие на обработку данных
3. регистрация пользователя
4. активация ключа доступа от менеджера
5. создание заявки на запись
6. выбор страны
7. выбор города подачи и визового центра
8. выбор цели поездки
9. выбор окна поиска записи
10. выбор количества заявителей
11. ввод данных заявителей
12. подтверждение заявки
13. создание заявки менеджеру как `paid_offline`
14. `/status` или `📌 Мои заявки`

## Admin flow

- просмотр новых заявок
- создание ключей доступа
- просмотр запросов клиентов
- создание промокодов
- подтверждение оплаты наличными
- ручное изменение статусов
- перевод заявки во внутренний mock booking stage

## Manual QA Script

1. Start bot.
2. Accept consent.
3. Register user.
4. Activate access key.
5. Create appointment request.
6. Choose country.
7. Choose city.
8. Choose purpose.
9. Choose time window.
10. Add applicants.
11. Confirm order without in-bot payment.
12. Check `/status`.
13. Admin opens `/admin`.
14. Admin creates access key and views new orders.
15. Admin changes order status or sends template message.
16. User receives status/template notification.

## Ограничения

- real booking API пока не подключен
- real payment provider пока не подключен и не используется в текущем user flow
- ключ доступа является основным production-механизмом авторизации клиента
- Telegram-бот не собирает паспортные данные
- Telegram-бот не собирает сканы документов
- Telegram-бот не собирает банковские выписки или bank statements
- `ENABLE_SENSITIVE_FIELDS` и `SENSITIVE_DATA_ENCRYPTION_KEY` зарезервированы для будущего secure backend flow и не включают сбор паспортных данных в текущем MVP
- если паспортные или документные данные понадобятся, менеджер должен запросить их через отдельный защищенный канал или будущий secure backend/storage flow
- SQLite является MVP-хранилищем; production должен использовать Postgres
- admin IDs задаются через env
