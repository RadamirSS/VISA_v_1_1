"use client";

import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/primitives";

type AdditionalApplicant = {
  fullName: string;
  birthDateOrYear: string;
  relationship: string;
};

type FormState = {
  lastName: string;
  firstName: string;
  patronymic: string;
  birthDateOrYear: string;
  citizenship: string;
  currentLocation: string;
  desiredCountry: string;
  travelPurpose: string;
  approximateTravelMonth: string;
  applicantsCount: number;
  additionalApplicants: AdditionalApplicant[];
  telegram: string;
  phone: string;
  email: string;
  comment: string;
  consent: boolean;
};

const countryOptions = ["Италия", "Франция", "Испания", "Греция", "Германия", "Португалия", "Не знаю, нужна консультация", "Другая страна"];
const purposeOptions = ["Туризм", "Бизнес", "Посещение родственников/друзей", "Учеба/мероприятие", "Не знаю / нужна консультация"];

const initialState: FormState = {
  lastName: "",
  firstName: "",
  patronymic: "",
  birthDateOrYear: "",
  citizenship: "Россия",
  currentLocation: "",
  desiredCountry: "Италия",
  travelPurpose: "Туризм",
  approximateTravelMonth: "",
  applicantsCount: 1,
  additionalApplicants: [],
  telegram: "",
  phone: "",
  email: "",
  comment: "",
  consent: false
};

export function ApplyForm({ initialDesiredCountry }: { initialDesiredCountry?: string }) {
  const [form, setForm] = useState<FormState>(initialState);
  const [status, setStatus] = useState<"idle" | "loading" | "success">("idle");
  const [error, setError] = useState("");

  const additionalCount = useMemo(() => Math.max(form.applicantsCount - 1, 0), [form.applicantsCount]);

  useEffect(() => {
    if (initialDesiredCountry && countryOptions.includes(initialDesiredCountry)) {
      setForm((current) => ({ ...current, desiredCountry: initialDesiredCountry }));
    }
  }, [initialDesiredCountry]);

  const syncApplicants = (count: number) => {
    setForm((current) => {
      const nextApplicants = Array.from({ length: Math.max(count - 1, 0) }, (_, index) => current.additionalApplicants[index] ?? { fullName: "", birthDateOrYear: "", relationship: "" });
      return {
        ...current,
        applicantsCount: count,
        additionalApplicants: nextApplicants
      };
    });
  };

  const updateApplicant = (index: number, key: keyof AdditionalApplicant, value: string) => {
    setForm((current) => ({
      ...current,
      additionalApplicants: current.additionalApplicants.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item))
    }));
  };

  const validate = () => {
    if (!form.lastName || !form.firstName || !form.birthDateOrYear || !form.citizenship || !form.consent) {
      setError("Заполните обязательные поля и подтвердите согласие.");
      return false;
    }

    if (!form.telegram.trim() && !form.phone.trim() && !form.email.trim()) {
      setError("Нужен хотя бы один способ связи: Telegram, телефон или email.");
      return false;
    }

    for (const applicant of form.additionalApplicants) {
      if (!applicant.fullName.trim() || !applicant.birthDateOrYear.trim()) {
        setError("Для дополнительных заявителей нужно указать имя и дату или год рождения.");
        return false;
      }
    }

    setError("");
    return true;
  };

  const onSubmit = async () => {
    if (!validate()) {
      return;
    }

    setStatus("loading");

    const response = await fetch("/api/leads", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        mainApplicant: {
          lastName: form.lastName,
          firstName: form.firstName,
          patronymic: form.patronymic || undefined,
          birthDateOrYear: form.birthDateOrYear,
          citizenship: form.citizenship,
          currentLocation: form.currentLocation || undefined
        },
        desiredCountry: form.desiredCountry,
        travelPurpose: form.travelPurpose,
        approximateTravelMonth: form.approximateTravelMonth || undefined,
        applicantsCount: form.applicantsCount,
        additionalApplicants: form.additionalApplicants.filter((item) => item.fullName.trim()),
        contact: {
          telegram: form.telegram || undefined,
          phone: form.phone || undefined,
          email: form.email || undefined
        },
        comment: form.comment || undefined,
        consent: form.consent,
        source: "website"
      })
    });

    const result = (await response.json()) as { ok: boolean; error?: string };
    if (!response.ok || !result.ok) {
      setStatus("idle");
      setError(result.error || "Не удалось отправить заявку.");
      return;
    }

    setStatus("success");
  };

  if (status === "success") {
    return (
      <Card className="space-y-5 bg-[var(--surface)]">
        <p className="text-sm uppercase tracking-[0.24em] text-[var(--accent)]">Заявка принята</p>
        <h3 className="font-display text-3xl text-[var(--ink)]">Спасибо, мы получили ваш запрос</h3>
        <p className="text-[var(--muted)]">
          Сначала мы сохраняем заявку на сервере, затем менеджер связывается с вами по указанным контактам для первичной консультации.
          Финальное решение по визе принимает консульство или уполномоченный визовый орган.
        </p>
      </Card>
    );
  }

  return (
    <Card className="space-y-6">
      <div className="rounded-[24px] bg-[var(--surface)] p-4 text-sm text-[var(--muted)]">
        Укажите только базовую информацию для связи и первичной консультации. Паспортные данные, загрузка документов и платежные сведения на сайте не нужны.
        Мы не гарантируем визу и не гарантируем запись — доступность дат зависит от внешних визовых систем.
      </div>

      <div className="space-y-4">
        <div>
          <p className="font-display text-2xl text-[var(--ink)]">Основной заявитель</p>
          <p className="mt-2 text-sm text-[var(--muted)]">Эти поля помогают менеджеру понять кейс и связаться с вами без лишнего запроса данных.</p>
        </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Фамилия" value={form.lastName} onChange={(value) => setForm((current) => ({ ...current, lastName: value }))} />
        <Field label="Имя" value={form.firstName} onChange={(value) => setForm((current) => ({ ...current, firstName: value }))} />
        <Field label="Отчество" value={form.patronymic} onChange={(value) => setForm((current) => ({ ...current, patronymic: value }))} />
        <Field label="Дата рождения или год рождения" value={form.birthDateOrYear} onChange={(value) => setForm((current) => ({ ...current, birthDateOrYear: value }))} />
        <Field label="Гражданство" value={form.citizenship} onChange={(value) => setForm((current) => ({ ...current, citizenship: value }))} />
        <Field label="Текущий город / страна" value={form.currentLocation} onChange={(value) => setForm((current) => ({ ...current, currentLocation: value }))} />
      </div>
      </div>

      <div className="space-y-4">
        <div>
          <p className="font-display text-2xl text-[var(--ink)]">Направление визы</p>
          <p className="mt-2 text-sm text-[var(--muted)]">Если страна или цель пока не определены, можно выбрать вариант с консультацией.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
        <SelectField label="Желаемая страна Шенгена" value={form.desiredCountry} options={countryOptions} onChange={(value) => setForm((current) => ({ ...current, desiredCountry: value }))} />
        <SelectField label="Цель поездки" value={form.travelPurpose} options={purposeOptions} onChange={(value) => setForm((current) => ({ ...current, travelPurpose: value }))} />
        <Field label="Примерный месяц поездки" value={form.approximateTravelMonth} onChange={(value) => setForm((current) => ({ ...current, approximateTravelMonth: value }))} />
        <SelectField
          label="Количество заявителей"
          value={String(form.applicantsCount)}
          options={["1", "2", "3", "4", "5"]}
          onChange={(value) => syncApplicants(Number(value))}
        />
      </div>
      </div>

      {additionalCount > 0 ? (
        <div className="space-y-4">
          <p className="font-display text-2xl text-[var(--ink)]">Дополнительные заявители</p>
          {form.additionalApplicants.map((item, index) => (
            <div key={index} className="grid gap-4 rounded-[24px] bg-[var(--surface)] p-4 md:grid-cols-3">
              <Field label="ФИО" value={item.fullName} onChange={(value) => updateApplicant(index, "fullName", value)} />
              <Field label="Дата или год рождения" value={item.birthDateOrYear} onChange={(value) => updateApplicant(index, "birthDateOrYear", value)} />
              <Field label="Кем приходится" value={item.relationship} onChange={(value) => updateApplicant(index, "relationship", value)} />
            </div>
          ))}
        </div>
      ) : null}

      <div className="space-y-4">
        <div>
          <p className="font-display text-2xl text-[var(--ink)]">Контакты</p>
          <p className="mt-2 text-sm text-[var(--muted)]">Нужен хотя бы один способ связи: Telegram, телефон или email.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Telegram username" value={form.telegram} onChange={(value) => setForm((current) => ({ ...current, telegram: value }))} />
          <Field label="Телефон" value={form.phone} onChange={(value) => setForm((current) => ({ ...current, phone: value }))} />
          <Field label="Email" value={form.email} onChange={(value) => setForm((current) => ({ ...current, email: value }))} />
        </div>
      </div>

      <label>
        <span className="mb-2 block text-sm font-medium text-[var(--ink)]">Комментарий</span>
        <textarea
          value={form.comment}
          onChange={(event) => setForm((current) => ({ ...current, comment: event.target.value }))}
          className="min-h-32 w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--accent)]"
        />
      </label>

      <label className="flex items-start gap-3 rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-4">
        <input
          type="checkbox"
          checked={form.consent}
          onChange={(event) => setForm((current) => ({ ...current, consent: event.target.checked }))}
          className="mt-1 h-4 w-4 rounded border-[var(--line)]"
        />
        <span className="text-sm text-[var(--muted)]">Согласен на обработку данных для связи со мной и первичной консультации.</span>
      </label>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onSubmit}
          className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
          disabled={status === "loading"}
        >
          {status === "loading" ? "Отправляем..." : "Отправить заявку"}
        </button>
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

function SelectField({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-[var(--ink)]">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--accent)]">
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
