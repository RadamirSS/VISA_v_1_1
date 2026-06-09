"use client";

import { useState } from "react";

import { api } from "../../lib/api";
import type { DocumentItem } from "../../lib/types";
import { DocumentUploadButton } from "./DocumentUploadButton";

type DocumentCardProps = {
  document: DocumentItem;
  onUpdate: (document: DocumentItem) => void;
};

export function DocumentCard({ document, onUpdate }: DocumentCardProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const isInsurance = document.category === "insurance_own";

  async function handleNoInsurance() {
    setLoading(true);
    setError("");
    try {
      const updated = await api.commentDocument(document.id, "У меня нет своей страховки.", true);
      onUpdate(updated);
    } catch (commentError) {
      setError(commentError instanceof Error ? commentError.message : "Не удалось отправить сообщение.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    setLoading(true);
    setError("");
    try {
      const blob = await api.downloadDocument(document.id);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = document.title;
      link.click();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : "Не удалось скачать документ.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="surface-card dashboard-card">
      <div className="card-row">
        <div>
          <p className="card-label">{document.source_type === "client_required" ? "Нужно от вас" : "Готовит агентство"}</p>
          <h3>{document.title}</h3>
        </div>
        <span className="status-chip active">{document.status_label}</span>
      </div>
      {document.description ? <p className="muted-text">{document.description}</p> : null}
      {document.manager_comment ? (
        <p className="muted-text">Комментарий менеджера: {document.manager_comment}</p>
      ) : null}
      {document.client_comment ? <p className="muted-text">Ваш комментарий: {document.client_comment}</p> : null}
      {error ? <p className="status-banner">{error}</p> : null}
      {document.source_type === "client_required" ? (
        <>
          <DocumentUploadButton document={document} onUploaded={onUpdate} />
          {isInsurance && document.can_upload ? (
            <button className="ghost-button" type="button" disabled={loading} onClick={() => void handleNoInsurance()}>
              Сообщить, что страховки нет
            </button>
          ) : null}
        </>
      ) : (
        <>
          {document.can_download ? (
            <button className="secondary-button" type="button" disabled={loading} onClick={() => void handleDownload()}>
              {loading ? "Открываем..." : "Скачать / открыть"}
            </button>
          ) : (
            <p className="muted-text">
              {document.has_file ? "Документ будет доступен после передачи менеджером." : "Документ будет добавлен позже."}
            </p>
          )}
        </>
      )}
    </section>
  );
}
