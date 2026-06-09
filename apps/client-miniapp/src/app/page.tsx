"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import type { MeResponse, VisaCase } from "../lib/types";
import { getTelegramUser, setupTelegramWebApp } from "../lib/telegram";

export default function HomePage() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [error, setError] = useState<string>("");
  const telegramUser = getTelegramUser();

  useEffect(() => {
    setupTelegramWebApp();
    async function load() {
      try {
        const meResponse = await api.getMe();
        setMe(meResponse);
        if (meResponse.has_active_access) {
          try {
            const caseResponse = await api.getCurrentCase();
            setVisaCase(caseResponse);
          } catch {
            setVisaCase(null);
          }
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить кабинет.");
      }
    }
    void load();
  }, []);

  if (!me && !error) {
    return (
      <AppShell title="Личный кабинет" subtitle="Загружаем информацию по вашей заявке">
        <LoadingState label="Подготавливаем кабинет..." />
      </AppShell>
    );
  }

  return (
    <AppShell
      title={`Здравствуйте${telegramUser?.first_name ? `, ${telegramUser.first_name}` : ""}`}
      subtitle="Здесь вы заполняете анкеты заявителей в структурированной форме вместо длинной переписки в чате."
    >
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {me && !me.has_active_access ? (
        <EmptyState
          title="Нужен ключ доступа"
          description="Для продолжения нужен ключ доступа от менеджера агентства. Вернитесь в бот и введите ключ доступа."
        />
      ) : null}
      {me?.has_active_access ? (
        <div className="grid-stack">
          <section className="surface-card">
            <p className="card-label">Моя заявка</p>
            {!me.has_case ? (
              <>
                <h3>У вас пока нет визовой заявки</h3>
                <p className="muted-text">Заполните анкеты заявителей и создайте заявку на подачу.</p>
                <Link className="primary-button" href="/case/new">
                  Создать заявку
                </Link>
              </>
            ) : (
              <>
                <h3>{visaCase?.desired_country_name_ru ?? "Заявка в работе"}</h3>
                <p className="muted-text">
                  {visaCase?.preferred_submission_city ? `Город подачи: ${visaCase.preferred_submission_city}` : "Город подачи пока не выбран"}
                </p>
                <p className="muted-text">Статус: {visaCase?.status ?? me.current_case_status ?? "draft"}</p>
                <Link className="primary-button" href="/case">
                  Открыть заявку
                </Link>
              </>
            )}
          </section>
          <section className="surface-card">
            <p className="card-label">Заявители</p>
            <h3>{visaCase?.applicants_count ?? 0}</h3>
            <p className="muted-text">Количество профилей в текущем кейсе</p>
            <Link className="primary-button" href="/applicants">
              Заполнить анкеты
            </Link>
          </section>
          <section className="surface-card">
            <p className="card-label">Статус</p>
            <h3>{me.current_case_status ?? "Ожидает заполнения"}</h3>
            <p className="muted-text">В личном кабинете вы можете заполнить анкеты, создать заявку и выбрать город подачи.</p>
          </section>
          <section className="surface-card">
            <p className="card-label">Документы</p>
            <p className="muted-text">Загрузка документов не входит в этот этап MVP.</p>
          </section>
          <section className="surface-card">
            <p className="card-label">Связь с менеджером</p>
            <p className="muted-text">Если нужен менеджер, используйте кнопку связи в Telegram-боте.</p>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
