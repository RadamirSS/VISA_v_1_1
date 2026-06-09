import Link from "next/link";

import type { CabinetDocumentsSummary } from "../../lib/types";

type DocumentsSummaryCardProps = {
  documents: CabinetDocumentsSummary;
  expanded?: boolean;
};

export function DocumentsSummaryCard({ documents, expanded = false }: DocumentsSummaryCardProps) {
  if (!documents.has_items) {
    if (!expanded) {
      return null;
    }
    return (
      <section className="surface-card dashboard-card">
        <p className="card-label">Документы</p>
        <h3>Документы</h3>
        <p className="muted-text">Менеджер запросит документы после проверки анкеты.</p>
        <Link className="secondary-button" href="/documents">
          Открыть документы
        </Link>
      </section>
    );
  }

  const readyCount = documents.agency_ready + documents.agency_shared;

  return (
    <section className="surface-card dashboard-card">
      <p className="card-label">Документы</p>
      <h3>Документы</h3>
      {documents.client_pending > 0 ? (
        <p className="muted-text">От вас: {documents.client_pending} ожидают загрузки</p>
      ) : null}
      {documents.client_uploaded > 0 ? (
        <p className="muted-text">От вас: {documents.client_uploaded} на проверке</p>
      ) : null}
      {documents.agency_in_progress > 0 ? (
        <p className="muted-text">Агентство: {documents.agency_in_progress} документ готовится</p>
      ) : null}
      {readyCount > 0 ? <p className="muted-text">Готово: {readyCount}</p> : null}
      {expanded ? (
        <>
          <p className="muted-text">
            Ожидаем от вас: {documents.client_pending} · Готовит агентство: {documents.agency_in_progress} · Готово:{" "}
            {readyCount}
          </p>
        </>
      ) : null}
      <Link className="secondary-button" href="/documents">
        Открыть документы
      </Link>
    </section>
  );
}
