"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { AppointmentStatusCard } from "../../components/dashboard/AppointmentStatusCard";
import { DocumentsSummaryCard } from "../../components/dashboard/DocumentsSummaryCard";
import { NextActionCard } from "../../components/dashboard/NextActionCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusTimeline } from "../../components/StatusTimeline";
import { formatProviderDisplayName } from "../../lib/cabinet";
import { api } from "../../lib/api";
import type { CabinetSummary, CaseTimelineResponse, VisaCase } from "../../lib/types";

export default function CasePage() {
  const [summary, setSummary] = useState<CabinetSummary | null>(null);
  const [timeline, setTimeline] = useState<CaseTimelineResponse | null>(null);
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const summaryResponse = await api.getCabinetSummary();
        setSummary(summaryResponse);
        if (!summaryResponse.access.active) {
          setError("Для просмотра заявки нужен активный ключ доступа.");
          return;
        }
        if (!summaryResponse.case) {
          setError("no_case");
          return;
        }
        const [timelineResponse, caseResponse] = await Promise.all([api.getCaseTimeline(), api.getCurrentCase()]);
        setTimeline(timelineResponse);
        setVisaCase(caseResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить заявку.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <AppShell title="Заявка на сопровождение" subtitle="Здесь вы отслеживаете заявку и следующий шаг от менеджера.">
      {loading ? <LoadingState label="Загружаем заявку..." /> : null}
      {error === "no_case" ? (
        <EmptyState
          title="Заявка еще не создана"
          description="У вас пока нет визовой заявки. Заполните анкеты заявителей и создайте заявку на подачу."
          ctaHref="/case/new"
          ctaLabel="Создать заявку"
        />
      ) : null}
      {error && error !== "no_case" ? (
        <EmptyState
          title="Нужен активный ключ доступа"
          description="Для просмотра заявки активируйте ключ доступа в Telegram-боте и откройте личный кабинет снова."
          ctaHref="/"
          ctaLabel="На главную"
        />
      ) : null}
      {summary?.case && visaCase ? (
        <div className="grid-stack">
          <section className="surface-card dashboard-card">
            <p className="card-label">Заявка на сопровождение</p>
            <div className="card-row">
              <div>
                <h3>{summary.case.public_number || "Текущая заявка"}</h3>
                <ul className="case-facts">
                  <li>Страна подачи: {summary.case.desired_country_name_ru ?? "не выбрана"}</li>
                  <li>Город подачи: {summary.case.preferred_submission_city ?? "не выбран"}</li>
                  <li>
                    Визовый центр / провайдер:{" "}
                    {formatProviderDisplayName(summary.case.submission_provider) || "не выбран"}
                  </li>
                  <li>Цель поездки: {visaCase.travel_purpose ?? "не выбрана"}</li>
                  <li>Заявителей: {summary.case.applicants_count}</li>
                  <li>Статус сопровождения: {summary.case.status_label}</li>
                </ul>
              </div>
              <span className="status-chip success">{summary.case.status_label}</span>
            </div>
          </section>
          {summary.documents ? <DocumentsSummaryCard documents={summary.documents} expanded /> : null}
          <NextActionCard summary={summary} />
          <AppointmentStatusCard appointment={summary.appointment} expanded />
          {timeline ? <StatusTimeline steps={timeline.steps} /> : null}
        </div>
      ) : null}
    </AppShell>
  );
}
