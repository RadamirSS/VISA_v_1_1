import { Card, Section } from "@/components/ui/primitives";

const questions = [
  ["Вы гарантируете получение визы?", "Нет. Мы помогаем подготовить пакет документов и процесс, а финальное решение принимает компетентный орган."],
  ["Можно ли сразу записаться через сайт?", "Нет, в MVP запись и оплата показаны как placeholder-функции без реальных внешних подключений."],
  ["Где хранятся документы?", "В демо хранятся только метаданные файлов. Безопасное хранилище нужно подключать отдельно."],
  ["Есть ли личный кабинет?", "Да, после одобрения заявки менеджером пользователь получает доступ в mock-портал."]
];

export default function FaqPage() {
  return (
    <Section eyebrow="FAQ" title="Частые вопросы" description="Формулировки нарочно сделаны осторожными и прозрачными, чтобы не создавать юридически рискованных ожиданий.">
      <div className="grid gap-4">
        {questions.map(([question, answer]) => (
          <Card key={question}>
            <p className="font-medium text-[var(--ink)]">{question}</p>
            <p className="mt-3 text-[var(--muted)]">{answer}</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}
