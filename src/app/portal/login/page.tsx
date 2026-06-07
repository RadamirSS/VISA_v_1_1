"use client";

import Link from "next/link";
import { useState } from "react";
import { useDemoStore } from "@/lib/demo-store";
import { Card, Section } from "@/components/ui/primitives";

export default function PortalLoginPage() {
  const { loginMock } = useDemoStore();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("");
  const [result, setResult] = useState("");

  return (
    <Section eyebrow="Portal Login" title="Вход в личный кабинет" description="Для демо можно использовать одобренный invite и затем войти под email клиента.">
      <Card className="mx-auto max-w-2xl space-y-5">
        <Field label="Email" value={email} onChange={setEmail} />
        <Field label="Пароль" value={password} onChange={setPassword} type="password" />
        <button onClick={() => setResult(loginMock(email, password).message)} className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
          Войти
        </button>
        {result ? <p className="text-sm text-[var(--muted)]">{result}</p> : null}
        <div className="rounded-[24px] bg-[var(--surface)] p-4 text-sm text-[var(--muted)]">
          Демо-пользователь уже есть в системе: <span className="font-medium text-[var(--ink)]">demo@example.com</span>. Сначала задайте ему пароль на странице регистрации, если локальное состояние пустое.
        </div>
        <Link href="/portal/register?invite=INVITE-DEMO-2026" className="text-sm text-[var(--accent)]">
          Открыть регистрацию по демо-приглашению
        </Link>
      </Card>
    </Section>
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
