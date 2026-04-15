// =============================================================================
// XVault Backend API Client
// =============================================================================

import type {
  ApiResponse,
  PaginatedResponse,
  Agent,
  Treasury,
  AgentDecision,
  Transaction,
  PerformanceFee,
  PnLDataPoint,
  RiskHeatmapCell,
  CommandResult,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res.json();
}

// -----------------------------------------------------------------------------
// Treasury Endpoints
// -----------------------------------------------------------------------------

export const treasuryApi = {
  /** Fetch full treasury state including all assets */
  getOverview: () =>
    apiFetch<Treasury>("/api/treasury"),

  /** Historical PnL data for charts (interval: 1h, 4h, 1d) */
  getPnLHistory: (range: "24h" | "7d" | "30d" | "all" = "24h") =>
    apiFetch<PnLDataPoint[]>(`/api/treasury/pnl?range=${range}`),

  /** Risk heatmap data across protocols */
  getRiskHeatmap: () =>
    apiFetch<RiskHeatmapCell[]>("/api/treasury/risk-heatmap"),

  /** Trigger manual rebalance (requires risk agent approval) */
  triggerRebalance: () =>
    apiFetch<{ job_id: string }>("/api/treasury/rebalance", { method: "POST" }),
};

// -----------------------------------------------------------------------------
// Agent Endpoints
// -----------------------------------------------------------------------------

export const agentsApi = {
  /** Get all 5 agents with current status and wallet balances */
  getAll: () =>
    apiFetch<Agent[]>("/api/agents"),

  /** Get single agent details */
  getOne: (name: string) =>
    apiFetch<Agent>(`/api/agents/${name}`),

  /** Pause or resume an agent */
  togglePause: (name: string, paused: boolean) =>
    apiFetch<Agent>(`/api/agents/${name}/pause`, {
      method: "POST",
      body: JSON.stringify({ paused }),
    }),

  /** Update agent configuration thresholds */
  updateConfig: (name: string, config: Record<string, unknown>) =>
    apiFetch<Agent>(`/api/agents/${name}/config`, {
      method: "PATCH",
      body: JSON.stringify(config),
    }),

  /** Trigger a single agent run manually */
  triggerRun: (name: string) =>
    apiFetch<{ job_id: string }>(`/api/agents/${name}/run`, { method: "POST" }),
};

// -----------------------------------------------------------------------------
// Decision Log Endpoints
// -----------------------------------------------------------------------------

export const decisionsApi = {
  /** Paginated decision feed across all agents */
  getAll: (page = 1, page_size = 50) =>
    apiFetch<PaginatedResponse<AgentDecision>>(
      `/api/decisions?page=${page}&page_size=${page_size}`
    ),

  /** Decisions filtered by agent */
  getByAgent: (agent: string, limit = 20) =>
    apiFetch<AgentDecision[]>(`/api/decisions?agent=${agent}&limit=${limit}`),
};

// -----------------------------------------------------------------------------
// Transaction Endpoints
// -----------------------------------------------------------------------------

export const transactionsApi = {
  getAll: (page = 1) =>
    apiFetch<PaginatedResponse<Transaction>>(`/api/transactions?page=${page}`),

  getByHash: (hash: string) =>
    apiFetch<Transaction>(`/api/transactions/${hash}`),
};

// -----------------------------------------------------------------------------
// Economy Endpoints
// -----------------------------------------------------------------------------

export const economyApi = {
  /** Recent performance fee events */
  getFeesHistory: (limit = 20) =>
    apiFetch<PerformanceFee[]>(`/api/economy/fees?limit=${limit}`),

  /** Agent earnings breakdown */
  getAgentEarnings: () =>
    apiFetch<Record<string, number>>("/api/economy/earnings"),

  /** Total fees collected lifetime */
  getTotals: () =>
    apiFetch<{ total_fees_usd: number; total_distributed_usd: number }>(
      "/api/economy/totals"
    ),
};

// -----------------------------------------------------------------------------
// Natural Language Command Endpoint
// -----------------------------------------------------------------------------

export const commandApi = {
  /** Send a natural language command to the orchestrator */
  execute: (command: string) =>
    apiFetch<CommandResult>("/api/command", {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
};
