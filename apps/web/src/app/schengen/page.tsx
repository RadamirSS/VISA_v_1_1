import { Card, Section } from "@/components/ui/primitives";

const points = [
  "Мы помогаем подготовить заявку и маршрут подачи.",
  "Доступность записи зависит от внешних систем и визовых центров.",
  "Сайт не собирает паспортные данные, сканы документов или банковскую информацию.",
  "Финальное решение принимает консульство или уполномоченный визовый орган."
];

export default function SchengenPage() {
  return (
    <Section eyebrow="Schengen" title="Поддержка по шенгенскому кейсу" description="Этот сайт нужен для первичного контакта и старта кейса. Детальная рабочая часть по записи ведется через отдельный Telegram-бот и менеджера.">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Что делает команда</h3>
          <ul className="mt-4 space-y-3 text-[var(--muted)]">
            {points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Чего мы не обещаем</h3>
          <p className="mt-4 text-[var(--muted)]">
            Мы не гарантируем запись, не гарантируем выдачу визы и не заявляем об официальном партнерстве с консульствами или визовыми центрами.
          </p>
        </Card>
      </div>
    </Section>
  );
}
