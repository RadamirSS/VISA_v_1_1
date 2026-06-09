import Link from "next/link";

import type { ApplicantProfile } from "../lib/types";
import { ProgressBadge } from "./ProgressBadge";

const statusLabels: Record<string, string> = {
  draft: "Черновик",
  incomplete: "Черновик",
  completed: "Заполнено",
  needs_review: "На проверке",
  approved_by_manager: "Проверено"
};

export function ApplicantCard({ applicant }: { applicant: ApplicantProfile }) {
  const title = applicant.last_name_cyrillic || applicant.first_name_cyrillic
    ? `${applicant.last_name_cyrillic ?? ""} ${applicant.first_name_cyrillic ?? ""}`.trim()
    : `Заявитель ${applicant.position}`;

  const actionLabel =
    applicant.completion_percent === 0 ? "Заполнить" : applicant.status === "completed" ? "Редактировать" : "Продолжить";

  return (
    <article className="surface-card">
      <div className="card-row">
        <div>
          <p className="card-label">Заявитель {applicant.position}</p>
          <h3>{title}</h3>
          <p className="muted-text">{statusLabels[applicant.status] ?? "Не начато"}</p>
        </div>
        <ProgressBadge percent={applicant.completion_percent} />
      </div>
      <Link className="primary-button" href={`/applicants/${applicant.id}`}>
        {actionLabel}
      </Link>
    </article>
  );
}
