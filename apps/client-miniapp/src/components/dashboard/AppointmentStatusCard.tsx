import Link from "next/link";

import { formatAppointmentDate, formatProviderDisplayName } from "../../lib/cabinet";
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
        <h3>Запись подтверждена менеджером</h3>
        <p className="muted-text">Проверьте детали в личном кабинете.</p>
        <p className="appointment-date">{formatAppointmentDate(confirmed.date, confirmed.time)}</p>
        {expanded && (confirmed.city || confirmed.provider) ? (
          <p className="muted-text">
            {[confirmed.city, formatProviderDisplayName(confirmed.provider)].filter(Boolean).join(" · ")}
          </p>
        ) : null}
        {!expanded && confirmed.city && confirmed.provider ? (
          <p className="muted-text">
            {confirmed.city} · {formatProviderDisplayName(confirmed.provider)}
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
        <p className="muted-text">Менеджер проверяет и подтверждает запись.</p>
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
        <p className="muted-text">Выберите удобный вариант из предложенных менеджером дат.</p>
        <Link className="primary-button" href="/appointment">
          Выбрать дату
        </Link>
      </section>
    );
  }

  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Запись</p>
      <h3>Менеджер подбирает доступные даты</h3>
      <p className="muted-text">Мы уведомим вас, когда варианты появятся.</p>
      {expanded ? (
        <Link className="secondary-button" href="/appointment">
          Открыть раздел записи
        </Link>
      ) : null}
    </section>
  );
}
