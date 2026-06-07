import { ReactNode } from "react";

export function Section({
  title,
  eyebrow,
  description,
  children
}: {
  title: string;
  eyebrow?: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="max-w-2xl">
        {eyebrow ? <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent)]">{eyebrow}</p> : null}
        <h2 className="mt-3 font-display text-3xl text-[var(--ink)] sm:text-4xl">{title}</h2>
        {description ? <p className="mt-4 text-base text-[var(--muted)]">{description}</p> : null}
      </div>
      <div className="mt-8">{children}</div>
    </section>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-[28px] border border-[var(--line)] bg-white p-6 shadow-soft ${className}`}>{children}</div>;
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 rounded-full bg-[var(--line)]">
      <div className="h-2 rounded-full bg-[var(--accent)] transition-all" style={{ width: `${value}%` }} />
    </div>
  );
}
