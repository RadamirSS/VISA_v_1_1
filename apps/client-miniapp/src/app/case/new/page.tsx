"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { AppShell } from "../../../components/AppShell";
import { StatusTimeline } from "../../../components/StatusTimeline";
import { ConsulateCard, CountryCard } from "../../../components/CaseSelectionCard";
import { LoadingState } from "../../../components/LoadingState";
import { api } from "../../../lib/api";
import type { CasePayload, CaseTimelineResponse, ConsulateOption, CountryOption, VisaCase } from "../../../lib/types";

const travelPurposeOptions = ["Туризм", "Бизнес", "Посещение родственников/друзей", "Учеба / мероприятие", "Медицинская цель", "Другое / уточнить с менеджером"];

export default function NewCasePage() {
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [consulates, setConsulates] = useState<ConsulateOption[]>([]);
  const [formData, setFormData] = useState<CasePayload>({});
  const [incompleteApplicants, setIncompleteApplicants] = useState<string[]>([]);
  const [timeline, setTimeline] = useState<CaseTimelineResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  const consultationOptions = useMemo(
    () => [
      { code: "CONSULTATION", name_ru: "Не знаю, нужна консультация", suits_for_ru: "Создадим кейс без выбора города и менеджер поможет определить маршрут подачи." },
      { code: "OTHER", name_ru: "Другая страна", suits_for_ru: "Если нужной страны нет в списке, менеджер уточнит возможный сценарий." }
    ],
    []
  );

  useEffect(() => {
    async function load() {
      try {
        const [countriesResponse, caseResponse] = await Promise.all([
          api.listCountries(),
          api.createCase()
        ]);
        setCountries(countriesResponse);
        setVisaCase(caseResponse.case);
        setFormData({
          desired_country_code: caseResponse.case.desired_country_code,
          desired_country_name_ru: caseResponse.case.desired_country_name_ru,
          preferred_submission_city: caseResponse.case.preferred_submission_city,
          submission_provider: caseResponse.case.submission_provider,
          travel_purpose: caseResponse.case.travel_purpose,
          approximate_travel_start_date: caseResponse.case.approximate_travel_start_date,
          approximate_travel_end_date: caseResponse.case.approximate_travel_end_date,
          client_comment: caseResponse.case.client_comment
        });
        setIncompleteApplicants(caseResponse.incomplete_applicants);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось подготовить заявку.");
      }
    }
    void load();
  }, []);

  useEffect(() => {
    async function loadTimeline() {
      if (!visaCase) {
        setTimeline(null);
        return;
      }
      try {
        setTimeline(await api.getCaseTimeline());
      } catch {
        setTimeline(null);
      }
    }
    void loadTimeline();
  }, [visaCase]);

  useEffect(() => {
    async function loadConsulates() {
      if (!formData.desired_country_code || formData.desired_country_code === "CONSULTATION" || formData.desired_country_code === "OTHER") {
        setConsulates([]);
        return;
      }
      setConsulates(await api.listConsulates(formData.desired_country_code));
    }
    void loadConsulates();
  }, [formData.desired_country_code]);

  async function persist(next: CasePayload) {
    setIsSaving(true);
    try {
      const updated = await api.updateCase(next);
      setVisaCase(updated);
      setFormData({
        desired_country_code: updated.desired_country_code,
        desired_country_name_ru: updated.desired_country_name_ru,
        preferred_submission_city: updated.preferred_submission_city,
        submission_provider: updated.submission_provider,
        travel_purpose: updated.travel_purpose,
        approximate_travel_start_date: updated.approximate_travel_start_date,
        approximate_travel_end_date: updated.approximate_travel_end_date,
        client_comment: updated.client_comment
      });
      setError("");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Не удалось сохранить заявку.");
    } finally {
      setIsSaving(false);
    }
  }

  const canProceedToReview = Boolean(formData.desired_country_code && formData.travel_purpose);

  return (
    <AppShell title="Создание заявки" subtitle="Выберите страну, город подачи и визовый центр из общей конфигурации.">
      {!visaCase && !error ? <LoadingState label="Подготавливаем case flow..." /> : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {incompleteApplicants.length ? (
        <section className="surface-card">
          <h3>Сначала заполните анкеты всех заявителей</h3>
          <div className="plain-list">
            {incompleteApplicants.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
          <Link className="primary-button" href="/applicants">
            Перейти к анкетам
          </Link>
        </section>
      ) : null}
      {timeline ? <StatusTimeline steps={timeline.steps} /> : null}
      {visaCase && !incompleteApplicants.length ? (
        <div className="grid-stack">
          <section className="surface-card">
            <div className="card-row">
              <h3>Шаг 1. Страна Шенгена</h3>
              <span className="chip">1/5</span>
            </div>
            <div className="grid-stack">
              {countries.map((country) => (
                <CountryCard
                  key={country.code}
                  country={country}
                  isActive={formData.desired_country_code === country.code}
                  onSelect={() =>
                    void persist({
                      ...formData,
                      desired_country_code: country.code,
                      desired_country_name_ru: country.name_ru,
                      preferred_submission_city: undefined,
                      submission_provider: undefined
                    })
                  }
                />
              ))}
              {consultationOptions.map((country) => (
                <CountryCard
                  key={country.code}
                  country={country}
                  isActive={formData.desired_country_code === country.code}
                  onSelect={() =>
                    void persist({
                      ...formData,
                      desired_country_code: country.code,
                      desired_country_name_ru: country.name_ru,
                      preferred_submission_city: undefined,
                      submission_provider: undefined
                    })
                  }
                />
              ))}
            </div>
          </section>

          {formData.desired_country_code && formData.desired_country_code !== "CONSULTATION" && formData.desired_country_code !== "OTHER" ? (
            <section className="surface-card">
              <div className="card-row">
                <h3>Шаг 2. Город подачи и визовый центр</h3>
                <span className="chip">2/5</span>
              </div>
              <div className="grid-stack">
                {consulates.map((consulate) => (
                  <ConsulateCard
                    key={`${consulate.city}-${consulate.provider}`}
                    consulate={consulate}
                    isActive={
                      formData.preferred_submission_city === consulate.city && formData.submission_provider === consulate.provider
                    }
                    onSelect={() =>
                      void persist({
                        ...formData,
                        preferred_submission_city: consulate.city,
                        submission_provider: consulate.provider
                      })
                    }
                  />
                ))}
              </div>
            </section>
          ) : null}

          <section className="surface-card">
            <div className="card-row">
              <h3>Шаг 3. Цель поездки</h3>
              <span className="chip">3/5</span>
            </div>
            <div className="choice-grid">
              {travelPurposeOptions.map((purpose) => (
                <button
                  key={purpose}
                  className={formData.travel_purpose === purpose ? "secondary-button active" : "secondary-button"}
                  disabled={isSaving}
                  onClick={() => void persist({ ...formData, travel_purpose: purpose })}
                  type="button"
                >
                  {purpose}
                </button>
              ))}
            </div>
          </section>

          <section className="surface-card">
            <div className="card-row">
              <h3>Шаг 4. Примерные даты поездки</h3>
              <span className="chip">4/5</span>
            </div>
            <div className="form-grid">
              <label className="field">
                <span>Дата начала</span>
                <input
                  type="date"
                  value={formData.approximate_travel_start_date ?? ""}
                  onChange={(event) => setFormData((current) => ({ ...current, approximate_travel_start_date: event.target.value }))}
                />
              </label>
              <label className="field">
                <span>Дата окончания</span>
                <input
                  type="date"
                  value={formData.approximate_travel_end_date ?? ""}
                  onChange={(event) => setFormData((current) => ({ ...current, approximate_travel_end_date: event.target.value }))}
                />
              </label>
              <label className="field">
                <span>Комментарий для менеджера</span>
                <input
                  value={formData.client_comment ?? ""}
                  onChange={(event) => setFormData((current) => ({ ...current, client_comment: event.target.value }))}
                />
              </label>
              <button className="secondary-button" disabled={isSaving} onClick={() => void persist(formData)} type="button">
                Сохранить шаг
              </button>
            </div>
          </section>

          <section className="surface-card">
            <div className="card-row">
              <h3>Шаг 5. Проверка и отправка</h3>
              <span className="chip">5/5</span>
            </div>
            <p className="muted-text">После отправки менеджер проверит анкету и подберет возможные даты записи вручную.</p>
            <div className="action-bar">
              <Link className={canProceedToReview ? "primary-button" : "ghost-button"} href={canProceedToReview ? "/case/review" : "/case/new"}>
                Перейти к review
              </Link>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
