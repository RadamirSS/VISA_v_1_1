import Link from "next/link";
import { Section, Card } from "@/components/ui/primitives";

const services = [
  "Предварительная оценка кейса и маршрута подачи",
  "Подготовка списка документов и проверка комплектности",
  "Сопровождение по анкете и статусам",
  "Подготовка к записи в визовый центр"
];

const steps = [
  "Оставляете заявку и рассказываете о поездке",
  "Менеджер оценивает кейс и открывает доступ в кабинет",
  "Вы заполняете формы и прикладываете документы",
  "Команда проверяет комплект и готовит к записи"
];

export default function HomePage() {
  return (
    <>
      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8 lg:py-20">
        <div className="space-y-7">
          <div className="inline-flex rounded-full border border-[var(--line)] bg-white px-4 py-2 text-xs uppercase tracking-[0.24em] text-[var(--accent)] shadow-soft">
            Schengen visa assistance MVP
          </div>
          <div>
            <h1 className="max-w-4xl font-display text-5xl leading-tight text-[var(--ink)] sm:text-6xl">
              Помогаем подготовить пакет документов для шенгенской визы без перегруженного процесса
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-[var(--muted)]">
              Премиальный, но спокойный сервис для граждан России: заявка, проверка менеджером, личный кабинет, чек-лист документов и демо-запись в визовый центр в одном сценарии.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/apply" className="rounded-full bg-[var(--accent)] px-6 py-3.5 text-sm font-medium text-white">
              Оставить заявку
            </Link>
            <Link href="/telegram-bot-demo" className="rounded-full border border-[var(--line)] px-6 py-3.5 text-sm font-medium text-[var(--ink)]">
              Посмотреть Telegram flow
            </Link>
          </div>
          <p className="text-sm text-[var(--muted)]">
            Мы помогаем подготовить комплект и отслеживать готовность. Финальное решение о визе принимает консульство или визовый орган.
          </p>
        </div>

        <Card className="relative overflow-hidden bg-[linear-gradient(180deg,#1f4850_0%,#14363b_100%)] text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.2),transparent_35%)]" />
          <div className="relative space-y-6">
            <div className="rounded-[24px] bg-white/10 p-5 backdrop-blur">
              <p className="text-sm uppercase tracking-[0.24em] text-white/70">Демо-маршрут</p>
              <p className="mt-3 text-3xl font-semibold">От маркетингового сайта до записи</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Metric title="Статус клиента" value="Approved" note="после ревью менеджером" />
              <Metric title="Кабинет" value="Portal" note="анкета, документы, статус" />
              <Metric title="Интеграции" value="Mocked" note="без реальных платежей и слотов" />
              <Metric title="Язык UI" value="RU" note="с учетом legal-safe wording" />
            </div>
          </div>
        </Card>
      </section>

      <Section eyebrow="О сервисе" title="Сайт, кабинет и бот построены как единый путь клиента" description="MVP показывает, как потенциальный заявитель движется от консультации к подготовке документов и готовности к записи.">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h3 className="font-display text-2xl text-[var(--ink)]">Что включено</h3>
            <ul className="mt-5 space-y-3 text-[var(--muted)]">
              {services.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
          <Card>
            <h3 className="font-display text-2xl text-[var(--ink)]">Как это работает</h3>
            <ol className="mt-5 space-y-4 text-[var(--muted)]">
              {steps.map((item, index) => (
                <li key={item} className="flex gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface)] text-sm font-semibold text-[var(--accent)]">{index + 1}</span>
                  <span>{item}</span>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      </Section>

      <Section eyebrow="Направления" title="Популярные страны подачи" description="В интерфейсе можно переключать направления и готовность кейса без правок backend-интеграций.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {["Италия", "Франция", "Испания", "Греция"].map((country) => (
            <Card key={country}>
              <p className="text-sm uppercase tracking-[0.24em] text-[var(--accent)]">{country}</p>
              <p className="mt-4 text-sm text-[var(--muted)]">
                Подготовка документов, трекинг готовности и демо-поток записи для кейсов по направлению {country}.
              </p>
            </Card>
          ))}
        </div>
      </Section>

      <Section eyebrow="Стоимость" title="Цена обсуждается после консультации" description="Мы сознательно не показываем обещающую фиксированную цену без оценки кейса. Так продукт звучит аккуратно и профессионально.">
        <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
          <Card>
            <p className="font-display text-2xl text-[var(--ink)]">Что влияет на стоимость</p>
            <p className="mt-4 text-[var(--muted)]">
              Страна подачи, срочность, число заявителей, необходимость дополнительных документов и глубина сопровождения.
            </p>
          </Card>
          <Card>
            <p className="font-display text-2xl text-[var(--ink)]">Как мы формулируем оффер</p>
            <p className="mt-4 text-[var(--muted)]">
              Стоимость и формат сопровождения обсуждаются после консультации. Никаких обещаний по решению консульства мы не даем.
            </p>
          </Card>
        </div>
      </Section>
    </>
  );
}

function Metric({ title, value, note }: { title: string; value: string; note: string }) {
  return (
    <div className="rounded-[24px] border border-white/15 bg-white/5 p-4">
      <p className="text-sm text-white/70">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      <p className="mt-1 text-sm text-white/70">{note}</p>
    </div>
  );
}
