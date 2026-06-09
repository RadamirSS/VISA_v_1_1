import { Card, Section } from "@/components/ui/primitives";

export default function ContactsPage() {
  return (
    <Section
      eyebrow="Контакты"
      title="Связаться с командой"
      description="Если вы не уверены в стране подачи или хотите начать с консультации, оставьте заявку на сайте или свяжитесь с нами по указанным каналам. Мы не гарантируем визу и не гарантируем запись."
    >
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="font-medium text-[var(--ink)]">Telegram</p>
          <p className="mt-3 text-[var(--muted)]">@visa_atelier_contact</p>
        </Card>
        <Card>
          <p className="font-medium text-[var(--ink)]">Email</p>
          <p className="mt-3 text-[var(--muted)]">hello@visaatelier.example</p>
        </Card>
        <Card>
          <p className="font-medium text-[var(--ink)]">Формат</p>
          <p className="mt-3 text-[var(--muted)]">Онлайн-консультация и дальнейшее сопровождение через менеджера после первичной заявки</p>
        </Card>
      </div>
    </Section>
  );
}
