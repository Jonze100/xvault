"use client";

import useSWR from "swr";
import { treasuryApi } from "@/lib/api";
import { useWSEvents } from "./useWSEvents";
import type { Treasury } from "@/lib/types";

const fetcher = () => treasuryApi.getOverview().then((r) => r.data);

export function useTreasury() {
  const { data, error, isLoading, mutate } = useSWR<Treasury>(
    "/api/treasury",
    fetcher,
    {
      refreshInterval: 30_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  useWSEvents("treasury_update", (updated: Partial<Treasury>) => {
    mutate((prev) => (prev ? { ...prev, ...updated } : prev), {
      revalidate: false,
    });
  });

  return {
    treasury: data,
    isLoading,
    error,
    isOffline: !!error && !data,
    refetch: () => mutate(),
  };
}
