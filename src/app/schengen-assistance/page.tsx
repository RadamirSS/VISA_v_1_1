import { Card, Section } from "@/components/ui/primitives";

const pillars = [
  "Разбор цели поездки и маршрута подачи",
  "Подготовка анкеты и сопроводительной структуры",
  "Проверка документационного пакета",
  "Подготовка к записи и оплате после подключения интеграций"
];

export default function SchengenAssistancePage() {
  return (
    <Section eyebrow="Schengen" title="Поддержка по шенгенскому кейсу" description="Мы помогаем собрать и структурировать процесс подачи, но не обещаем решение, которое находится вне зоны контроля сервиса.">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Что делает команда</h3>
          <ul className="mt-4 space-y-3 text-[var(--muted)]">
            {pillars.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3 className="font-display text-2xl text-[var(--ink)]">Что остается за компетентным органом</h3>
          <p className="mt-4 text-[var(--muted)]">
            Решение о выдаче визы, подтверждение слота, финальный прием документов и любые официальные требования всегда определяются консульством, визовым центром или иной уполномоченной структурой.
          </p>
        </Card>
      </div>
    </Section>
  );
}
