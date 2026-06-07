import { timelineSteps } from "@/lib/mock-data";
import { ApplicationRecord } from "@/lib/types";

export function StatusTimeline({ application }: { application: ApplicationRecord }) {
  return (
    <div className="space-y-4">
      {timelineSteps.map((step, index) => {
        const complete = application.timelineCompletedKeys.includes(step.key);
        const blocked = step.key === "appointment_booking" || step.key === "payment" || step.key === "appointment_confirmed";
        return (
          <div key={step.key} className="flex gap-4 rounded-[26px] border border-[var(--line)] bg-white p-5 shadow-soft">
            <div className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${complete ? "bg-[var(--accent)] text-white" : "bg-[var(--surface)] text-[var(--muted)]"}`}>
              {index + 1}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-[var(--ink)]">{step.title}</p>
                {blocked ? <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">Placeholder</span> : null}
              </div>
              <p className="mt-2 text-sm text-[var(--muted)]">{step.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
