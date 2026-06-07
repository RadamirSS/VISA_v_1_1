import { Card, Section } from "@/components/ui/primitives";

const stages = [
  "Клиент оставляет короткую заявку на сайте",
  "Менеджер связывается и уточняет страну, цель и состав заявителей",
  "Если нужен запрос записи, клиент переводится в Telegram-бот",
  "Через бот создается рабочая заявка на поиск или сопровождение записи",
  "Менеджер и внешние системы обрабатывают запрос в рамках доступных возможностей"
];

export default function ProcessPage() {
  return (
    <Section eyebrow="Процесс" title="Понятный путь без лишнего интерфейса" description="Мы убрали публичный личный кабинет и тяжелую демо-логику, чтобы сайт оставался понятным и не собирал лишние чувствительные данные.">
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
