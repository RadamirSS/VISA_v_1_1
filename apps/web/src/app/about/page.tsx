import { Card, Section } from "@/components/ui/primitives";

export default function AboutPage() {
  return (
    <Section eyebrow="О компании" title="Спокойный сервис без агрессивных обещаний" description="Мы не заменяем собой визовый центр или консульство. Наша задача — помочь клиенту на старте, объяснить маршрут подачи и собрать базовую информацию для менеджера.">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Честная коммуникация</h3>
          <p className="mt-3 text-[var(--muted)]">Мы не обещаем гарантированную визу, гарантированный слот или специальный доступ к внешним системам.</p>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Минимум данных на сайте</h3>
          <p className="mt-3 text-[var(--muted)]">До первичной консультации сайт собирает только базовую информацию для связи и понимания направления.</p>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Дальнейшая работа через менеджера и бот</h3>
          <p className="mt-3 text-[var(--muted)]">Запросы на запись, статусы, промокоды и рабочий поток вынесены в отдельный Telegram-бот.</p>
        </Card>
      </div>
    </Section>
  );
}
