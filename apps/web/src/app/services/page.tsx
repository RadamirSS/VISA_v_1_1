import { Card, Section } from "@/components/ui/primitives";

const items = [
  "Первичная консультация по стране подачи и маршруту",
  "Сбор базовой информации для менеджера",
  "Объяснение подготовительных шагов до начала записи",
  "Перевод в рабочий Telegram-поток для запроса записи",
  "Сопровождение по организационным вопросам подачи"
];

export default function ServicesPage() {
  return (
    <Section eyebrow="Услуги" title="Что мы делаем на этом этапе" description="Сайт предназначен для первого контакта и аккуратного старта кейса. Полный рабочий процесс ведется уже после связи с менеджером.">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <Card key={item}>
            <p className="font-medium text-[var(--ink)]">{item}</p>
            <p className="mt-3 text-sm text-[var(--muted)]">Финальные сроки, доступность записи и состав пакета могут зависеть от страны подачи и внешних систем.</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
