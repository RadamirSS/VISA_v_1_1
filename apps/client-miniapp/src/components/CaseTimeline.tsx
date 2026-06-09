import type { VisaCase } from "../lib/types";

const orderedSteps = [
  { key: "profiles", label: "Анкеты заполнены" },
  { key: "submitted", label: "Заявка отправлена менеджеру" },
  { key: "reviewing", label: "Менеджер проверяет данные" },
  { key: "search", label: "Менеджер подбирает даты" },
  { key: "offered", label: "Даты отправлены" },
  { key: "selected", label: "Дата выбрана клиентом" },
  { key: "confirming", label: "Запись подтверждается" },
  { key: "confirmed", label: "Запись подтверждена" }
] as const;

function resolveState(visaCase: VisaCase | null, index: number): "done" | "current" | "locked" {
  if (!visaCase) {
    return index === 0 ? "current" : "locked";
  }
  const status = visaCase.status;
  const progressMap = {
    profiles_in_progress: 0,
    profiles_not_started: 0,
    profiles_completed: 0,
    draft: 0,
    city_selection_in_progress: 0,
    needs_clarification: 1,
    submitted_for_manager_review: 1,
    needs_manager_consultation: 1,
    manager_reviewing: 2,
    ready_for_slot_search: 3,
    slot_options_sent: 4,
    slot_selected_by_client: 5,
    appointment_confirmation_pending: 6,
    appointment_confirmed: 7,
    closed: 7
  } as const;
  const current = progressMap[status as keyof typeof progressMap] ?? 0;
  if (index < current) {
    return "done";
  }
  if (index === current) {
    return "current";
  }
  return "locked";
}

export function CaseTimeline({ visaCase }: { visaCase: VisaCase | null }) {
  return (
    <section className="surface-card">
      <p className="card-label">Статус заявки</p>
      <div className="timeline">
        {orderedSteps.map((step, index) => {
          const state = resolveState(visaCase, index);
          return (
            <div key={step.key} className={`timeline-item ${state}`}>
              <span className="timeline-dot" />
              <div>
                <strong>{step.label}</strong>
                <p className="muted-text">
                  {state === "done" ? "Выполнено" : state === "current" ? "Текущий этап" : "Ожидает"}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
