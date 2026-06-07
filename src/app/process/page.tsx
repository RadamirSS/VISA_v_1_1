import { Card, Section } from "@/components/ui/primitives";

const stages = [
  "Сайт и первичная заявка",
  "Проверка менеджером",
  "Выдача invite-ссылки в кабинет",
  "Заполнение профиля и анкеты",
  "Загрузка метаданных документов",
  "Готовность к записи и демо-бот"
];

export default function ProcessPage() {
  return (
    <Section eyebrow="Процесс" title="Путь клиента разбит на понятные этапы" description="Так легче объяснять сервис пользователю и потом подключать реальные операционные шаги без полной переделки интерфейса.">
      <div className="grid gap-4">
        {stages.map((stage, index) => (
          <Card key={stage} className="flex items-center gap-5">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface)] font-semibold text-[var(--accent)]">{index + 1}</div>
            <div>
              <p className="font-medium text-[var(--ink)]">{stage}</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Каждый этап имеет собственный интерфейс, статусы и placeholder-точки интеграции.</p>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}
