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
          <h3 className="font-display text-2xl text-[var(--ink)]">Ручная первичная консультация</h3>
          <p className="mt-3 text-[var(--muted)]">После заявки менеджер связывается с клиентом, уточняет цель поездки и предлагает подходящий следующий шаг без публичного портала.</p>
        </Card>
      </div>
    </Section>
  );
}
