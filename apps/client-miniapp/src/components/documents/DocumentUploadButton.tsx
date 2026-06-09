"use client";

import { useRef, useState } from "react";

import { api } from "../../lib/api";
import type { DocumentItem } from "../../lib/types";

type DocumentUploadButtonProps = {
  document: DocumentItem;
  onUploaded: (document: DocumentItem) => void;
};

export function DocumentUploadButton({ document, onUploaded }: DocumentUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedName, setSelectedName] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!document.uploads_enabled) {
    return (
      <p className="muted-text">Загрузка файлов будет доступна позже. Свяжитесь с менеджером.</p>
    );
  }

  if (!document.can_upload) {
    return null;
  }

  async function handleUpload(file: File) {
    setLoading(true);
    setError("");
    try {
      const result = await api.uploadDocument(document.id, file);
      onUploaded({
        ...document,
        status: result.status,
        status_label: result.status_label,
        has_file: result.has_file,
        can_upload: false
      });
      setSelectedName("");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Не удалось загрузить файл.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-stack">
      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            setSelectedName(file.name);
            void handleUpload(file);
          }
        }}
      />
      {selectedName ? <p className="muted-text">Выбран файл: {selectedName}</p> : null}
      {error ? <p className="status-banner">{error}</p> : null}
      <button
        className="secondary-button"
        type="button"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? "Загрузка..." : "Загрузить файл"}
      </button>
    </div>
  );
}
