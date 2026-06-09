"use client";

import { useEffect } from "react";

import { AppShell } from "../components/AppShell";
import { AccessStatusCard } from "../components/dashboard/AccessStatusCard";
import { ApplicantsProgressCard } from "../components/dashboard/ApplicantsProgressCard";
import { AppointmentStatusCard } from "../components/dashboard/AppointmentStatusCard";
import { DocumentsSummaryCard } from "../components/dashboard/DocumentsSummaryCard";
import { CaseOverviewCard } from "../components/dashboard/CaseOverviewCard";
import { ManagerHintCard } from "../components/dashboard/ManagerHintCard";
import { NextActionCard } from "../components/dashboard/NextActionCard";
import { TimelinePreviewCard } from "../components/dashboard/TimelinePreviewCard";
import { LoadingState } from "../components/LoadingState";
import { useCabinetData } from "../lib/useCabinetData";
import { setupTelegramWebApp } from "../lib/telegram";

export default function HomePage() {
  const { summary, timeline, error, loading } = useCabinetData();

  useEffect(() => {
    setupTelegramWebApp();
  }, []);

  const firstName = summary?.user.first_name;
  const greeting = firstName ? `Здравствуйте, ${firstName}` : "Здравствуйте";

  if (loading) {
    return (
      <AppShell title={greeting} subtitle="Личный кабинет визового сопровождения" hideEyebrow>
        <LoadingState label="Подготавливаем кабинет..." />
      </AppShell>
    );
  }

  return (
    <AppShell
      title={greeting}
      subtitle="Сервис помогает организовать сбор данных, документов и коммуникацию с менеджером."
      hideEyebrow
    >
      {error ? (
        <section className="surface-card status-banner">
          <p>Не удалось загрузить кабинет. Проверьте подключение и откройте Mini App снова из Telegram.</p>
        </section>
      ) : null}
      {summary ? (
        <div className="grid-stack">
          <AccessStatusCard access={summary.access} />
          {summary.access.active ? (
            <>
              <CaseOverviewCard summary={summary} />
              <NextActionCard summary={summary} />
              <ApplicantsProgressCard applicants={summary.applicants} />
              {summary.documents ? <DocumentsSummaryCard documents={summary.documents} /> : null}
              <AppointmentStatusCard appointment={summary.appointment} />
              <ManagerHintCard />
              {timeline ? <TimelinePreviewCard steps={timeline.steps} /> : null}
            </>
          ) : null}
        </div>
      ) : null}
    </AppShell>
  );
}
