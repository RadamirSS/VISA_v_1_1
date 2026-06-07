"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Главная" },
  { href: "/about", label: "О компании" },
  { href: "/services", label: "Услуги" },
  { href: "/schengen", label: "Шенген" },
  { href: "/process", label: "Процесс" },
  { href: "/countries", label: "Страны" },
  { href: "/faq", label: "FAQ" },
  { href: "/contacts", label: "Контакты" }
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-white/50 bg-[rgba(247,245,239,0.92)] backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--accent)] text-sm font-semibold text-white">
            VA
          </div>
          <div>
            <div className="font-display text-lg text-[var(--ink)]">Visa Atelier</div>
            <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Visa assistance</div>
          </div>
        </Link>
        <nav className="hidden items-center gap-5 text-sm md:flex">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={active ? "font-medium text-[var(--ink)]" : "text-[var(--muted)] transition hover:text-[var(--ink)]"}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/apply" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white transition hover:bg-[var(--accent-strong)]">
            Оставить заявку
          </Link>
        </div>
      </div>
    </header>
  );
}
