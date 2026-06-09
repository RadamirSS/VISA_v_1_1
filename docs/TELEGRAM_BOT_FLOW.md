# Telegram Bot Flow

Бот является отдельным deployable-приложением и главным интерфейсом для workflow по заявкам на поиск записи.

## Основные этапы

1. `/start` и онбординг
2. согласие на обработку данных
3. регистрация пользователя
4. создание заявки на запись
5. выбор страны
6. выбор города подачи и визового центра
7. выбор цели поездки
8. выбор окна поиска записи
9. выбор количества заявителей
10. ввод данных заявителей
11. промокод или продолжение без промокода
12. расчет цены
13. mock-оплата или отметка об офлайн-оплате
14. создание заявки менеджеру
15. `/status` или `📌 Мои заявки`

## Admin flow

- просмотр новых заявок
- создание промокодов
- подтверждение оплаты наличными
- ручное изменение статусов
- перевод заявки во внутренний mock booking stage

## Manual QA Script

1. Start bot.
2. Accept consent.
3. Register user.
4. Create appointment request.
5. Choose country.
6. Choose city.
7. Choose purpose.
8. Choose time window.
9. Add applicants.
10. Apply no promo / promo.
11. Complete mock payment.
12. Check `/status`.
13. Admin opens `/admin`.
14. Admin views new orders.
15. Admin changes order status.
16. User receives status notification.

## Ограничения

- real booking API пока не подключен
- real payment provider пока не подключен
- passport/document scans нельзя отправлять через Telegram-бота
- паспортные данные отключены по умолчанию и блокируются без ключа шифрования
- SQLite является MVP-хранилищем; production должен использовать Postgres
- admin IDs задаются через env
