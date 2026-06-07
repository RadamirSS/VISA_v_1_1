import { Card, Section } from "@/components/ui/primitives";

export default function ContactsPage() {
  return (
    <Section eyebrow="Контакты" title="Связаться с командой" description="Для MVP контакты носят демонстрационный характер и показывают точки входа в реальном продукте.">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="font-medium text-[var(--ink)]">Telegram</p>
          <p className="mt-3 text-[var(--muted)]">@visa_atelier_demo</p>
        </Card>
        <Card>
          <p className="font-medium text-[var(--ink)]">Email</p>
          <p className="mt-3 text-[var(--muted)]">hello@visaatelier.demo</p>
        </Card>
        <Card>
          <p className="font-medium text-[var(--ink)]">Формат работы</p>
          <p className="mt-3 text-[var(--muted)]">Удаленно, с координацией по Европе и СНГ</p>
        </Card>
      </div>
    </Section>
  );
}
