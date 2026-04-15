"use client";

import useSWR from "swr";
import { treasuryApi } from "@/lib/api";
import type { PnLDataPoint } from "@/lib/types";

export function usePnLHistory(range: "24h" | "7d" | "30d" | "all") {
  const { data, isLoading, error } = useSWR<PnLDataPoint[]>(
    `/api/treasury/pnl?range=${range}`,
    () => treasuryApi.getPnLHistory(range).then((r) => r.data),
    {
      refreshInterval: 60_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  return {
    data,
    isLoading,
    error,
    isOffline: !!error && !data,
  };
}
