# visa-config

Общие конфиги для сайта и Telegram-бота:

- `countries.ru.json` — страны и контент для сайта.
- `consulates.ru.json` — seed-список городов и визовых центров с `verificationStatus`.
- `price-tiers.ru.json` — конфиг тарифов, окон поиска записи и стоимости доп. заявителя.

Эти файлы не должны дублироваться в хендлерах или UI-кнопках как hardcoded-списки. Публичный сайт использует `countries.ru.json` для country-страниц и безопасных дисклеймеров без обещаний по визе или записи, а Telegram-бот читает их как config-driven источники для страны, города и pricing flow.
