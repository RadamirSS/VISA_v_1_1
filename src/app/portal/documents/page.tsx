"use client";

import { useState } from "react";
import { PortalShell } from "@/components/portal/portal-shell";
import { Card, ProgressBar } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";
import { formatDate } from "@/lib/utils";

export default function PortalDocumentsPage() {
  const { getCurrentApplication, updateDocumentMetadata, updateDocumentStatus, getProgress } = useDemoStore();
  const application = getCurrentApplication();
  const [message, setMessage] = useState("");

  if (!application) {
    return <PortalShell title="Документы" description="Нужна активная демо-сессия."><Card>Нет доступа.</Card></PortalShell>;
  }

  const progress = getProgress(application);

  return (
    <PortalShell title="Чек-лист документов" description="В демо мы сохраняем только метаданные файлов. Безопасное хранилище и реальная загрузка должны быть подключены позже.">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-display text-2xl text-[var(--ink)]">Прогресс по документам</p>
            <p className="text-sm text-[var(--muted)]">Отслеживается наличие обязательных позиций и комментарии по качеству.</p>
          </div>
          <div className="rounded-full bg-[var(--surface)] px-4 py-2 text-sm text-[var(--ink)]">Отсутствует обязательных: {progress.missingDocuments}</div>
        </div>
        <ProgressBar value={progress.documentsCompletion} />
      </Card>

      <div className="grid gap-4">
        {application.documents.map((item) => (
          <Card key={item.id} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium text-[var(--ink)]">{item.title}</p>
                  <span className={`rounded-full px-3 py-1 text-xs ${item.required ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`}>
                    {item.required ? "Required" : "Optional"}
                  </span>
                  <span className="rounded-full bg-[var(--surface)] px-3 py-1 text-xs text-[var(--ink)]">{item.status}</span>
                </div>
                <p className="mt-2 text-sm text-[var(--muted)]">{item.guidance}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => updateDocumentStatus(item.id, "accepted")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                  Accepted
                </button>
                <button onClick={() => updateDocumentStatus(item.id, "needs_correction")} className="rounded-full border border-amber-200 px-4 py-2 text-sm text-amber-800">
                  Needs correction
                </button>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-4">
              <input id={`${item.id}-name`} placeholder="Имя файла" defaultValue={item.fileName ?? ""} className="rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
              <input id={`${item.id}-type`} placeholder="Тип файла" defaultValue={item.fileType ?? ""} className="rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
              <input id={`${item.id}-size`} placeholder="Размер (KB)" defaultValue={item.fileSizeKb ?? ""} className="rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
              <input id={`${item.id}-comment`} placeholder="Комментарий клиента" defaultValue={item.clientComment} className="rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => {
                  updateDocumentMetadata(item.id, {
                    fileName: (window.document.getElementById(`${item.id}-name`) as HTMLInputElement).value,
                    fileType: (window.document.getElementById(`${item.id}-type`) as HTMLInputElement).value,
                    fileSizeKb: Number((window.document.getElementById(`${item.id}-size`) as HTMLInputElement).value || "0"),
                    clientComment: (window.document.getElementById(`${item.id}-comment`) as HTMLInputElement).value
                  });
                  setMessage(`Метаданные для "${item.title}" сохранены.`);
                }}
                className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white"
              >
                Сохранить метаданные
              </button>
              <div className="rounded-full bg-[var(--surface)] px-4 py-2 text-sm text-[var(--muted)]">
                Комментарий менеджера: {item.managerComment || "появится после подключения backend review"}
              </div>
              {item.uploadedAt ? <p className="text-sm text-[var(--muted)]">Последнее обновление: {formatDate(item.uploadedAt)}</p> : null}
            </div>
          </Card>
        ))}
      </div>
      {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
    </PortalShell>
  );
}
