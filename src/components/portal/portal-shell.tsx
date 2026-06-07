"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { useDemoStore } from "@/lib/demo-store";

const nav = [
  { href: "/portal/dashboard", label: "Обзор" },
  { href: "/portal/profile", label: "Профиль" },
  { href: "/portal/forms", label: "Анкета" },
  { href: "/portal/documents", label: "Документы" },
  { href: "/portal/status", label: "Статус" },
  { href: "/portal/appointment", label: "Запись" }
];

export function PortalShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  const pathname = usePathname();
  const { logout, getCurrentApplication, getProgress } = useDemoStore();
  const application = getCurrentApplication();
  const progress = getProgress(application);

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[260px_1fr] lg:px-8">
      <aside className="space-y-4 rounded-[30px] border border-[var(--line)] bg-white p-5 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--accent)]">Portal</p>
          <h2 className="mt-2 font-display text-2xl text-[var(--ink)]">Личный кабинет</h2>
        </div>
        <div className="rounded-3xl bg-[var(--surface)] p-4">
          <p className="text-sm text-[var(--muted)]">Общая готовность</p>
          <p className="mt-2 text-3xl font-semibold text-[var(--ink)]">{progress.totalCompletion}%</p>
        </div>
        <nav className="grid gap-2">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={
                pathname === item.href
                  ? "rounded-2xl bg-[var(--ink)] px-4 py-3 text-sm font-medium text-white"
                  : "rounded-2xl px-4 py-3 text-sm text-[var(--muted)] transition hover:bg-[var(--surface)] hover:text-[var(--ink)]"
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button onClick={logout} className="w-full rounded-full border border-[var(--line)] px-4 py-3 text-sm font-medium text-[var(--ink)]">
          Выйти
        </button>
      </aside>
      <div className="space-y-6">
        <div className="rounded-[30px] border border-[var(--line)] bg-white p-6 shadow-soft">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--accent)]">{application?.visaDirection ?? "Demo"}</p>
          <h1 className="mt-3 font-display text-3xl text-[var(--ink)]">{title}</h1>
          <p className="mt-3 max-w-3xl text-[var(--muted)]">{description}</p>
        </div>
        {children}
      </div>
    </div>
  );
}
