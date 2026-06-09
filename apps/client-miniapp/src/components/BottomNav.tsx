"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Главная" },
  { href: "/applicants", label: "Анкеты" },
  { href: "/case", label: "Заявка" },
  { href: "/appointment", label: "Даты" },
  { href: "/settings", label: "Настройки" }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="bottom-nav">
      {links.map((link) => (
        <Link key={link.href} className={pathname === link.href ? "nav-link active" : "nav-link"} href={link.href}>
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
