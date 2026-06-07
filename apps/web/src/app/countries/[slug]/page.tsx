import Link from "next/link";
import { notFound } from "next/navigation";
import countries from "@config/countries.ru.json";
import { Card, Section } from "@/components/ui/primitives";

type Params = { slug: string };

export function generateStaticParams() {
  return countries.map((country) => ({ slug: country.slug }));
}

export default function CountryDetailPage({ params }: { params: Params }) {
  const country = countries.find((item) => item.slug === params.slug);

  if (!country) {
    notFound();
  }

  return (
    <Section eyebrow="Страна подачи" title={`${country.nameRu}: краткий ориентир по направлению`} description={country.suitsForRu}>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Для кого может подойти</h3>
          <p className="mt-4 text-[var(--muted)]">{country.suitsForRu}</p>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Распространенные цели поездки</h3>
          <ul className="mt-4 space-y-3 text-[var(--muted)]">
            {country.travelPurposesRu.map((purpose) => (
              <li key={purpose}>{purpose}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Что помогает подготовить агентство</h3>
          <ul className="mt-4 space-y-3 text-[var(--muted)]">
            {country.preparationAreasRu.map((area) => (
              <li key={area}>{area}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Важно знать</h3>
          <p className="mt-4 text-[var(--muted)]">Мы помогаем подготовить заявку и маршрут подачи.</p>
          <p className="mt-4 text-[var(--muted)]">{country.appointmentNoteRu}</p>
          <p className="mt-4 text-[var(--muted)]">{country.processingDisclaimerRu}</p>
          <p className="mt-4 text-[var(--muted)]">{country.providerDisclaimerRu}</p>
        </Card>
      </div>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link href={`/apply?country=${country.slug}`} className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white">
          Оставить заявку
        </Link>
        <Link href="/apply?country=consultation" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-medium text-[var(--ink)]">
          Не знаю страну — нужна консультация
        </Link>
      </div>
    </Section>
  );
}
