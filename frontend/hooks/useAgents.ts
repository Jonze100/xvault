"use client";

import useSWR from "swr";
import { agentsApi } from "@/lib/api";
import { useWSEvents } from "./useWSEvents";
import type { Agent } from "@/lib/types";

const fetcher = () => agentsApi.getAll().then((r) => r.data);

const SWR_OPTIONS = {
  refreshInterval: 15_000,
  errorRetryCount: 3,
  errorRetryInterval: 5_000,
};

export function useAgents() {
  const { data, error, isLoading, mutate } = useSWR<Agent[]>(
    "/api/agents",
    fetcher,
    SWR_OPTIONS
  );

  useWSEvents("agent_status_update", (updated: Agent) => {
    mutate(
      (prev) =>
        prev?.map((a) => (a.id === updated.id ? updated : a)) ?? prev,
      { revalidate: false }
    );
  });

  return {
    agents: data,
    isLoading,
    error,
    isOffline: !!error && !data,
    refetch: () => mutate(),
  };
}
