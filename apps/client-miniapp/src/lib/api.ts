import type {
  ApplicantPayload,
  ApplicantProfile,
  CabinetSummary,
  CasePayload,
  CaseTimelineResponse,
  ConsulateOption,
  CountryOption,
  CreateCaseResponse,
  MeResponse,
  SlotOffer,
  SubmitCaseResponse,
  VisaCase
} from "./types";
import { getTelegramInitData } from "./telegram";

const API_BASE = process.env.NEXT_PUBLIC_MINIAPP_API_BASE_URL ?? "http://localhost:8100";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const initData = getTelegramInitData();
  if (initData) {
    headers.set("Authorization", `tma ${initData}`);
  } else if (process.env.NEXT_PUBLIC_MINIAPP_DEV_TELEGRAM_ID) {
    headers.set("X-Dev-Telegram-Id", process.env.NEXT_PUBLIC_MINIAPP_DEV_TELEGRAM_ID);
    headers.set("X-Dev-Username", process.env.NEXT_PUBLIC_MINIAPP_DEV_USERNAME ?? "localdev");
    headers.set("X-Dev-First-Name", process.env.NEXT_PUBLIC_MINIAPP_DEV_FIRST_NAME ?? "Локальный");
  }
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Ошибка API" }));
    const detail = payload.detail;
    if (typeof detail === "object" && detail?.message) {
      throw new Error(detail.message);
    }
    throw new Error(detail ?? "Ошибка API");
  }
  return response.json() as Promise<T>;
}

export const api = {
  validateTelegram: () => request<{ ok: boolean; telegram_id: number }>("/api/telegram/validate", { method: "POST" }),
  getMe: () => request<MeResponse>("/api/me"),
  getCabinetSummary: () => request<CabinetSummary>("/api/cabinet/summary"),
  getCaseTimeline: () => request<CaseTimelineResponse>("/api/case/current/timeline"),
  listCountries: () => request<CountryOption[]>("/api/config/countries"),
  listConsulates: (countryCode: string) => request<ConsulateOption[]>(`/api/config/consulates?countryCode=${encodeURIComponent(countryCode)}`),
  getCurrentCase: () => request<VisaCase>("/api/case/current"),
  createCase: () => request<CreateCaseResponse>("/api/case", { method: "POST" }),
  updateCase: (payload: CasePayload) =>
    request<VisaCase>("/api/case/current", {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  submitCase: () => request<SubmitCaseResponse>("/api/case/current/submit", { method: "POST" }),
  getSlotOffers: () => request<SlotOffer[]>("/api/case/current/slot-offers"),
  selectSlotOption: (optionId: string) => request<VisaCase>(`/api/case/current/slot-options/${optionId}/select`, { method: "POST" }),
  setApplicantsCount: (applicantsCount: number) =>
    request<VisaCase>("/api/case/applicants-count", {
      method: "POST",
      body: JSON.stringify({ applicants_count: applicantsCount })
    }),
  listApplicants: () => request<ApplicantProfile[]>("/api/applicants"),
  createApplicant: () => request<ApplicantProfile>("/api/applicants", { method: "POST" }),
  getApplicant: (id: string) => request<ApplicantProfile>(`/api/applicants/${id}`),
  updateApplicant: (id: string, payload: ApplicantPayload) =>
    request<ApplicantProfile>(`/api/applicants/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  copyFromPrimary: (id: string) =>
    request<ApplicantProfile>(`/api/applicants/${id}/copy-from-primary`, { method: "POST" })
};
