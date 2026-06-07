"use client";

import { useState } from "react";
import { PortalShell } from "@/components/portal/portal-shell";
import { Card } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";

export default function PortalProfilePage() {
  const { getCurrentApplication, updateProfile } = useDemoStore();
  const application = getCurrentApplication();
  const [message, setMessage] = useState("");

  if (!application) {
    return <PortalShell title="Профиль" description="Нужна активная демо-сессия."><Card>Нет доступа.</Card></PortalShell>;
  }

  return (
    <PortalShell title="Профиль заявителя" description="Контакты и страна проживания выделены отдельно, чтобы менеджеру было проще проверить базовые данные до анкеты.">
      <Card className="grid gap-4 md:grid-cols-2">
        <Field id="phone" label="Телефон" defaultValue={application.profile.phone} />
        <Field id="residenceCountry" label="Текущая страна проживания" defaultValue={application.profile.residenceCountry} />
        <Field id="address" label="Домашний адрес" defaultValue={application.profile.address} />
        <Field id="residencePermit" label="ВНЖ / разрешение" defaultValue={application.profile.residencePermit} />
        <Field id="emergencyContact" label="Контакт для связи" defaultValue={application.profile.emergencyContact} />
        <div className="md:col-span-2 flex flex-wrap items-center gap-3">
          <button
            onClick={() => {
              const profile = {
                password: application.profile.password,
                phone: (document.getElementById("phone") as HTMLInputElement).value,
                residenceCountry: (document.getElementById("residenceCountry") as HTMLInputElement).value,
                address: (document.getElementById("address") as HTMLInputElement).value,
                residencePermit: (document.getElementById("residencePermit") as HTMLInputElement).value,
                emergencyContact: (document.getElementById("emergencyContact") as HTMLInputElement).value
              };
              updateProfile(profile);
              setMessage("Профиль сохранен.");
            }}
            className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white"
          >
            Сохранить профиль
          </button>
          {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
        </div>
      </Card>
    </PortalShell>
  );
}

function Field({ id, label, defaultValue }: { id: string; label: string; defaultValue: string }) {
  return (
    <label>
      <span className="mb-2 block text-sm font-medium text-[var(--ink)]">{label}</span>
      <input id={id} defaultValue={defaultValue} className="w-full rounded-3xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3" />
    </label>
  );
}
