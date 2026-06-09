"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { CaseTimeline } from "../../components/CaseTimeline";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { MeResponse, VisaCase } from "../../lib/types";

export default function StatusPage() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);

  useEffect(() => {
    async function load() {
      const meResponse = await api.getMe();
      setMe(meResponse);
      if (meResponse.has_active_access && meResponse.has_case) {
        try {
          setVisaCase(await api.getCurrentCase());
        } catch {
          setVisaCase(null);
        }
      }
    }
    void load();
  }, []);

  return (
    <AppShell title="Статус" subtitle="Этот экран показывает прогресс по вашему текущему кейсу и анкетам.">
      {!me ? <LoadingState label="Загружаем статус..." /> : null}
      {me ? (
        <div className="grid-stack">
          <section className="surface-card">
            <p className="card-label">Доступ</p>
            <h3>{me.has_active_access ? "Активирован" : "Не активирован"}</h3>
            <p className="muted-text">Ключ: {me.active_access_key_code ?? "нет активного ключа"}</p>
          </section>
          <section className="surface-card">
            <p className="card-label">Кейс</p>
            <h3>{visaCase?.status ?? me.current_case_status ?? "Ожидается"}</h3>
            <p className="muted-text">Менеджер увидит только обезличенное уведомление о готовности анкет.</p>
          </section>
          <CaseTimeline visaCase={visaCase} />
        </div>
      ) : null}
    </AppShell>
  );
}
