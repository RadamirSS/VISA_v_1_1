"use client";

import Link from "next/link";
import { useState } from "react";
import { useDemoStore } from "@/lib/demo-store";
import { Card } from "@/components/ui/primitives";

export function RegisterForm({ initialInvite }: { initialInvite: string }) {
  const { registerWithInvite, getApplicationByInvite } = useDemoStore();
  const [invite, setInvite] = useState(initialInvite);
  const [password, setPassword] = useState("");
  const [result, setResult] = useState("");

  const application = getApplicationByInvite(invite);

  return (
    <Card className="mx-auto max-w-2xl space-y-5">
      <Field label="Invite token" value={invite} onChange={setInvite} />
      <Field label="Создайте пароль" value={password} onChange={setPassword} type="password" />
      {application ? (
        <div className="rounded-[24px] bg-[var(--surface)] p-4 text-sm text-[var(--muted)]">
          Клиент: <span className="font-medium text-[var(--ink)]">{application.fullName}</span>
          <br />
          Направление: <span className="font-medium text-[var(--ink)]">{application.visaDirection}</span>
        </div>
      ) : null}
      <button
        onClick={() => setResult(registerWithInvite(invite, password).message)}
        className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white"
      >
        Создать доступ
      </button>
      {result ? <p className="text-sm text-[var(--muted)]">{result}</p> : null}
      <div className="flex flex-wrap gap-3 text-sm">
        <Link href="/portal/login" className="text-[var(--accent)]">Уже есть доступ? Войти</Link>
        <Link href="/manager/leads" className="text-[var(--accent)]">Вернуться в демо менеджера</Link>
      </div>
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-[var(--ink)]">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3"
      />
    </label>
  );
}
