export function LoadingState({ label = "Загрузка..." }: { label?: string }) {
  return (
    <div className="surface-card loading-state">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}
