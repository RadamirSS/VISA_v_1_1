"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { ApplicantCard } from "../../components/ApplicantCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { ApplicantProfile, VisaCase } from "../../lib/types";

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
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [error, setError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  async function load() {
    try {
      const meResponse = await api.getMe();
      if (meResponse.has_case) {
        try {
          setVisaCase(await api.getCurrentCase());
        } catch {
          setVisaCase(null);
        }
      }
      const listResponse = await api.listApplicants();
      setApplicants(listResponse);
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
    } catch (selectionError) {
      setError(selectionError instanceof Error ? selectionError.message : "Не удалось создать анкеты.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <AppShell title="Заявители" subtitle="Заполните профили для себя, семьи или группы в одном месте.">
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {applicants === null ? <LoadingState label="Загружаем список заявителей..." /> : null}
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
        <EmptyState title="Профили еще не созданы" description="Выберите количество заявителей, и мы подготовим черновики анкет." />
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
