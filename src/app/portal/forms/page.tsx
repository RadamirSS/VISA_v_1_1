"use client";

import { useState } from "react";
import { PortalShell } from "@/components/portal/portal-shell";
import { Card, ProgressBar } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";

const stepGroups = [
  {
    title: "Личные данные",
    fields: [
      ["surname", "Фамилия"],
      ["givenName", "Имя"],
      ["previousNames", "Прежние фамилии"],
      ["birthDate", "Дата рождения"],
      ["birthPlace", "Место рождения"],
      ["birthCountry", "Страна рождения"],
      ["nationality", "Текущее гражданство"],
      ["nationalityAtBirth", "Гражданство при рождении"],
      ["gender", "Пол"],
      ["maritalStatus", "Семейное положение"],
      ["minorDetails", "Данные законного представителя для несовершеннолетнего"]
    ]
  },
  {
    title: "Паспорт и контакты",
    fields: [
      ["passportNumber", "Номер паспорта"],
      ["passportIssueDate", "Дата выдачи"],
      ["passportExpiryDate", "Дата окончания"],
      ["passportAuthority", "Кем выдан"],
      ["passportType", "Тип паспорта"],
      ["homeAddress", "Адрес проживания"],
      ["email", "Email"],
      ["phone", "Телефон"],
      ["currentResidence", "Текущая страна проживания"],
      ["residencePermitFields", "Поля по ВНЖ"]
    ]
  },
  {
    title: "Работа и поездка",
    fields: [
      ["occupation", "Род занятий"],
      ["employer", "Работодатель / компания"],
      ["fundsSource", "Источник средств"],
      ["mainDestination", "Основная страна назначения"],
      ["firstEntry", "Страна первого въезда"],
      ["travelPurpose", "Цель поездки"],
      ["arrivalDate", "Дата прибытия"],
      ["departureDate", "Дата выезда"],
      ["entriesRequested", "Количество въездов"],
      ["hostInfo", "Принимающая сторона / отель"],
      ["itineraryNotes", "Маршрут и заметки"]
    ]
  },
  {
    title: "История и подтверждения",
    fields: [
      ["previousVisas", "Предыдущие шенгенские визы"],
      ["fingerprintsCollected", "Отпечатки ранее сдавались"],
      ["previousRefusals", "Были ли отказы"],
      ["refusalNotes", "Пояснение по отказам"],
      ["expensesCoveredBy", "Кто оплачивает поездку"],
      ["accommodationPrepaid", "Жилье предоплачено"],
      ["transportPrepaid", "Транспорт предоплачен"],
      ["otherSupport", "Другая поддержка"],
      ["dataConsent", "Согласие на обработку данных"],
      ["accuracyConsent", "Подтверждение точности данных"],
      ["authorityDisclaimer", "Понимание, что решение принимает уполномоченный орган"]
    ]
  }
] as const;

export default function PortalFormsPage() {
  const { getCurrentApplication, updateVisaForm, getProgress } = useDemoStore();
  const application = getCurrentApplication();
  const [stepIndex, setStepIndex] = useState(0);
  const [message, setMessage] = useState("");

  if (!application) {
    return <PortalShell title="Анкета" description="Нужна активная демо-сессия."><Card>Нет доступа.</Card></PortalShell>;
  }

  const group = stepGroups[stepIndex];
  const progress = getProgress(application);

  return (
    <PortalShell title="Визовая анкета" description="Форма разделена на смысловые блоки, чтобы MVP не выглядел как одна перегруженная юридическая анкета.">
      <Card className="space-y-5">
        <div className="flex items-center justify-between text-sm text-[var(--muted)]">
          <span>{group.title}</span>
          <span>{stepIndex + 1} / {stepGroups.length}</span>
        </div>
        <ProgressBar value={progress.formCompletion} />
        <div className="grid gap-4 md:grid-cols-2">
          {group.fields.map(([key, label]) => {
            const value = application.visaForm[key];
            const isBoolean = typeof value === "boolean";
            return isBoolean ? (
              <label key={key} className="md:col-span-2 flex items-start gap-3 rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-4">
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(event) => updateVisaForm({ [key]: event.target.checked })}
                  className="mt-1 h-4 w-4"
                />
                <span className="text-sm text-[var(--muted)]">{label}</span>
              </label>
            ) : (
              <label key={key}>
                <span className="mb-2 block text-sm font-medium text-[var(--ink)]">{label}</span>
                <input
                  value={String(value)}
                  onChange={(event) => updateVisaForm({ [key]: event.target.value })}
                  className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3"
                />
              </label>
            );
          })}
        </div>
        <div className="flex flex-wrap justify-between gap-3">
          <button onClick={() => setStepIndex((current) => Math.max(current - 1, 0))} className="rounded-full border border-[var(--line)] px-5 py-3 text-sm" disabled={stepIndex === 0}>
            Назад
          </button>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {
                setMessage("Черновик сохранен.");
              }}
              className="rounded-full border border-[var(--line)] px-5 py-3 text-sm"
            >
              Сохранить
            </button>
            <button
              onClick={() => {
                setStepIndex((current) => Math.min(current + 1, stepGroups.length - 1));
                setMessage("Шаг сохранен.");
              }}
              className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white"
            >
              Далее
            </button>
          </div>
        </div>
        {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
      </Card>
    </PortalShell>
  );
}
