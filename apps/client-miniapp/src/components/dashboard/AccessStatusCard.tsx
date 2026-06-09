import { closeTelegramMiniApp } from "../../lib/telegram";
import type { CabinetSummary } from "../../lib/types";

export function AccessStatusCard({ access }: { access: CabinetSummary["access"] }) {
  if (access.active) {
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Доступ</p>
        <div className="card-row">
          <div>
            <h3>Доступ активирован</h3>
            <p className="muted-text">Вы можете заполнить анкеты и отслеживать заявку.</p>
          </div>
          <span className="status-chip active">{access.status_label}</span>
        </div>
      </section>
    );
  }

  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Доступ</p>
      <div className="card-row">
        <div>
          <h3>Доступ не активирован</h3>
          <p className="muted-text">Для продолжения нужен ключ доступа от менеджера агентства.</p>
        </div>
        <span className="status-chip inactive">{access.status_label}</span>
      </div>
      <button className="primary-button" onClick={closeTelegramMiniApp} type="button">
        Вернуться в бот
      </button>
    </section>
  );
}
