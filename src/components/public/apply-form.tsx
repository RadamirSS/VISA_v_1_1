"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { initialLeadValues } from "@/lib/mock-data";
import { useDemoStore } from "@/lib/demo-store";
import { LeadFormValues } from "@/lib/types";
import { Card, ProgressBar } from "@/components/ui/primitives";

const steps = [
  { key: "contact", title: "Контакты", fields: ["fullName", "phone", "telegram", "email"] },
  { key: "travel", title: "Поездка", fields: ["citizenship", "location", "schengenCountry", "purpose", "travelDates", "applicantsCount"] },
  { key: "screening", title: "Проверка кейса", fields: ["previousSchengen", "passportValidity", "comment", "consent"] }
] as const;

export function ApplyForm() {
  const { createLead } = useDemoStore();
  const [form, setForm] = useState<LeadFormValues>(initialLeadValues);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState("");
  const [submittedLeadId, setSubmittedLeadId] = useState<string | null>(null);

  const currentStep = steps[stepIndex];
  const completion = useMemo(() => Math.round(((stepIndex + 1) / steps.length) * 100), [stepIndex]);

  const update = (key: keyof LeadFormValues, value: string | boolean) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const validateStep = () => {
    for (const field of currentStep.fields) {
      const value = form[field as keyof LeadFormValues];
      if (typeof value === "boolean" && !value) {
        setError("Нужно подтвердить согласие на обработку данных.");
        return false;
      }
      if (typeof value === "string" && value.trim().length === 0) {
        setError("Пожалуйста, заполните все обязательные поля на этом шаге.");
        return false;
      }
    }

    setError("");
    return true;
  };

  const onNext = () => {
    if (!validateStep()) {
      return;
    }

    setStepIndex((current) => Math.min(current + 1, steps.length - 1));
  };

  const onSubmit = () => {
    if (!validateStep()) {
      return;
    }

    const lead = createLead(form);
    setSubmittedLeadId(lead.id);
  };

  if (submittedLeadId) {
    return (
      <Card className="space-y-5 bg-[var(--surface)]">
        <p className="text-sm uppercase tracking-[0.24em] text-[var(--accent)]">Заявка отправлена</p>
        <h3 className="font-display text-3xl text-[var(--ink)]">Спасибо, мы получили ваш запрос</h3>
        <p className="text-[var(--muted)]">
          Статус заявки: <span className="font-medium text-[var(--ink)]">Submitted / Waiting for manager review</span>.
        </p>
        <p className="text-[var(--muted)]">Идентификатор заявки: {submittedLeadId}</p>
        <div className="flex flex-wrap gap-3">
          <Link href="/manager/leads" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
            Открыть демо менеджера
          </Link>
          <Link href="/" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-medium text-[var(--ink)]">
            Вернуться на сайт
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card className="space-y-6">
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm text-[var(--muted)]">
          <span>Шаг {stepIndex + 1} из {steps.length}</span>
          <span>{currentStep.title}</span>
        </div>
        <ProgressBar value={completion} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {stepIndex === 0 ? (
          <>
            <Field label="ФИО" value={form.fullName} onChange={(value) => update("fullName", value)} />
            <Field label="Телефон" value={form.phone} onChange={(value) => update("phone", value)} />
            <Field label="Telegram username" value={form.telegram} onChange={(value) => update("telegram", value)} />
            <Field label="Email" value={form.email} onChange={(value) => update("email", value)} />
          </>
        ) : null}

        {stepIndex === 1 ? (
          <>
            <Field label="Гражданство" value={form.citizenship} onChange={(value) => update("citizenship", value)} />
            <Field label="Текущая страна / город" value={form.location} onChange={(value) => update("location", value)} />
            <Field label="Желаемая страна Шенгена" value={form.schengenCountry} onChange={(value) => update("schengenCountry", value)} />
            <Field label="Цель поездки" value={form.purpose} onChange={(value) => update("purpose", value)} />
            <Field label="Планируемые даты" value={form.travelDates} onChange={(value) => update("travelDates", value)} />
            <Field label="Количество заявителей" value={form.applicantsCount} onChange={(value) => update("applicantsCount", value)} />
          </>
        ) : null}

        {stepIndex === 2 ? (
          <>
            <Field label="Шенгенские визы ранее" value={form.previousSchengen} onChange={(value) => update("previousSchengen", value)} />
            <Field label="Срок действия паспорта" value={form.passportValidity} onChange={(value) => update("passportValidity", value)} />
            <label className="md:col-span-2">
              <span className="mb-2 block text-sm font-medium text-[var(--ink)]">Комментарий</span>
              <textarea
                value={form.comment}
                onChange={(event) => update("comment", event.target.value)}
                className="min-h-32 w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--accent)]"
              />
            </label>
            <label className="md:col-span-2 flex items-start gap-3 rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-4">
              <input
                type="checkbox"
                checked={form.consent}
                onChange={(event) => update("consent", event.target.checked)}
                className="mt-1 h-4 w-4 rounded border-[var(--line)]"
              />
              <span className="text-sm text-[var(--muted)]">
                Согласен на обработку данных в рамках первичной консультации. Безопасное хранилище документов и финальные интеграции будут подключены позже.
              </span>
            </label>
          </>
        ) : null}
      </div>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="flex flex-wrap justify-between gap-3">
        <button
          type="button"
          onClick={() => setStepIndex((current) => Math.max(current - 1, 0))}
          className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-medium text-[var(--ink)] disabled:opacity-40"
          disabled={stepIndex === 0}
        >
          Назад
        </button>

        {stepIndex < steps.length - 1 ? (
          <button type="button" onClick={onNext} className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
            Далее
          </button>
        ) : (
          <button type="button" onClick={onSubmit} className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
            Отправить заявку
          </button>
        )}
      </div>
    </Card>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-[var(--ink)]">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--accent)]"
      />
    </label>
  );
}
