"use client";

import { ReactNode, useMemo, useState } from "react";
import { Card } from "@/components/ui/primitives";

type BotState = {
  country: string;
  city: string;
  visaType: string;
  applicationId: string;
  slot: string;
};

const countries = ["Италия", "Франция", "Испания"];
const citiesByCountry: Record<string, string[]> = {
  "Италия": ["Белград", "Москва", "Стамбул"],
  "Франция": ["Белград", "Ереван"],
  "Испания": ["Белград", "Тбилиси"]
};

const visaTypes = ["Туризм", "Бизнес", "Посещение семьи"];
type ButtonTuple = [string, () => void];

export function BotSimulator() {
  const [screen, setScreen] = useState("menu");
  const [state, setState] = useState<BotState>({
    country: "",
    city: "",
    visaType: "",
    applicationId: "",
    slot: ""
  });
  const [message, setMessage] = useState("");

  const slots = useMemo(
    () => (state.country === "Испания" ? [] : ["14 июля, 10:15", "18 июля, 12:40", "25 июля, 09:30"]),
    [state.country]
  );

  const reset = () => {
    setScreen("menu");
    setState({ country: "", city: "", visaType: "", applicationId: "", slot: "" });
    setMessage("");
  };

  const action = (nextScreen: string, nextState?: Partial<BotState>, nextMessage?: string) => {
    setState((current) => ({ ...current, ...nextState }));
    setScreen(nextScreen);
    setMessage(nextMessage ?? "");
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
      <Card className="overflow-hidden p-0">
        <div className="bg-[#4c6c91] px-5 py-4 text-white">
          <p className="font-medium">Visa Atelier Bot</p>
          <p className="text-sm text-white/75">Демо Telegram-поток для записи в визовый центр</p>
        </div>
        <div className="space-y-4 bg-[#e9f0f8] p-5">
          <Bubble from="bot">
            Добро пожаловать! Я помогу проверить готовность заявки, показать список документов и провести по демо-потоку записи.
          </Bubble>

          {screen === "menu" ? (
            <ButtonGroup
              buttons={[
                ["Проверить заявку", () => action("application", {}, "Введите или выберите ID заявки.")],
                ["Записаться в консульство", () => action("country")],
                ["Список документов", () => action("docs", {}, "Базовый список документов уже доступен в портале.")],
                ["Связаться с менеджером", () => action("manager", {}, "Менеджер ответит в рабочее время. Канал связи пока демо.")],
              ]}
            />
          ) : null}

          {screen === "docs" ? (
            <>
              <Bubble from="bot">Для старта обычно нужны паспорт, фото, страховка, брони и финансовые документы. Полный чек-лист доступен в кабинете.</Bubble>
              <ButtonGroup buttons={[["Главное меню", reset]]} />
            </>
          ) : null}

          {screen === "manager" ? (
            <>
              <Bubble from="bot">Напишите менеджеру в Telegram: @visa_atelier_demo. Это демонстрационный контакт без реальной поддержки.</Bubble>
              <ButtonGroup buttons={[["Главное меню", reset]]} />
            </>
          ) : null}

          {screen === "application" ? (
            <>
              <Bubble from="bot">{message}</Bubble>
              <ButtonGroup
                buttons={[
                  ["app-demo-1", () => action("ready", { applicationId: "app-demo-1" }, "Заявка найдена. Комплект пока не завершен на 100%.")],
                  ["Назад", reset]
                ]}
              />
            </>
          ) : null}

          {screen === "ready" ? (
            <>
              <Bubble from="bot">{message}</Bubble>
              <ButtonGroup
                buttons={[
                  ["Продолжить запись", () => action("country")],
                  ["Главное меню", reset]
                ]}
              />
            </>
          ) : null}

          {screen === "country" ? (
            <>
              <Bubble from="bot">Шаг 1. Выберите страну подачи.</Bubble>
              <ButtonGroup buttons={countries.map((country): ButtonTuple => [country, () => action("city", { country })]).concat([["Отмена", reset] as ButtonTuple])} />
            </>
          ) : null}

          {screen === "city" ? (
            <>
              <Bubble from="bot">Шаг 2. Выберите город / визовый центр.</Bubble>
              <ButtonGroup buttons={(citiesByCountry[state.country] ?? []).map((city): ButtonTuple => [city, () => action("type", { city })]).concat([["Назад", () => action("country")] as ButtonTuple])} />
            </>
          ) : null}

          {screen === "type" ? (
            <>
              <Bubble from="bot">Шаг 3. Выберите тип визы.</Bubble>
              <ButtonGroup buttons={visaTypes.map((visaType): ButtonTuple => [visaType, () => action("appId", { visaType })]).concat([["Назад", () => action("city")] as ButtonTuple])} />
            </>
          ) : null}

          {screen === "appId" ? (
            <>
              <Bubble from="bot">Шаг 4. Подтвердите ID заявки.</Bubble>
              <ButtonGroup
                buttons={[
                  ["app-demo-1", () => action("check", { applicationId: "app-demo-1" }, "Проверяю готовность комплекта...")],
                  ["Назад", () => action("type")]
                ]}
              />
            </>
          ) : null}

          {screen === "check" ? (
            <>
              <Bubble from="bot">{message}</Bubble>
              <Bubble from="bot">Шаг 5. Документы готовы для демо-поиска слота.</Bubble>
              <ButtonGroup
                buttons={[
                  ["Искать слот", () => action("slots")],
                  ["Отмена", reset]
                ]}
              />
            </>
          ) : null}

          {screen === "slots" ? (
            <>
              <Bubble from="bot">Шаг 6. Ищу свободные слоты...</Bubble>
              {slots.length === 0 ? (
                <>
                  <Bubble from="bot">Свободных слотов сейчас нет. Попробуйте позже или свяжитесь с менеджером.</Bubble>
                  <ButtonGroup buttons={[["Главное меню", reset], ["Назад", () => action("country")]]} />
                </>
              ) : (
                <ButtonGroup buttons={slots.map((slot): ButtonTuple => [slot, () => action("confirm", { slot })]).concat([["Назад", () => action("check")] as ButtonTuple])} />
              )}
            </>
          ) : null}

          {screen === "confirm" ? (
            <>
              <Bubble from="bot">
                Шаг 7. Проверьте данные: {state.country}, {state.city}, {state.visaType}, слот {state.slot}, ID {state.applicationId}.
              </Bubble>
              <ButtonGroup
                buttons={[
                  ["Подтвердить", () => action("final")],
                  ["Назад", () => action("slots")]
                ]}
              />
            </>
          ) : null}

          {screen === "final" ? (
            <>
              <Bubble from="bot">Шаг 8. Финальный экран. Реальные интеграции пока не подключены.</Bubble>
              <ButtonGroup
                buttons={[
                  ["Book appointment", () => setMessage("Booking API is not connected yet")],
                  ["Pay", () => setMessage("Payment provider is not connected yet")],
                  ["Главное меню", reset]
                ]}
              />
              {message ? <Bubble from="bot">{message}</Bubble> : null}
            </>
          ) : null}
        </div>
      </Card>

      <Card className="space-y-4">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--accent)]">Что покрыто</p>
        <h3 className="font-display text-2xl text-[var(--ink)]">Логика демо-бота</h3>
        <ul className="space-y-3 text-sm text-[var(--muted)]">
          <li>/start, главное меню, back, cancel</li>
          <li>Проверка заявки и готовности документов</li>
          <li>Выбор страны, города, типа визы и слота</li>
          <li>Пустое состояние слотов для части направлений</li>
          <li>Финальные кнопки только возвращают placeholder-сообщения</li>
        </ul>
      </Card>
    </div>
  );
}

function Bubble({ from, children }: { from: "bot" | "user"; children: ReactNode }) {
  return (
    <div className={from === "bot" ? "mr-10 rounded-3xl rounded-tl-md bg-white p-4 text-sm text-[var(--ink)] shadow-sm" : "ml-10 rounded-3xl rounded-tr-md bg-[#d6f5c9] p-4 text-sm text-[var(--ink)]"}>
      {children}
    </div>
  );
}

function ButtonGroup({ buttons }: { buttons: ButtonTuple[] }) {
  return (
    <div className="grid gap-2">
      {buttons.map(([label, onClick]) => (
        <button key={label} onClick={onClick} className="rounded-2xl bg-white px-4 py-3 text-left text-sm font-medium text-[var(--ink)] shadow-sm transition hover:bg-slate-50">
          {label}
        </button>
      ))}
    </div>
  );
}
