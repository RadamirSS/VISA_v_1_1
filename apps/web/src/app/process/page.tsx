import { Card, Section } from "@/components/ui/primitives";

const stages = [
  "Клиент оставляет короткую заявку на сайте",
  "Менеджер связывается и уточняет страну, цель и состав заявителей",
  "Мы помогаем подготовить заявку и маршрут подачи",
  "Менеджер объясняет ограничения по срокам, записи и составу пакета",
  "Следующий шаг по сопровождению согласуется вручную под конкретный кейс"
];

export default function ProcessPage() {
  return (
    <Section eyebrow="Процесс" title="Понятный путь без лишнего интерфейса" description="Сайт остается публичной страницей с понятным маршрутом: изучить информацию, оставить запрос и дождаться связи с менеджером.">
      <div className="grid gap-4">
        {stages.map((stage, index) => (
          <Card key={stage} className="flex items-center gap-5">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface)] font-semibold text-[var(--accent)]">{index + 1}</div>
            <div>
              <p className="font-medium text-[var(--ink)]">{stage}</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Доступность записи зависит от визовых центров, консульств и внешних систем, а не от самого сайта.</p>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}
