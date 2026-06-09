import Link from "next/link";

import { formatAppointmentDate } from "../../lib/cabinet";
import type { CabinetSummary } from "../../lib/types";

type AppointmentStatusCardProps = {
  appointment: CabinetSummary["appointment"];
  expanded?: boolean;
};

export function AppointmentStatusCard({ appointment, expanded = false }: AppointmentStatusCardProps) {
  const confirmed = appointment.confirmed;
  const selected = appointment.selected;

  if (confirmed?.date) {
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Запись</p>
        <h3>Запись подтверждена</h3>
        <p className="appointment-date">{formatAppointmentDate(confirmed.date, confirmed.time)}</p>
        {expanded && (confirmed.city || confirmed.provider) ? (
          <p className="muted-text">
            {[confirmed.city, confirmed.provider].filter(Boolean).join(" · ")}
          </p>
        ) : null}
        {!expanded && confirmed.city && confirmed.provider ? (
          <p className="muted-text">
            {confirmed.city} · {confirmed.provider}
          </p>
        ) : null}
      </section>
    );
  }

  if (selected?.date) {
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Запись</p>
        <h3>Вы выбрали дату</h3>
        <p className="appointment-date">{formatAppointmentDate(selected.date, selected.time)}</p>
        <p className="muted-text">Ожидаем финального подтверждения менеджера.</p>
        {expanded ? (
          <Link className="secondary-button" href="/appointment">
            Открыть запись
          </Link>
        ) : null}
      </section>
    );
  }

  if (appointment.has_options) {
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Запись</p>
        <h3>Менеджер отправил варианты дат</h3>
        <p className="muted-text">Выберите удобную дату.</p>
        <Link className="primary-button" href="/appointment">
          Выбрать дату
        </Link>
      </section>
    );
  }

  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Запись</p>
      <h3>Менеджер подбирает даты</h3>
      <p className="muted-text">Когда варианты появятся, вы получите уведомление в Telegram.</p>
      {expanded ? (
        <Link className="secondary-button" href="/appointment">
          Открыть раздел записи
        </Link>
      ) : null}
    </section>
  );
}
