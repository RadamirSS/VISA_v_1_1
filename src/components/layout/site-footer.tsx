import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--line)] bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 text-sm text-[var(--muted)] sm:px-6 lg:grid-cols-[1.2fr_1fr_1fr] lg:px-8">
        <div>
          <p className="font-display text-lg text-[var(--ink)]">Visa Atelier</p>
          <p className="mt-3 max-w-md">
            Помогаем подготовить документы и управлять готовностью к подаче на шенгенскую визу. Финальное решение всегда принимает консульство или визовый центр.
          </p>
        </div>
        <div>
          <p className="font-medium text-[var(--ink)]">Маршрут клиента</p>
          <div className="mt-3 space-y-2">
            <Link href="/apply">Первичная заявка</Link>
            <br />
            <Link href="/manager/leads">Демо-кабинет менеджера</Link>
            <br />
            <Link href="/portal/dashboard">Личный кабинет</Link>
          </div>
        </div>
        <div>
          <p className="font-medium text-[var(--ink)]">Контакты</p>
          <p className="mt-3">Telegram: @visa_atelier_demo</p>
          <p>Почта: hello@visaatelier.demo</p>
          <p>Белград / удаленно по Европе</p>
        </div>
      </div>
    </footer>
  );
}
