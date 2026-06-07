import { Card, Section } from "@/components/ui/primitives";

const docs = [
  "Загранпаспорт",
  "Фото",
  "Страховка",
  "Бронь билетов и проживания",
  "Банковская выписка",
  "Подтверждение занятости или дохода"
];

export default function DocumentsPage() {
  return (
    <Section eyebrow="Документы" title="Базовый обзор комплекта" description="Точный перечень зависит от направления и профиля заявителя. Финальный пакет всегда проверяется по требованиям визового центра и консульства.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {docs.map((doc) => (
          <Card key={doc}>
            <p className="font-medium text-[var(--ink)]">{doc}</p>
            <p className="mt-3 text-sm text-[var(--muted)]">В кабинете для каждого документа есть статус, комментарий менеджера и подсказка по формату.</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
