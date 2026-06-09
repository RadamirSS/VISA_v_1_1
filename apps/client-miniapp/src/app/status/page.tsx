"use client";

import { AppShell } from "../../components/AppShell";
import { AccessStatusCard } from "../../components/dashboard/AccessStatusCard";
import { CaseOverviewCard } from "../../components/dashboard/CaseOverviewCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusTimeline } from "../../components/StatusTimeline";
import { useCabinetData } from "../../lib/useCabinetData";

export default function StatusPage() {
  const { summary, timeline, error, loading } = useCabinetData();

  return (
    <AppShell title="Статус заявки" subtitle="Полный ход вашей заявки и текущий этап сопровождения.">
      {loading ? <LoadingState label="Загружаем статус..." /> : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {summary ? (
        <div className="grid-stack">
          <AccessStatusCard access={summary.access} />
          <CaseOverviewCard summary={summary} />
          {timeline ? <StatusTimeline steps={timeline.steps} title="Полный статус" /> : null}
        </div>
      ) : null}
    </AppShell>
  );
}
