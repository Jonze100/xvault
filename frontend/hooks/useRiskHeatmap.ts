"use client";

import useSWR from "swr";
import { treasuryApi } from "@/lib/api";
import type { RiskHeatmapCell } from "@/lib/types";

export function useRiskHeatmap() {
  const { data, isLoading, error } = useSWR<RiskHeatmapCell[]>(
    "/api/treasury/risk-heatmap",
    () => treasuryApi.getRiskHeatmap().then((r) => r.data),
    {
      refreshInterval: 120_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  return { data, isLoading, error, isOffline: !!error && !data };
}
