import Link from "next/link";
import countries from "@config/countries.ru.json";
import { Card, Section } from "@/components/ui/primitives";

const servicePoints = [
  "Первичная оценка кейса и подбор маршрута подачи",
  "Подсказки по структуре пакета документов",
  "Сопровождение по организационным вопросам записи",
  "Передача кейса менеджеру для дальнейшей работы"
];

const processPoints = [
  "Вы оставляете короткую заявку на сайте",
  "Менеджер связывается с вами и уточняет детали поездки",
  "Мы помогаем определить страну подачи и подготовительный план",
  "Дальнейшая работа по записи и сопровождению идет через менеджера и Telegram-бот"
];

export default function HomePage() {
  return (
    <>
      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-20">
        <div className="space-y-7">
          <div className="inline-flex rounded-full border border-[var(--line)] bg-white px-4 py-2 text-xs uppercase tracking-[0.24em] text-[var(--accent)] shadow-soft">
            Schengen visa assistance
          </div>
          <div>
            <h1 className="max-w-4xl font-display text-5xl leading-tight text-[var(--ink)] sm:text-6xl">
              Спокойный и понятный старт для подготовки к подаче на шенгенскую визу
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-[var(--muted)]">
              Сайт помогает быстро оставить заявку и получить первичную консультацию. Для записи, оплаты и рабочих статусов используется отдельный Telegram-бот и менеджерское сопровождение.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/apply" className="rounded-full bg-[var(--accent)] px-6 py-3.5 text-sm font-medium text-white">
              Оставить заявку
            </Link>
            <Link href="/schengen" className="rounded-full border border-[var(--line)] px-6 py-3.5 text-sm font-medium text-[var(--ink)]">
              Как мы работаем
            </Link>
          </div>
          <p className="text-sm text-[var(--muted)]">
            Мы не гарантируем одобрение визы и не гарантируем доступность записи. Финальные решения принимают консульства и уполномоченные визовые органы.
          </p>
        </div>

        <Card className="relative overflow-hidden bg-[linear-gradient(180deg,#1f4850_0%,#14363b_100%)] text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.18),transparent_35%)]" />
          <div className="relative space-y-6">
            <div className="rounded-[24px] bg-white/10 p-5 backdrop-blur">
              <p className="text-sm uppercase tracking-[0.24em] text-white/70">Формат работы</p>
              <p className="mt-3 text-3xl font-semibold">Сайт для первичной заявки, бот для запроса записи</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Metric title="Сайт" value="Lead-first" note="короткая заявка без паспортных данных" />
              <Metric title="Бот" value="Workflow" note="запрос записи, промокоды, статусы" />
              <Metric title="Подход" value="Manual review" note="менеджер проверяет кейс и детали" />
              <Metric title="Юридически аккуратно" value="Safe wording" note="без обещаний по визе и слотам" />
            </div>
          </div>
        </Card>
      </section>

      <Section eyebrow="О сервисе" title="Сайт больше не притворяется личным кабинетом" description="Мы упростили интерфейс до маркетингового сайта и короткой заявки, чтобы не собирать лишние данные до первичной консультации.">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h3 className="font-display text-2xl text-[var(--ink)]">Что делает сайт</h3>
            <ul className="mt-5 space-y-3 text-[var(--muted)]">
              {servicePoints.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
          <Card>
            <h3 className="font-display text-2xl text-[var(--ink)]">Как выглядит путь клиента</h3>
            <ol className="mt-5 space-y-4 text-[var(--muted)]">
              {processPoints.map((item, index) => (
                <li key={item} className="flex gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface)] text-sm font-semibold text-[var(--accent)]">{index + 1}</span>
                  <span>{item}</span>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      </Section>

      <Section eyebrow="Страны" title="Основные направления подачи" description="Подробные страницы по странам помогают понять, какой маршрут подачи может подойти вашему кейсу.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {countries.map((country) => (
            <Card key={country.code}>
              <p className="font-display text-2xl text-[var(--ink)]">{country.nameRu}</p>
              <p className="mt-3 text-sm text-[var(--muted)]">{country.suitsForRu}</p>
              <Link href={`/countries/${country.slug}`} className="mt-5 inline-flex text-sm font-medium text-[var(--accent)]">
                Подробнее о направлении
              </Link>
            </Card>
          ))}
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
