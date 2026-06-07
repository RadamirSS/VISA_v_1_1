import { promises as fs } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
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

type NotificationStatus = "pending" | "sent" | "failed" | "skipped_env_missing";

type LeadRecord = {
  id: string;
  createdAt: string;
  payload: LeadPayload;
  notificationStatus: NotificationStatus;
};

const required = (value?: string) => Boolean(value && value.trim().length > 0);

const storageDirectory = path.join(process.cwd(), "storage");
const storageFile = path.join(storageDirectory, "leads.jsonl");

const buildText = (record: LeadRecord) => {
  const { payload } = record;
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
    `ID: ${record.id}`,
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
    `Комментарий:\n${payload.comment || "Нет"}`,
    `Источник: ${process.env.NEXT_PUBLIC_SITE_URL || "site_url_not_set"}`
  ].join("\n");
};

async function appendLeadRecord(record: LeadRecord) {
  await fs.mkdir(storageDirectory, { recursive: true });
  await fs.appendFile(storageFile, `${JSON.stringify(record)}\n`, "utf8");
}

async function notifyManager(message: string): Promise<NotificationStatus> {
  const token = process.env.LEADS_TELEGRAM_BOT_TOKEN;
  const chatId = process.env.LEADS_TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    console.warn("Lead notification skipped: Telegram env vars are missing.");
    return "skipped_env_missing";
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
    return "failed";
  }

  return "sent";
}

function validateAdditionalApplicants(payload: LeadPayload) {
  const expectedAdditionalCount = Math.max(payload.applicantsCount - 1, 0);

  if (payload.additionalApplicants.length !== expectedAdditionalCount) {
    return false;
  }

  return payload.additionalApplicants.every((applicant) => required(applicant.fullName) && required(applicant.birthDateOrYear));
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

  if (!Number.isInteger(payload.applicantsCount) || payload.applicantsCount < 1 || payload.applicantsCount > 5) {
    return NextResponse.json({ ok: false, error: "Количество заявителей должно быть от 1 до 5." }, { status: 400 });
  }

  if (!validateAdditionalApplicants(payload)) {
    return NextResponse.json({ ok: false, error: "Проверьте данные по дополнительным заявителям." }, { status: 400 });
  }

  const leadId = `lead_${randomUUID().replace(/-/g, "").slice(0, 12)}`;
  const createdAt = new Date().toISOString();

  try {
    const pendingRecord: LeadRecord = {
      id: leadId,
      createdAt,
      payload,
      notificationStatus: "pending"
    };

    await appendLeadRecord(pendingRecord);

    let notificationStatus: NotificationStatus;

    try {
      notificationStatus = await notifyManager(buildText(pendingRecord));
    } catch (error) {
      console.warn("Lead notification threw an error", error);
      notificationStatus = "failed";
    }

    await appendLeadRecord({
      ...pendingRecord,
      notificationStatus
    });
  } catch (error) {
    console.error("Lead save failed", error);
    return NextResponse.json({ ok: false, error: "Не удалось сохранить заявку. Попробуйте еще раз." }, { status: 500 });
  }

  return NextResponse.json({ ok: true, message: "Заявка принята", id: leadId });
}
