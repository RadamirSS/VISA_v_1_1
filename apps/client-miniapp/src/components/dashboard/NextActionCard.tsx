import Link from "next/link";

import { resolveNextAction } from "../../lib/cabinet";
import type { CabinetSummary } from "../../lib/types";

export function NextActionCard({ summary }: { summary: CabinetSummary }) {
  const nextAction = resolveNextAction(summary);
  if (!nextAction) {
    return null;
  }

  return (
    <section className="surface-card dashboard-card next-action-card">
      <p className="card-label">Следующий шаг</p>
      <h3>{nextAction.label}</h3>
      <Link className="primary-button" href={nextAction.href}>
        Продолжить
      </Link>
    </section>
  );
}
