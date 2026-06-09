"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "../lib/api";
import type { ApplicantPayload, ApplicantProfile } from "../lib/types";
import { validateApplicant } from "../lib/validation";
import { ProgressBadge } from "./ProgressBadge";

const sectionFields = {
  personal: ["last_name_latin", "first_name_latin", "last_name_cyrillic", "first_name_cyrillic", "patronymic", "birth_date", "birth_place", "citizenship", "gender", "marital_status"],
  contact: ["phone", "email", "residence_country", "residence_city", "residence_address", "postal_code"],
  passport: ["passport_number", "passport_issue_date", "passport_expiry_date", "passport_issuing_authority", "passport_issuing_country"],
  trip: ["desired_country_code", "desired_country_name_ru", "travel_purpose", "approximate_travel_dates", "entries_count", "preferred_submission_city"]
} as const;

function sectionProgress(data: ApplicantPayload, keys: readonly string[]) {
  const filled = keys.filter((key) => {
    const value = data[key as keyof ApplicantPayload];
    return value && String(value).trim() !== "";
  }).length;
  return Math.round((filled / keys.length) * 100);
}

function Field({
  label,
  name,
  value,
  onChange,
  error,
  required = false
}: {
  label: string;
  name: keyof ApplicantPayload;
  value?: string | null;
  onChange: (name: keyof ApplicantPayload, value: string) => void;
  error?: string;
  required?: boolean;
}) {
  return (
    <label className="field">
      <span>
        {label}
        {required ? " *" : ""}
      </span>
      <input value={value ?? ""} onChange={(event) => onChange(name, event.target.value)} />
      {error ? <small className="field-error">{error}</small> : null}
    </label>
  );
}

export function ApplicantForm({ initialApplicant, applicantsCount }: { initialApplicant: ApplicantProfile; applicantsCount: number }) {
  const router = useRouter();
  const [formData, setFormData] = useState<ApplicantPayload>(initialApplicant);
  const [completionPercent, setCompletionPercent] = useState(initialApplicant.completion_percent);
  const [errors, setErrors] = useState<Partial<Record<keyof ApplicantPayload, string>>>({});
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setFormData(initialApplicant);
    setCompletionPercent(initialApplicant.completion_percent);
  }, [initialApplicant]);

  const onChange = (name: keyof ApplicantPayload, value: string) => {
    setFormData((current) => ({ ...current, [name]: value }));
  };

  async function save(returnToList: boolean) {
    const nextErrors = validateApplicant(formData);
    setErrors(nextErrors);
    setIsSaving(true);
    try {
      const saved = await api.updateApplicant(initialApplicant.id, formData);
      setFormData(saved);
      setCompletionPercent(saved.completion_percent);
      setStatusMessage("Черновик сохранен.");
      if (returnToList) {
        router.push("/applicants");
        router.refresh();
      } else {
        router.refresh();
      }
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Не удалось сохранить анкету.");
    } finally {
      setIsSaving(false);
    }
  }

  async function copyFromPrimary() {
    try {
      const saved = await api.copyFromPrimary(initialApplicant.id);
      setFormData(saved);
      setCompletionPercent(saved.completion_percent);
      setStatusMessage("Контакты и адрес скопированы от основного заявителя.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Не удалось скопировать данные.");
    }
  }

  return (
    <div className="form-stack">
      <section className="surface-card">
        <div className="card-row">
          <div>
            <p className="card-label">Общий прогресс</p>
            <h3>Заявитель {initialApplicant.position}</h3>
          </div>
          <ProgressBadge percent={completionPercent} />
        </div>
        {statusMessage ? <p className="status-banner">{statusMessage}</p> : null}
      </section>

      <section className="surface-card">
        <div className="card-row">
          <h3>Раздел A. Личные данные</h3>
          <span className="chip">{sectionProgress(formData, sectionFields.personal)}%</span>
        </div>
        <div className="form-grid">
          <Field label="Фамилия, латиницей" name="last_name_latin" value={formData.last_name_latin} onChange={onChange} error={errors.last_name_latin} required />
          <Field label="Имя, латиницей" name="first_name_latin" value={formData.first_name_latin} onChange={onChange} error={errors.first_name_latin} required />
          <Field label="Фамилия, кириллицей" name="last_name_cyrillic" value={formData.last_name_cyrillic} onChange={onChange} error={errors.last_name_cyrillic} required />
          <Field label="Имя, кириллицей" name="first_name_cyrillic" value={formData.first_name_cyrillic} onChange={onChange} error={errors.first_name_cyrillic} required />
          <Field label="Отчество" name="patronymic" value={formData.patronymic} onChange={onChange} />
          <Field label="Дата рождения" name="birth_date" value={formData.birth_date} onChange={onChange} error={errors.birth_date} required />
          <Field label="Место рождения" name="birth_place" value={formData.birth_place} onChange={onChange} error={errors.birth_place} required />
          <Field label="Гражданство" name="citizenship" value={formData.citizenship} onChange={onChange} error={errors.citizenship} required />
          <Field label="Пол" name="gender" value={formData.gender} onChange={onChange} />
          <Field label="Семейное положение" name="marital_status" value={formData.marital_status} onChange={onChange} />
        </div>
      </section>

      <section className="surface-card">
        <div className="card-row">
          <h3>Раздел B. Контакты и проживание</h3>
          <span className="chip">{sectionProgress(formData, sectionFields.contact)}%</span>
        </div>
        <div className="form-grid">
          <Field label="Телефон" name="phone" value={formData.phone} onChange={onChange} error={errors.phone} required />
          <Field label="Email" name="email" value={formData.email} onChange={onChange} />
          <Field label="Страна проживания" name="residence_country" value={formData.residence_country} onChange={onChange} error={errors.residence_country} required />
          <Field label="Город проживания" name="residence_city" value={formData.residence_city} onChange={onChange} error={errors.residence_city} required />
          <Field label="Адрес проживания" name="residence_address" value={formData.residence_address} onChange={onChange} error={errors.residence_address} required />
          <Field label="Почтовый индекс" name="postal_code" value={formData.postal_code} onChange={onChange} />
        </div>
      </section>

      <section className="surface-card">
        <div className="card-row">
          <h3>Раздел C. Загранпаспорт</h3>
          <span className="chip">{sectionProgress(formData, sectionFields.passport)}%</span>
        </div>
        <p className="muted-text">Паспортные данные остаются только в Mini App и backend-хранилище. Они не отправляются в Telegram-сообщения.</p>
        <div className="form-grid">
          <Field label="Номер паспорта" name="passport_number" value={formData.passport_number} onChange={onChange} error={errors.passport_number} required />
          <Field label="Дата выдачи" name="passport_issue_date" value={formData.passport_issue_date} onChange={onChange} error={errors.passport_issue_date} required />
          <Field label="Срок действия" name="passport_expiry_date" value={formData.passport_expiry_date} onChange={onChange} error={errors.passport_expiry_date} required />
          <Field label="Кем выдан" name="passport_issuing_authority" value={formData.passport_issuing_authority} onChange={onChange} />
          <Field label="Страна выдачи" name="passport_issuing_country" value={formData.passport_issuing_country} onChange={onChange} error={errors.passport_issuing_country} required />
        </div>
      </section>

      <section className="surface-card">
        <div className="card-row">
          <h3>Раздел D. Параметры поездки</h3>
          <span className="chip">{sectionProgress(formData, sectionFields.trip)}%</span>
        </div>
        <div className="form-grid">
          <Field label="Код страны Шенгена" name="desired_country_code" value={formData.desired_country_code} onChange={onChange} error={errors.desired_country_code} required />
          <Field label="Страна поездки" name="desired_country_name_ru" value={formData.desired_country_name_ru} onChange={onChange} />
          <Field label="Цель поездки" name="travel_purpose" value={formData.travel_purpose} onChange={onChange} error={errors.travel_purpose} required />
          <Field label="Примерные даты поездки" name="approximate_travel_dates" value={formData.approximate_travel_dates} onChange={onChange} />
          <Field label="Количество въездов" name="entries_count" value={formData.entries_count} onChange={onChange} />
          <Field label="Предпочтительный город подачи" name="preferred_submission_city" value={formData.preferred_submission_city} onChange={onChange} />
        </div>
      </section>

      {applicantsCount > 1 && initialApplicant.position > 1 ? (
        <section className="surface-card">
          <h3>Раздел E. Семья / группа</h3>
          <button className="secondary-button" type="button" onClick={copyFromPrimary}>
            Скопировать адрес и контакты от основного заявителя
          </button>
        </section>
      ) : null}

      <div className="action-bar">
        <button className="secondary-button" disabled={isSaving} type="button" onClick={() => save(false)}>
          {isSaving ? "Сохранение..." : "Сохранить черновик"}
        </button>
        <button className="primary-button" disabled={isSaving} type="button" onClick={() => save(true)}>
          Сохранить и вернуться
        </button>
        <button className="ghost-button" type="button" onClick={() => router.push("/applicants")}>
          Отмена
        </button>
      </div>
    </div>
  );
}
