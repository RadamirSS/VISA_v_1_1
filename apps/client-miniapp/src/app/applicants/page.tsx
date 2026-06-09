"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { ApplicantCard } from "../../components/ApplicantCard";
import { ProgressBar } from "../../components/ProgressBar";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { ApplicantProfile, CabinetSummary, VisaCase } from "../../lib/types";

const applicantOptions = [
  { label: "1 человек", value: 1 },
  { label: "2 человека", value: 2 },
  { label: "3 человека", value: 3 },
  { label: "4 человека", value: 4 },
  { label: "5+", value: 5 },
  { label: "Семья / группа", value: 6 }
];

export default function ApplicantsPage() {
  const [applicants, setApplicants] = useState<ApplicantProfile[] | null>(null);
  const [summary, setSummary] = useState<CabinetSummary | null>(null);
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [error, setError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  async function load() {
    try {
      const [summaryResponse, listResponse] = await Promise.all([api.getCabinetSummary(), api.listApplicants()]);
      setSummary(summaryResponse);
      setApplicants(listResponse);
      if (summaryResponse.case) {
        try {
          setVisaCase(await api.getCurrentCase());
        } catch {
          setVisaCase(null);
        }
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить заявителей.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function selectCount(value: number) {
    setIsSaving(true);
    try {
      const caseResponse = await api.setApplicantsCount(value);
      setVisaCase(caseResponse);
      setApplicants(await api.listApplicants());
      setSummary(await api.getCabinetSummary());
    } catch (selectionError) {
      setError(selectionError instanceof Error ? selectionError.message : "Не удалось создать анкеты.");
    } finally {
      setIsSaving(false);
    }
  }

  const completed = summary?.applicants.completed ?? applicants?.filter((item) => item.status === "completed").length ?? 0;
  const total = summary?.applicants.total ?? applicants?.length ?? 0;

  return (
    <AppShell title="Заявители" subtitle="Заполните профили для себя, семьи или группы в одном месте.">
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {applicants === null ? <LoadingState label="Загружаем список заявителей..." /> : null}
      {applicants !== null ? (
        <section className="surface-card dashboard-card">
          <p className="card-label">Прогресс</p>
          <h3>Заявители</h3>
          <p className="muted-text">Заполнено: {completed} из {total || "—"}</p>
          <ProgressBar completed={completed} total={total} />
        </section>
      ) : null}
      {visaCase && visaCase.applicants_count === 0 ? (
        <section className="surface-card">
          <h3>Сколько человек подается на визу?</h3>
          <div className="choice-grid">
            {applicantOptions.map((option) => (
              <button key={option.label} className="secondary-button" disabled={isSaving} onClick={() => selectCount(option.value)} type="button">
                {option.label}
              </button>
            ))}
          </div>
        </section>
      ) : null}
      {applicants?.length === 0 ? (
        <EmptyState
          title="Анкеты еще не созданы"
          description="Укажите количество заявителей, чтобы начать заполнение."
        />
      ) : null}
      {applicants?.length ? (
        <div className="grid-stack">
          {applicants.map((applicant) => (
            <ApplicantCard key={applicant.id} applicant={applicant} />
          ))}
        </div>
      ) : null}
    </AppShell>
  );
}
