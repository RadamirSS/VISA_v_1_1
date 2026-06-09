"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "../../../components/AppShell";
import { CaseTimeline } from "../../../components/CaseTimeline";
import { LoadingState } from "../../../components/LoadingState";
import { api } from "../../../lib/api";
import type { ApplicantProfile, VisaCase } from "../../../lib/types";

function applicantName(applicant: ApplicantProfile) {
  return (
    `${applicant.last_name_cyrillic ?? ""} ${applicant.first_name_cyrillic ?? ""}`.trim() ||
    `Заявитель ${applicant.position}`
  );
}

export default function ReviewCasePage() {
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [applicants, setApplicants] = useState<ApplicantProfile[]>([]);
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [caseResponse, applicantsResponse] = await Promise.all([api.getCurrentCase(), api.listApplicants()]);
        setVisaCase(caseResponse);
        setApplicants(applicantsResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить review.");
      }
    }
    void load();
  }, []);

  async function submit() {
    setIsSubmitting(true);
    try {
      const response = await api.submitCase();
      setVisaCase(response.case);
      setError("");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось отправить заявку.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AppShell title="Проверка заявки" subtitle="Проверьте summary перед отправкой менеджеру.">
      {!visaCase && !error ? <LoadingState label="Готовим итоговое summary..." /> : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {visaCase ? (
        <div className="grid-stack">
          <section className="surface-card">
            <h3>Итоговая проверка</h3>
            <p className="muted-text">Заявители: {applicants.length}</p>
            <p className="muted-text">Страна: {visaCase.desired_country_name_ru ?? "не выбрана"}</p>
            <p className="muted-text">Город подачи: {visaCase.preferred_submission_city ?? "не выбран"}</p>
            <p className="muted-text">Визовый центр: {visaCase.submission_provider ?? "не выбран"}</p>
            <p className="muted-text">Цель: {visaCase.travel_purpose ?? "не выбрана"}</p>
            <p className="muted-text">
              Даты поездки: {visaCase.approximate_travel_start_date ?? "не указано"} — {visaCase.approximate_travel_end_date ?? "не указано"}
            </p>
            <p className="muted-text">После отправки менеджер проверит анкету и подберет возможные даты записи вручную.</p>
          </section>
          <section className="surface-card">
            <h3>Проверка анкет заявителей</h3>
            <div className="plain-list">
              {applicants.map((item) => (
                <p key={item.id}>
                  {applicantName(item)} — {item.completion_percent}% ({item.status})
                </p>
              ))}
            </div>
          </section>
          <CaseTimeline visaCase={visaCase} />
          <div className="action-bar">
            <button className="primary-button" disabled={isSubmitting} onClick={submit} type="button">
              {isSubmitting ? "Отправляем..." : "Отправить менеджеру"}
            </button>
            <Link className="secondary-button" href="/case/new">
              Вернуться к редактированию
            </Link>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
