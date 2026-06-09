"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import type { CabinetSummary, CaseTimelineResponse } from "./types";

export function useCabinetData() {
  const [summary, setSummary] = useState<CabinetSummary | null>(null);
  const [timeline, setTimeline] = useState<CaseTimelineResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const summaryResponse = await api.getCabinetSummary();
        setSummary(summaryResponse);
        if (summaryResponse.access.active && summaryResponse.case) {
          try {
            setTimeline(await api.getCaseTimeline());
          } catch {
            setTimeline(null);
          }
        } else {
          setTimeline(null);
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить кабинет.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return { summary, timeline, error, loading };
}
