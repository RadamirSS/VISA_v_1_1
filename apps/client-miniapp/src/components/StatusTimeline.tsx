import type { TimelineStep } from "../lib/types";
import { timelineStateLabel } from "../lib/cabinet";

type StatusTimelineProps = {
  steps: TimelineStep[];
  compact?: boolean;
  title?: string;
  className?: string;
};

export function StatusTimeline({ steps, compact = false, title = "Статус заявки", className = "" }: StatusTimelineProps) {
  if (!steps.length) {
    return null;
  }

  return (
    <section className={`surface-card ${compact ? "timeline-compact" : ""} ${className}`.trim()}>
      {title ? <p className="card-label">{title}</p> : null}
      <div className="timeline">
        {steps.map((step) => (
          <div key={step.key} className={`timeline-item ${step.state}`}>
            <span className="timeline-dot" />
            <div>
              <strong>{step.label}</strong>
              <p className="muted-text">{timelineStateLabel(step.state)}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
