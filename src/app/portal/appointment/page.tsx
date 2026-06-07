"use client";

import Link from "next/link";
import { useState } from "react";
import { PortalShell } from "@/components/portal/portal-shell";
import { Card } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";

export default function PortalAppointmentPage() {
  const { getCurrentApplication, placeholders } = useDemoStore();
  const application = getCurrentApplication();
  const [searchTerm, setSearchTerm] = useState("Италия / Белград");
  const [message, setMessage] = useState("");

  if (!application) {
    return <PortalShell title="Запись" description="Нужна активная демо-сессия."><Card>Нет доступа.</Card></PortalShell>;
  }

  const slots = placeholders.searchAppointmentSlots(searchTerm);

  return (
    <PortalShell title="Запись и оплата" description="Маршрут готов для подключения реального booking-провайдера и payment-провайдера, но в MVP обе функции остаются безопасными placeholder-операциями.">
      <Card className="space-y-5">
        <label>
          <span className="mb-2 block text-sm font-medium text-[var(--ink)]">Поиск слотов</span>
          <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
        </label>
        <div className="grid gap-3">
          {slots.length === 0 ? (
            <div className="rounded-[24px] bg-[var(--surface)] p-4 text-sm text-[var(--muted)]">Слоты не найдены. Можно вернуться позже или обсудить альтернативное направление с менеджером.</div>
          ) : (
            slots.map((slot) => (
              <div key={slot} className="rounded-[24px] border border-[var(--line)] bg-white p-4 text-sm text-[var(--ink)]">
                Доступный слот: {slot}
              </div>
            ))
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={() => setMessage(placeholders.bookAppointmentPlaceholder())} className="rounded-full bg-slate-300 px-5 py-3 text-sm font-medium text-slate-700">
            Book appointment
          </button>
          <button onClick={() => setMessage(placeholders.createPaymentPlaceholder())} className="rounded-full bg-slate-300 px-5 py-3 text-sm font-medium text-slate-700">
            Pay
          </button>
          <Link href="/telegram-bot-demo" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-medium text-[var(--ink)]">
            Открыть Telegram demo
          </Link>
        </div>
        {message ? <div className="rounded-[24px] bg-[var(--surface)] p-4 text-sm text-[var(--muted)]">{message}</div> : null}
      </Card>
    </PortalShell>
  );
}
