import { applicantsProgressPercent } from "../lib/cabinet";

export function ProgressBar({ completed, total, label }: { completed: number; total: number; label?: string }) {
  const percent = applicantsProgressPercent(completed, total);

  return (
    <div className="progress-bar-block">
      {label ? <p className="muted-text">{label}</p> : null}
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <p className="progress-bar-value">{percent}%</p>
    </div>
  );
}
