"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useDemoStore } from "@/lib/demo-store";
import { formatDate } from "@/lib/utils";
import { LeadStatusBadge } from "@/components/manager/lead-status-badge";
import { Card, Section } from "@/components/ui/primitives";

export default function ManagerLeadDetailPage() {
  const params = useParams<{ id: string }>();
  const { getLeadById, updateLeadStatus } = useDemoStore();
  const lead = getLeadById(params.id);

  if (!lead) {
    return (
      <Section eyebrow="Manager Demo" title="Заявка не найдена" description="Возможно, демо-состояние было очищено в браузере.">
        <Link href="/manager/leads" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
          Вернуться к списку
        </Link>
      </Section>
    );
  }

  return (
    <Section eyebrow="Lead Detail" title={lead.values.fullName} description="Карточка объединяет все данные первичной формы и показывает, какой invite увидит клиент после одобрения.">
      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="space-y-4">
          <div className="flex items-center gap-3">
            <LeadStatusBadge status={lead.status} />
            <span className="text-sm text-[var(--muted)]">{formatDate(lead.createdAt)}</span>
          </div>
          <Detail label="Телефон" value={lead.values.phone} />
          <Detail label="Telegram" value={lead.values.telegram} />
          <Detail label="Email" value={lead.values.email} />
          <Detail label="Гражданство" value={lead.values.citizenship} />
          <Detail label="Текущая локация" value={lead.values.location} />
          <Detail label="Страна подачи" value={lead.values.schengenCountry} />
          <Detail label="Цель поездки" value={lead.values.purpose} />
          <Detail label="Даты" value={lead.values.travelDates} />
          <Detail label="Предыдущий Шенген" value={lead.values.previousSchengen} />
          <Detail label="Комментарий" value={lead.values.comment} />
        </Card>
        <Card className="space-y-4">
          <p className="font-display text-2xl text-[var(--ink)]">Решение менеджера</p>
          <p className="text-[var(--muted)]">После одобрения пользователь сможет зарегистрироваться в портале по invite token.</p>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => updateLeadStatus(lead.id, "in_review")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
              In review
            </button>
            <button onClick={() => updateLeadStatus(lead.id, "approved")} className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
              Approved
            </button>
            <button onClick={() => updateLeadStatus(lead.id, "rejected")} className="rounded-full border border-rose-200 px-4 py-2 text-sm text-rose-700">
              Rejected
            </button>
          </div>
          {lead.inviteToken ? (
            <div className="rounded-[24px] bg-[var(--surface)] p-4">
              <p className="text-sm text-[var(--muted)]">Приглашение клиента</p>
              <p className="mt-2 font-medium text-[var(--ink)]">{lead.inviteToken}</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Используйте его на странице регистрации портала.</p>
              <Link href={`/portal/register?invite=${lead.inviteToken}`} className="mt-4 inline-flex rounded-full bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white">
                Открыть регистрацию
              </Link>
            </div>
          ) : null}
        </Card>
      </div>
    </Section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] bg-[var(--surface)] p-4">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-[var(--ink)]">{value}</p>
    </div>
  );
}
