"use client";

import useSWR from "swr";
import { economyApi } from "@/lib/api";

export function useEconomyEarnings() {
  const { data, isLoading, error } = useSWR(
    "/api/economy/earnings",
    () => economyApi.getAgentEarnings().then((r) => r.data),
    {
      refreshInterval: 60_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  return {
    earnings: data as Record<string, number> | undefined,
    isLoading,
    error,
    isOffline: !!error && !data,
  };
}

export function useEconomyTotals() {
  const { data, isLoading, error } = useSWR(
    "/api/economy/totals",
    () => economyApi.getTotals().then((r) => r.data),
    {
      refreshInterval: 60_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  return { totals: data, isLoading, isOffline: !!error && !data };
}
