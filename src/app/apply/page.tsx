import { ApplyForm } from "@/components/public/apply-form";
import { Section } from "@/components/ui/primitives";

export default function ApplyPage() {
  return (
    <Section eyebrow="Первичная заявка" title="Расскажите о поездке и вашем кейсе" description="Форма разбита на шаги, чтобы клиент видел прогресс, а менеджер получал структурированный лид.">
      <ApplyForm />
    </Section>
  );
}
