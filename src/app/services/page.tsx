import { Card, Section } from "@/components/ui/primitives";

const items = [
  "Первичная консультация и маршрутизация кейса",
  "Сбор и структура пакета документов",
  "Помощь в заполнении визовых форм",
  "Подготовка к записи в визовый центр",
  "Сопровождение по чек-листу и статусам"
];

export default function ServicesPage() {
  return (
    <Section eyebrow="Услуги" title="Что получает заявитель" description="Модель сервиса построена вокруг подготовки и контроля комплектности, а не вокруг обещаний результата.">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <Card key={item}>
            <p className="font-medium text-[var(--ink)]">{item}</p>
            <p className="mt-3 text-sm text-[var(--muted)]">Подходит для демо MVP и легко связывается с будущими API и внутренними операционными системами.</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
