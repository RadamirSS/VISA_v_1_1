"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { BottomNav } from "./BottomNav";

export function AppShell({
  children,
  title,
  subtitle,
  hideEyebrow = false
}: {
  children: ReactNode;
  title: string;
  subtitle?: string;
  hideEyebrow?: boolean;
}) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <header className="hero-card">
        <div>
          {hideEyebrow ? <p className="eyebrow">Личный кабинет визового сопровождения</p> : <p className="eyebrow">Telegram Mini App</p>}
          <h1>{title}</h1>
          {subtitle ? <p className="hero-copy">{subtitle}</p> : null}
        </div>
        {pathname !== "/" ? (
          <Link className="ghost-button" href="/">
            На главную
          </Link>
        ) : null}
      </header>
      <main className="page-content">{children}</main>
      <BottomNav />
    </div>
  );
}
