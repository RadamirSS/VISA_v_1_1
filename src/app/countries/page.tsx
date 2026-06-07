import { Card, Section } from "@/components/ui/primitives";

const countries = [
  ["Италия", "Частый выбор для туризма и посещения друзей."],
  ["Франция", "Подходит для туризма, бизнес-поездок и family visit."],
  ["Испания", "В демо показывает сценарий с отсутствием слотов."],
  ["Греция", "Маршрут можно быстро адаптировать под сезонные кейсы."]
];

export default function CountriesPage() {
  return (
    <Section eyebrow="Направления" title="Страны и сценарии подачи" description="В MVP мы показываем, как интерфейс поддерживает разные направления, не создавая ложных обещаний по доступности записи.">
      <div className="grid gap-4 md:grid-cols-2">
        {countries.map(([country, note]) => (
          <Card key={country}>
            <p className="font-display text-2xl text-[var(--ink)]">{country}</p>
            <p className="mt-3 text-[var(--muted)]">{note}</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
