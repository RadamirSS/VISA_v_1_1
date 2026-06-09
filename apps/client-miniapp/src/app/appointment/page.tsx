"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { CaseTimeline } from "../../components/CaseTimeline";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { SlotOffer, SlotOption, VisaCase } from "../../lib/types";

function formatOption(option: SlotOption) {
  const [year, month, day] = option.option_date.split("-");
  return `${day}.${month}.${year}, ${option.option_time}`;
}

export default function AppointmentPage() {
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [offers, setOffers] = useState<SlotOffer[]>([]);
  const [error, setError] = useState<string>("");
  const [selectingId, setSelectingId] = useState<string>("");

  async function load() {
    try {
      const [caseResponse, offersResponse] = await Promise.all([api.getCurrentCase(), api.getSlotOffers()]);
      setVisaCase(caseResponse);
      setOffers(offersResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить варианты дат.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function choose(optionId: string) {
    setSelectingId(optionId);
    try {
      setVisaCase(await api.selectSlotOption(optionId));
      await load();
    } catch (selectError) {
      setError(selectError instanceof Error ? selectError.message : "Не удалось выбрать дату.");
    } finally {
      setSelectingId("");
    }
  }

  return (
    <AppShell title="Даты записи" subtitle="Здесь появляются варианты, которые менеджер нашел вручную.">
      {!visaCase && !error ? <LoadingState label="Загружаем варианты дат..." /> : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {visaCase ? (
        <div className="grid-stack">
          {offers.length === 0 && !visaCase.selected_slot_option_id ? (
            <section className="surface-card">
              <h3>Менеджер подбирает доступные даты записи</h3>
              <p className="muted-text">Когда варианты появятся, вы получите уведомление в Telegram.</p>
            </section>
          ) : null}
          {offers.flatMap((offer) => offer.options).filter((option) => option.status === "available").map((option) => (
            <section key={option.id} className="surface-card">
              <h3>{formatOption(option)}</h3>
              <p className="muted-text">{option.city ?? "Город уточняется"}</p>
              <p className="muted-text">{option.provider ?? "Провайдер уточняется"}</p>
              <p className="muted-text">{option.comment ?? "Комментарий менеджера отсутствует"}</p>
              <button className="primary-button" disabled={selectingId === option.id} onClick={() => choose(option.id)} type="button">
                Выбрать эту дату
              </button>
            </section>
          ))}
          {visaCase.selected_slot_option_id ? (
            <section className="surface-card">
              <h3>Вы выбрали</h3>
              <p className="muted-text">
                {visaCase.selected_appointment_date} {visaCase.selected_appointment_time}
              </p>
              <p className="muted-text">Ожидаем финального подтверждения менеджера.</p>
            </section>
          ) : null}
          {visaCase.status === "appointment_confirmed" ? (
            <section className="surface-card">
              <h3>Запись подтверждена</h3>
              <p className="muted-text">
                {visaCase.selected_appointment_date} {visaCase.selected_appointment_time}
              </p>
              <p className="muted-text">
                {visaCase.selected_appointment_city} · {visaCase.selected_appointment_provider}
              </p>
            </section>
          ) : null}
          <CaseTimeline visaCase={visaCase} />
        </div>
      ) : null}
    </AppShell>
  );
}
