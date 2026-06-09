"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Главная", match: (pathname: string) => pathname === "/" },
  { href: "/applicants", label: "Анкеты", match: (pathname: string) => pathname.startsWith("/applicants") },
  { href: "/case", label: "Заявка", match: (pathname: string) => pathname.startsWith("/case") },
  { href: "/appointment", label: "Запись", match: (pathname: string) => pathname.startsWith("/appointment") },
  { href: "/documents", label: "Документы", match: (pathname: string) => pathname.startsWith("/documents") }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="bottom-nav">
      {links.map((link) => (
        <Link key={link.href} className={link.match(pathname) ? "nav-link active" : "nav-link"} href={link.href}>
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
