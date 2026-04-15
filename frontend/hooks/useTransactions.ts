"use client";

import useSWR from "swr";
import { transactionsApi } from "@/lib/api";
import type { Transaction } from "@/lib/types";

export function useTransactions(page = 1) {
  const { data, isLoading, error } = useSWR(
    `/api/transactions?page=${page}`,
    () => transactionsApi.getAll(page).then((r) => r.data),
    {
      refreshInterval: 30_000,
      errorRetryCount: 3,
      errorRetryInterval: 5_000,
    }
  );

  return {
    transactions: data?.items as Transaction[] | undefined,
    total: data?.total,
    isLoading,
    error,
    isOffline: !!error && !data,
  };
}
