import { Card, Section } from "@/components/ui/primitives";

export default function AboutPage() {
  return (
    <Section eyebrow="О компании" title="Спокойная, прозрачная помощь в подготовке к подаче" description="Мы не обещаем результат вместо консульства. Мы помогаем заявителю видеть, что именно уже готово, а что еще требует внимания.">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Подготовка</h3>
          <p className="mt-3 text-[var(--muted)]">Формируем понятный список документов и объясняем, что нужно именно для вашего сценария поездки.</p>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Проверка</h3>
          <p className="mt-3 text-[var(--muted)]">Менеджер видит статус заявки и может перевести клиента в этап документальной подготовки.</p>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Контроль готовности</h3>
          <p className="mt-3 text-[var(--muted)]">Личный кабинет и бот показывают прогресс без иллюзии, что внешние системы уже подключены.</p>
        </Card>
      </div>
    </Section>
  );
}
