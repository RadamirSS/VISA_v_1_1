"use client";

import Link from "next/link";
import { useDemoStore } from "@/lib/demo-store";
import { formatDate } from "@/lib/utils";
import { LeadStatusBadge } from "@/components/manager/lead-status-badge";
import { Card, Section } from "@/components/ui/primitives";

export default function ManagerLeadsPage() {
  const { state, updateLeadStatus } = useDemoStore();

  return (
    <Section eyebrow="Manager Demo" title="Входящие заявки" description="Это демонстрационная внутренняя зона без реальной авторизации. Здесь видно, как лид переходит в статус одобрения и получает invite в портал.">
      <div className="grid gap-4">
        {state.leads.map((lead) => (
          <Card key={lead.id} className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <p className="font-display text-2xl text-[var(--ink)]">{lead.values.fullName}</p>
                <LeadStatusBadge status={lead.status} />
              </div>
              <p className="mt-2 text-sm text-[var(--muted)]">
                {lead.values.schengenCountry} • {lead.values.purpose} • {lead.values.location}
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">Создано: {formatDate(lead.createdAt)}</p>
              {lead.inviteToken ? <p className="mt-2 text-sm text-[var(--accent)]">Invite token: {lead.inviteToken}</p> : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={() => updateLeadStatus(lead.id, "new")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                New
              </button>
              <button onClick={() => updateLeadStatus(lead.id, "in_review")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                In review
              </button>
              <button onClick={() => updateLeadStatus(lead.id, "approved")} className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
                Approve
              </button>
              <button onClick={() => updateLeadStatus(lead.id, "rejected")} className="rounded-full border border-rose-200 px-4 py-2 text-sm text-rose-700">
                Reject
              </button>
              <Link href={`/manager/leads/${lead.id}`} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                Открыть
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}
