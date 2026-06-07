import { ApplyForm } from "@/components/public/apply-form";
import { Section } from "@/components/ui/primitives";

export default function ApplyPage() {
  return (
    <Section eyebrow="Первичная заявка" title="Оставьте короткий запрос" description="Нам нужна только базовая информация для связи и понимания направления. Паспортные данные, сканы документов и финансовая информация на сайте не собираются.">
      <ApplyForm />
    </Section>
  );
}
