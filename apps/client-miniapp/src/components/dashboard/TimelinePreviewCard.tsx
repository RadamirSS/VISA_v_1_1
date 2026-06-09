import Link from "next/link";

import { pickTimelinePreview } from "../../lib/cabinet";
import type { TimelineStep } from "../../lib/types";
import { StatusTimeline } from "../StatusTimeline";

export function TimelinePreviewCard({ steps }: { steps: TimelineStep[] }) {
  if (!steps.length) {
    return null;
  }

  const preview = pickTimelinePreview(steps);

  return (
    <div className="grid-stack">
      <StatusTimeline steps={preview} compact title="Ход заявки" />
      <Link className="secondary-button" href="/status">
        Открыть полный статус
      </Link>
    </div>
  );
}
