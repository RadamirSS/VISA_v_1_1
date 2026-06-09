export function ProgressBadge({ percent }: { percent: number }) {
  return (
    <div className="progress-badge">
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <span>{percent}%</span>
    </div>
  );
}
