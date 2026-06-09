import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--line)] bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 text-sm text-[var(--muted)] sm:px-6 lg:grid-cols-[1.2fr_1fr_1fr] lg:px-8">
        <div>
          <p className="font-display text-lg text-[var(--ink)]">Visa Atelier</p>
          <p className="mt-3 max-w-md">
            Визовое сопровождение с личным кабинетом: документы, статусы и связь с менеджером — в одном месте. Мы не являемся официальным консульством или визовым центром и не гарантируем визу или запись.
          </p>
        </div>
        <div>
          <p className="font-medium text-[var(--ink)]">Разделы сайта</p>
          <div className="mt-3 space-y-2">
            <Link href="/services">Услуги</Link>
            <br />
            <Link href="/countries">Страны</Link>
            <br />
            <Link href="/apply">Оставить заявку</Link>
          </div>
        </div>
        <div>
          <p className="font-medium text-[var(--ink)]">Контакты</p>
          <p className="mt-3">Telegram: @visa_atelier_contact</p>
          <p>Почта: hello@visaatelier.example</p>
          <p>Работаем онлайн и по предварительной консультации</p>
        </div>
      </div>
    </footer>
  );
}
