import Link from "next/link";

export function EmptyState({ title, description, ctaHref, ctaLabel }: { title: string; description: string; ctaHref?: string; ctaLabel?: string }) {
  return (
    <section className="surface-card empty-state">
      <h3>{title}</h3>
      <p className="muted-text">{description}</p>
      {ctaHref && ctaLabel ? (
        <Link className="primary-button" href={ctaHref}>
          {ctaLabel}
        </Link>
      ) : null}
    </section>
  );
}
