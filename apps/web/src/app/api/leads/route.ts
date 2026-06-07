import { NextResponse } from "next/server";

type LeadPayload = {
  mainApplicant: {
    lastName: string;
    firstName: string;
    patronymic?: string;
    birthDateOrYear: string;
    citizenship: string;
    currentLocation?: string;
  };
  desiredCountry?: string;
  travelPurpose?: string;
  approximateTravelMonth?: string;
  applicantsCount: number;
  additionalApplicants: Array<{
    fullName: string;
    birthDateOrYear: string;
    relationship?: string;
  }>;
  contact: {
    telegram?: string;
    phone?: string;
    email?: string;
  };
  comment?: string;
  consent: boolean;
  source: "website";
};

const required = (value?: string) => Boolean(value && value.trim().length > 0);

const buildText = (payload: LeadPayload) => {
  const fullName = [payload.mainApplicant.lastName, payload.mainApplicant.firstName, payload.mainApplicant.patronymic].filter(Boolean).join(" ");
  const contacts = [
    payload.contact.telegram ? `Telegram: ${payload.contact.telegram}` : "",
    payload.contact.phone ? `Phone: ${payload.contact.phone}` : "",
    payload.contact.email ? `Email: ${payload.contact.email}` : ""
  ].filter(Boolean);
  const additionalApplicants =
    payload.additionalApplicants.length > 0
      ? payload.additionalApplicants
          .map((item, index) => `${index + 1}. ${item.fullName}, ${item.birthDateOrYear}${item.relationship ? `, ${item.relationship}` : ""}`)
          .join("\n")
      : "Нет";

  return [
    "Новая заявка с сайта",
    `ФИО: ${fullName}`,
    `Дата/год рождения: ${payload.mainApplicant.birthDateOrYear}`,
    `Гражданство: ${payload.mainApplicant.citizenship}`,
    `Локация: ${payload.mainApplicant.currentLocation || "Не указана"}`,
    `Страна Шенгена: ${payload.desiredCountry || "Нужна консультация"}`,
    `Цель: ${payload.travelPurpose || "Нужна консультация"}`,
    `Месяц поездки: ${payload.approximateTravelMonth || "Не указан"}`,
    `Количество заявителей: ${payload.applicantsCount}`,
    `Доп. заявители:\n${additionalApplicants}`,
    `Контакт:\n${contacts.join("\n") || "Не указан"}`,
    `Комментарий:\n${payload.comment || "Нет"}`
  ].join("\n");
};

async function notifyManager(message: string) {
  const token = process.env.LEADS_TELEGRAM_BOT_TOKEN;
  const chatId = process.env.LEADS_TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    console.warn("Lead notification skipped: Telegram env vars are missing.");
    return;
  }

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: message
    }),
    cache: "no-store"
  });

  if (!response.ok) {
    console.warn("Lead notification failed with status", response.status);
  }
}

export async function POST(request: Request) {
  const payload = (await request.json()) as LeadPayload;

  if (
    !required(payload.mainApplicant.lastName) ||
    !required(payload.mainApplicant.firstName) ||
    !required(payload.mainApplicant.birthDateOrYear) ||
    !required(payload.mainApplicant.citizenship) ||
    !payload.applicantsCount ||
    !payload.consent
  ) {
    return NextResponse.json({ ok: false, error: "Пожалуйста, заполните обязательные поля." }, { status: 400 });
  }

  if (!required(payload.contact.telegram) && !required(payload.contact.phone) && !required(payload.contact.email)) {
    return NextResponse.json({ ok: false, error: "Укажите хотя бы один способ связи." }, { status: 400 });
  }

  try {
    await notifyManager(buildText(payload));
  } catch (error) {
    console.warn("Lead notification threw an error", error);
  }

  return NextResponse.json({ ok: true, message: "Заявка принята" });
}
