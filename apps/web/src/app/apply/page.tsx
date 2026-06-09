import { ApplyForm } from "@/components/public/apply-form";
import { Section } from "@/components/ui/primitives";

const countryPrefillMap: Record<string, string> = {
  italy: "Италия",
  france: "Франция",
  spain: "Испания",
  greece: "Греция",
  germany: "Германия",
  portugal: "Португалия",
  consultation: "Не знаю, нужна консультация"
};

export default function ApplyPage({ searchParams }: { searchParams?: Record<string, string | string[] | undefined> }) {
  const rawCountry = searchParams?.country;
  const countryKey = typeof rawCountry === "string" ? rawCountry : undefined;
  const initialDesiredCountry = countryKey ? countryPrefillMap[countryKey] : undefined;

  return (
    <Section
      eyebrow="Первичная заявка"
      title="Оставьте короткий запрос"
      description="Нам нужна только базовая информация для связи и понимания направления. Паспортные данные, сканы документов и финансовая информация на сайте не собираются. Сервис помогает организовать сопровождение, но не гарантирует визу и не гарантирует доступность записи — даты зависят от внешних визовых систем."
    >
      <ApplyForm initialDesiredCountry={initialDesiredCountry} />
    </Section>
  );
}
