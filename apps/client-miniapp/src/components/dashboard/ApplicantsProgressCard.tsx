import Link from "next/link";

import { ProgressBar } from "../ProgressBar";
import type { CabinetSummary } from "../../lib/types";

export function ApplicantsProgressCard({ applicants }: { applicants: CabinetSummary["applicants"] }) {
  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Заявители</p>
      <h3>Заявители</h3>
      <p className="muted-text">
        Заполнено: {applicants.completed} из {applicants.total || "—"}
      </p>
      <ProgressBar completed={applicants.completed} total={applicants.total} />
      <Link className="primary-button" href="/applicants">
        Открыть анкеты
      </Link>
    </section>
  );
}
