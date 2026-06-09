import Link from "next/link";

import type { CabinetSummary } from "../../lib/types";

export function CaseOverviewCard({ summary }: { summary: CabinetSummary }) {
  const visaCase = summary.case;

  if (!summary.access.active) {
    return null;
  }

  if (!visaCase) {
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Визовая заявка</p>
        <h3>У вас пока нет визовой заявки</h3>
        <p className="muted-text">Заполните анкеты заявителей и создайте заявку.</p>
        <Link className="primary-button" href="/case/new">
          Создать заявку
        </Link>
      </section>
    );
  }

  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Визовая заявка</p>
      <div className="card-row">
        <div>
          <h3>{visaCase.desired_country_name_ru ?? "Текущая заявка"}</h3>
          <ul className="case-facts">
            {visaCase.desired_country_name_ru ? <li>Страна: {visaCase.desired_country_name_ru}</li> : null}
            {visaCase.preferred_submission_city ? <li>Город подачи: {visaCase.preferred_submission_city}</li> : null}
            {visaCase.submission_provider ? <li>Визовый центр: {visaCase.submission_provider}</li> : null}
            <li>Заявителей: {visaCase.applicants_count}</li>
            <li>Статус: {visaCase.status_label}</li>
          </ul>
        </div>
        <span className="status-chip success">{visaCase.status_label}</span>
      </div>
      <Link className="primary-button" href="/case">
        Открыть заявку
      </Link>
    </section>
  );
}
