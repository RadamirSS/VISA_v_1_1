"use client";

import { useEffect, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { DocumentCard } from "../../components/documents/DocumentCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { api } from "../../lib/api";
import type { DocumentItem } from "../../lib/types";

export default function DocumentsPage() {
  const [items, setItems] = useState<DocumentItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const response = await api.getDocuments();
        setItems(response.items);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить документы.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const clientItems = items.filter((item) => item.source_type === "client_required");
  const agencyItems = items.filter((item) => item.source_type === "agency_prepared");

  function updateItem(updated: DocumentItem) {
    setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  }

  return (
    <AppShell title="Документы" subtitle="Здесь вы видите, что нужно загрузить, и что готовит агентство.">
      {loading ? <LoadingState label="Загружаем документы..." /> : null}
      {error ? <section className="surface-card status-banner">{error}</section> : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Документы пока не запрошены"
          description="Менеджер запросит документы после проверки анкеты. Когда список появится, вы увидите его здесь."
          ctaHref="/"
          ctaLabel="На главную"
        />
      ) : null}
      {!loading && !error && items.length > 0 ? (
        <div className="grid-stack">
          <section className="surface-card">
            <h3>Нужно от вас</h3>
            {clientItems.length === 0 ? (
              <p className="muted-text">Сейчас от вас ничего не требуется.</p>
            ) : (
              <div className="grid-stack">
                {clientItems.map((item) => (
                  <DocumentCard key={item.id} document={item} onUpdate={updateItem} />
                ))}
              </div>
            )}
          </section>
          <section className="surface-card">
            <h3>Готовит агентство</h3>
            {agencyItems.length === 0 ? (
              <p className="muted-text">Документы от агентства появятся здесь по мере готовности.</p>
            ) : (
              <div className="grid-stack">
                {agencyItems.map((item) => (
                  <DocumentCard key={item.id} document={item} onUpdate={updateItem} />
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
