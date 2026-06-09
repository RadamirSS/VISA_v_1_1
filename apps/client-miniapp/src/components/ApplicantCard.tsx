import Link from "next/link";

import { applicantStatusLabel } from "../lib/cabinet";
import type { ApplicantProfile } from "../lib/types";

export function ApplicantCard({ applicant }: { applicant: ApplicantProfile }) {
  const title = applicant.last_name_cyrillic || applicant.first_name_cyrillic
    ? `${applicant.last_name_cyrillic ?? ""} ${applicant.first_name_cyrillic ?? ""}`.trim()
    : `Заявитель ${applicant.position}`;

  const actionLabel = applicant.status === "completed" ? "Редактировать" : applicant.completion_percent === 0 ? "Заполнить" : "Продолжить";

  return (
    <article className="surface-card">
      <div className="card-row">
        <div>
          <p className="card-label">Заявитель {applicant.position}</p>
          <h3>{title}</h3>
          <p className="applicant-meta">
            {applicant.completion_percent}% · {applicantStatusLabel(applicant.status)}
          </p>
        </div>
      </div>
      <Link className="primary-button" href={`/applicants/${applicant.id}`}>
        {actionLabel}
      </Link>
    </article>
  );
}
