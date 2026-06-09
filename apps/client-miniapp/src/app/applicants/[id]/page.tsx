"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AppShell } from "../../../components/AppShell";
import { ApplicantForm } from "../../../components/ApplicantForm";
import { LoadingState } from "../../../components/LoadingState";
import { api } from "../../../lib/api";
import type { ApplicantProfile, VisaCase } from "../../../lib/types";

export default function ApplicantPage() {
  const params = useParams<{ id: string }>();
  const [applicant, setApplicant] = useState<ApplicantProfile | null>(null);
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function load() {
      try {
        const [applicantResponse, caseResponse] = await Promise.all([
          api.getApplicant(params.id),
          api.getCurrentCase()
        ]);
        setApplicant(applicantResponse);
        setVisaCase(caseResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось открыть анкету.");
      }
    }
    void load();
  }, [params.id]);

  return (
    <AppShell title="Анкета заявителя" subtitle="Заполните данные в защищенной веб-форме внутри Mini App.">
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {!applicant || !visaCase ? <LoadingState label="Загружаем анкету..." /> : null}
      {applicant && visaCase ? <ApplicantForm initialApplicant={applicant} applicantsCount={visaCase.applicants_count} /> : null}
    </AppShell>
  );
}
