"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { AppointmentStatusCard } from "../../components/dashboard/AppointmentStatusCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusTimeline } from "../../components/StatusTimeline";
import { formatAppointmentDate, formatProviderDisplayName } from "../../lib/cabinet";
import { api } from "../../lib/api";
import type { CabinetSummary, CaseTimelineResponse, SlotOffer, SlotOption } from "../../lib/types";

export default function AppointmentPage() {
  const [summary, setSummary] = useState<CabinetSummary | null>(null);
  const [timeline, setTimeline] = useState<CaseTimelineResponse | null>(null);
  const [offers, setOffers] = useState<SlotOffer[]>([]);
  const [error, setError] = useState<string>("");
  const [needsAccess, setNeedsAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectingId, setSelectingId] = useState<string>("");

  async function load() {
    setLoading(true);
    setNeedsAccess(false);
    setError("");
    try {
      const summaryResponse = await api.getCabinetSummary();
      setSummary(summaryResponse);
      if (!summaryResponse.access.active || !summaryResponse.case) {
        setNeedsAccess(true);
        return;
      }
      const [offersResponse, timelineResponse] = await Promise.all([
        api.getSlotOffers(),
        api.getCaseTimeline().catch(() => null)
      ]);
      setOffers(offersResponse);
      setTimeline(timelineResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить варианты дат.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function choose(optionId: string) {
    setSelectingId(optionId);
    try {
      await api.selectSlotOption(optionId);
      await load();
    } catch (selectError) {
      setError(selectError instanceof Error ? selectError.message : "Не удалось выбрать дату.");
    } finally {
      setSelectingId("");
    }
  }

  const availableOptions = offers.flatMap((offer) => offer.options).filter((option) => option.status === "available");
  const hasAvailableOptions = Boolean(summary?.appointment.has_options);
  const hasSelected = Boolean(summary?.appointment.selected?.date);
  const isConfirmed = Boolean(summary?.appointment.confirmed?.date);

  return (
    <AppShell title="Запись" subtitle="Здесь появляются варианты, которые менеджер нашел вручную.">
      {loading ? <LoadingState label="Загружаем варианты дат..." /> : null}
      {needsAccess ? (
        <EmptyState
          title="Нужна активная заявка"
          description="Для выбора даты активируйте ключ доступа и создайте заявку на сопровождение."
          ctaHref="/"
          ctaLabel="На главную"
        />
      ) : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {summary?.access.active && summary.case ? (
        <div className="grid-stack">
          {!isConfirmed && !hasSelected && !hasAvailableOptions ? (
            <section className="surface-card dashboard-card">
              <h3>Менеджер подбирает доступные даты</h3>
              <p className="muted-text">Мы уведомим вас, когда варианты появятся.</p>
            </section>
          ) : null}

          {!isConfirmed && !hasSelected && hasAvailableOptions ? (
            <section className="surface-card dashboard-card">
              <h3>Выберите удобный вариант</h3>
              <p className="muted-text">Выберите удобный вариант из предложенных менеджером дат.</p>
            </section>
          ) : null}

          {!isConfirmed && !hasSelected && hasAvailableOptions
            ? availableOptions.map((option: SlotOption) => (
                <section key={option.id} className="surface-card slot-option-card">
                  <h3>{formatAppointmentDate(option.option_date, option.option_time)}</h3>
                  {option.city ? <p className="muted-text">{option.city}</p> : null}
                  {option.provider ? (
                    <p className="muted-text">{formatProviderDisplayName(option.provider)}</p>
                  ) : null}
                  <p className="muted-text">{option.comment ?? "Комментарий менеджера"}</p>
                  <button className="primary-button" disabled={selectingId === option.id} onClick={() => choose(option.id)} type="button">
                    Выбрать эту дату
                  </button>
                </section>
              ))
            : null}

          <AppointmentStatusCard appointment={summary.appointment} expanded />
          {timeline ? <StatusTimeline steps={timeline.steps} /> : null}
        </div>
      ) : null}
    </AppShell>
  );
}
