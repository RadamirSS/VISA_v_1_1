"use client";

import Link from "next/link";
import { PortalShell } from "@/components/portal/portal-shell";
import { Card, ProgressBar } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";

export default function PortalDashboardPage() {
  const { getCurrentApplication, getProgress } = useDemoStore();
  const application = getCurrentApplication();
  const progress = getProgress(application);

  if (!application) {
    return <MissingAccess />;
  }

  const nextAction =
    progress.profileCompletion < 70
      ? "Заполнить профиль"
      : progress.formCompletion < 70
        ? "Дозаполнить визовую анкету"
        : progress.missingDocuments > 0
          ? "Добавить документы"
          : "Открыть демо-запись";

  return (
    <PortalShell title="Обзор заявки" description="Здесь собран основной срез по готовности кейса, чтобы клиент сразу видел следующий шаг.">
      <div className="grid gap-4 xl:grid-cols-4">
        <Metric title="Направление" value={application.visaDirection} note="Текущая страна подачи" />
        <Metric title="Общая готовность" value={`${progress.totalCompletion}%`} note="На основе профиля, анкеты и документов" />
        <Metric title="Не хватает документов" value={`${progress.missingDocuments}`} note="Считаются обязательные позиции" />
        <Metric title="Статус менеджера" value="Request approved" note="Можно продолжать подготовку" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="space-y-5">
          <h3 className="font-display text-2xl text-[var(--ink)]">Прогресс по модулям</h3>
          <ProgressRow label="Профиль" value={progress.profileCompletion} />
          <ProgressRow label="Анкета" value={progress.formCompletion} />
          <ProgressRow label="Документы" value={progress.documentsCompletion} />
        </Card>
        <Card className="space-y-4">
          <p className="font-display text-2xl text-[var(--ink)]">Следующее действие</p>
          <p className="text-[var(--muted)]">{nextAction}</p>
          <div className="flex flex-wrap gap-3">
            <Link href="/portal/profile" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
              Открыть профиль
            </Link>
            <Link href="/portal/forms" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-medium text-[var(--ink)]">
              Анкета
            </Link>
          </div>
        </Card>
      </div>
    </PortalShell>
  );
}

function Metric({ title, value, note }: { title: string; value: string; note: string }) {
  return (
    <Card>
      <p className="text-sm text-[var(--muted)]">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-[var(--ink)]">{value}</p>
      <p className="mt-2 text-sm text-[var(--muted)]">{note}</p>
    </Card>
  );
}

function ProgressRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-[var(--muted)]">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <ProgressBar value={value} />
    </div>
  );
}

function MissingAccess() {
  return (
    <PortalShell title="Нет активной сессии" description="Сначала откройте регистрацию по invite или войдите под одобренным клиентом.">
      <Card className="space-y-4">
        <Link href="/portal/register?invite=INVITE-DEMO-2026" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
          Перейти к регистрации
        </Link>
      </Card>
    </PortalShell>
  );
}
