"use client";

import { PortalShell } from "@/components/portal/portal-shell";
import { StatusTimeline } from "@/components/portal/status-timeline";
import { Card } from "@/components/ui/primitives";
import { useDemoStore } from "@/lib/demo-store";

export default function PortalStatusPage() {
  const { getCurrentApplication } = useDemoStore();
  const application = getCurrentApplication();

  if (!application) {
    return <PortalShell title="Статус" description="Нужна активная демо-сессия."><Card>Нет доступа.</Card></PortalShell>;
  }

  return (
    <PortalShell title="Статус заявки" description="Таймлайн показывает, какие этапы уже пройдены, а какие будут открыты после подключения внешних систем.">
      <StatusTimeline application={application} />
    </PortalShell>
  );
}
