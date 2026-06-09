"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { CaseTimeline } from "../../components/CaseTimeline";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { SlotOffer, VisaCase } from "../../lib/types";

export default function CasePage() {
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [slotOffers, setSlotOffers] = useState<SlotOffer[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function load() {
      try {
        const currentCase = await api.getCurrentCase();
        setVisaCase(currentCase);
        setSlotOffers(await api.getSlotOffers());
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить заявку.");
      }
    }
    void load();
  }, []);

  return (
    <AppShell title="Визовая заявка" subtitle="Здесь вы создаете заявку на подачу и отслеживаете следующий шаг.">
      {!visaCase && !error ? <LoadingState label="Загружаем заявку..." /> : null}
      {error ? (
        <EmptyState
          title="Заявка еще не создана"
          description="У вас пока нет визовой заявки. Заполните анкеты заявителей и создайте заявку на подачу."
          ctaHref="/case/new"
          ctaLabel="Создать заявку"
        />
      ) : null}
      {visaCase ? (
        <div className="grid-stack">
          <section className="surface-card">
            <div className="card-row">
              <div>
                <p className="card-label">Страна и подача</p>
                <h3>{visaCase.desired_country_name_ru ?? "Страна не выбрана"}</h3>
                <p className="muted-text">Город: {visaCase.preferred_submission_city ?? "не выбран"}</p>
                <p className="muted-text">Визовый центр: {visaCase.submission_provider ?? "не выбран"}</p>
              </div>
              <span className="chip">{visaCase.status}</span>
            </div>
          </section>
          <section className="surface-card">
            <p className="card-label">Заявители</p>
            <h3>{visaCase.applicants_count}</h3>
            <p className="muted-text">Цель поездки: {visaCase.travel_purpose ?? "не выбрана"}</p>
          </section>
          <section className="surface-card">
            <p className="card-label">Следующий шаг</p>
            <h3>
              {visaCase.status === "submitted_for_manager_review" || visaCase.status === "needs_manager_consultation"
                ? "Ожидайте проверки менеджера"
                : visaCase.status === "slot_options_sent"
                  ? "Менеджер отправил варианты дат"
                  : visaCase.status === "slot_selected_by_client"
                    ? "Ожидаем финального подтверждения"
                : "Проверьте данные и завершите заявку"}
            </h3>
            <div className="action-bar">
              <Link className="primary-button" href="/case/new">
                Редактировать
              </Link>
              <Link className="secondary-button" href="/case/review">
                Открыть review
              </Link>
            </div>
          </section>
          <section className="surface-card">
            <p className="card-label">Запись</p>
            {slotOffers.length === 0 && !visaCase.selected_slot_option_id ? (
              <>
                <h3>Менеджер подбирает доступные даты записи</h3>
                <p className="muted-text">Когда варианты появятся, вы получите уведомление в Telegram.</p>
              </>
            ) : null}
            {slotOffers.length > 0 && !visaCase.selected_slot_option_id ? (
              <>
                <h3>Менеджер отправил варианты дат</h3>
                <p className="muted-text">Откройте подбор дат и выберите удобный вариант.</p>
                <Link className="primary-button" href="/appointment">
                  Открыть варианты дат
                </Link>
              </>
            ) : null}
            {visaCase.selected_slot_option_id && visaCase.status !== "appointment_confirmed" ? (
              <>
                <h3>Вы выбрали</h3>
                <p className="muted-text">
                  {visaCase.selected_appointment_date} {visaCase.selected_appointment_time}
                </p>
                <p className="muted-text">Ожидаем финального подтверждения менеджера.</p>
              </>
            ) : null}
            {visaCase.status === "appointment_confirmed" ? (
              <>
                <h3>Запись подтверждена</h3>
                <p className="muted-text">
                  {visaCase.selected_appointment_date} {visaCase.selected_appointment_time}
                </p>
                <p className="muted-text">
                  {visaCase.selected_appointment_city} · {visaCase.selected_appointment_provider}
                </p>
              </>
            ) : null}
          </section>
          <CaseTimeline visaCase={visaCase} />
        </div>
      ) : null}
    </AppShell>
  );
}
