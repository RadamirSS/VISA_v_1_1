import type { CabinetSummary, NextAction, TimelineStep, TimelineStepState } from "./types";

const MONTHS_RU = [
  "января",
  "февраля",
  "марта",
  "апреля",
  "мая",
  "июня",
  "июля",
  "августа",
  "сентября",
  "октября",
  "ноября",
  "декабря"
];

export function resolveNextAction(summary: CabinetSummary): NextAction | null {
  return summary.case?.next_action ?? summary.next_action ?? null;
}

export function formatAppointmentDate(date?: string | null, time?: string | null): string {
  if (!date) {
    return "";
  }
  const [year, month, day] = date.split("-").map(Number);
  if (!year || !month || !day) {
    return time ? `${date}, ${time}` : date;
  }
  const formatted = `${day} ${MONTHS_RU[month - 1] ?? month} ${year}`;
  return time ? `${formatted}, ${time}` : formatted;
}

export function applicantStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "черновик",
    incomplete: "черновик",
    completed: "заполнено",
    needs_review: "на проверке",
    approved_by_manager: "проверено"
  };
  return labels[status] ?? "не начато";
}

export function pickTimelinePreview(steps: TimelineStep[], max = 5): TimelineStep[] {
  if (steps.length <= max) {
    return steps;
  }
  const anchor = steps.findIndex((step) => step.state === "current" || step.state === "warning");
  const index = anchor >= 0 ? anchor : 0;
  const start = Math.max(0, index - 2);
  return steps.slice(start, start + max);
}

export function timelineStateLabel(state: TimelineStepState): string {
  const labels: Record<TimelineStepState, string> = {
    done: "Выполнено",
    current: "Сейчас",
    locked: "Ожидает",
    warning: "Требует внимания"
  };
  return labels[state];
}

export function applicantsProgressPercent(completed: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Math.round((completed / total) * 100);
}
