import { AppShell } from "../../components/AppShell";

export default function SettingsPage() {
  return (
    <AppShell title="Профиль" subtitle="Памятка по безопасности и текущим ограничениям Mini App.">
      <section className="surface-card">
        <h3>Как мы работаем с данными</h3>
        <ul className="plain-list">
          <li>Паспортные данные вводятся только в Mini App, а не в Telegram-чате.</li>
          <li>В Telegram менеджеру отправляется только статус готовности анкет без чувствительных полей.</li>
          <li>Для production обязательны HTTPS, контроль доступа, шифрование на уровне хранения и переход на Postgres.</li>
        </ul>
      </section>
      <section className="surface-card">
        <h3>Текущий этап MVP</h3>
        <p className="muted-text">
          Доступен чек-лист документов в разделе «Документы». Загрузка файлов зависит от настроек backend. Оплата, PDF и
          полноценный менеджерский интерфейс пока не реализованы.
        </p>
      </section>
    </AppShell>
  );
}
