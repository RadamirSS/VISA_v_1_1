import Link from "next/link";
import countries from "@config/countries.ru.json";
import { Card, Section } from "@/components/ui/primitives";

export default function CountriesPage() {
  return (
    <Section eyebrow="Страны" title="Направления, по которым мы консультируем" description="Здесь собраны основные сценарии подачи. Если вы не уверены в стране, можно оставить заявку на консультацию.">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {countries.map((country) => (
          <Card key={country.code}>
            <p className="font-display text-2xl text-[var(--ink)]">{country.nameRu}</p>
            <p className="mt-3 text-[var(--muted)]">{country.suitsForRu}</p>
            <Link href={`/countries/${country.slug}`} className="mt-5 inline-flex text-sm font-medium text-[var(--accent)]">
              Перейти к странице страны
            </Link>
          </Card>
        ))}
      </div>
    </Section>
  );
}
