// =============================================================================
// XVault Shared TypeScript Types
// =============================================================================

// -----------------------------------------------------------------------------
// Agent Types
// -----------------------------------------------------------------------------

export type AgentName = "signal" | "risk" | "execution" | "portfolio" | "economy";
export type AgentStatus = "active" | "idle" | "thinking" | "error" | "paused";

export interface AgentWallet {
  address: string;
  balance_eth: number;
  balance_usd: number;
  earnings_total_usd: number;
}

export interface Agent {
  id: string;
  name: AgentName;
  display_name: string;
  status: AgentStatus;
  wallet: AgentWallet;
  last_action: string;
  last_action_at: string;     // ISO timestamp
  loop_interval_seconds: number;
  decisions_today: number;
  success_rate: number;       // 0-1
  skills: string[];
}

// -----------------------------------------------------------------------------
// Decision / Log Types
// -----------------------------------------------------------------------------

export type DecisionType =
  | "signal_detected"
  | "risk_assessment"
  | "trade_approved"
  | "trade_rejected"
  | "trade_executed"
  | "position_opened"
  | "position_closed"
  | "fee_collected"
  | "fee_distributed"
  | "rebalance_triggered";

export interface AgentDecision {
  id: string;
  agent: AgentName;
  type: DecisionType;
  reasoning: string;
  confidence: number;         // 0-1
  data: Record<string, unknown>;
  timestamp: string;
  tx_hash?: string;
}

export interface AgentMessage {
  id: string;
  from_agent: AgentName;
  to_agent: AgentName | "all";
  content: string;
  type: "signal" | "request" | "response" | "broadcast";
  timestamp: string;
}

// -----------------------------------------------------------------------------
// Treasury Types
// -----------------------------------------------------------------------------

export interface TreasuryAsset {
  symbol: string;
  name: string;
  address: string;
  chain: string;
  balance: number;
  price_usd: number;
  value_usd: number;
  allocation_pct: number;     // 0-100
  pnl_24h_pct: number;
  pnl_24h_usd: number;
}

export interface Treasury {
  id: string;
  name: string;
  total_value_usd: number;
  total_pnl_24h_usd: number;
  total_pnl_24h_pct: number;
  total_pnl_7d_usd: number;
  total_pnl_all_time_usd: number;
  assets: TreasuryAsset[];
  risk_score: number;         // 0-100
  last_rebalance: string;
  performance_fees_collected_usd: number;
}

// -----------------------------------------------------------------------------
// Chart Data Types
// -----------------------------------------------------------------------------

export interface PnLDataPoint {
  timestamp: string;
  value_usd: number;
  pnl_usd: number;
  pnl_pct: number;
}

export interface RiskHeatmapCell {
  protocol: string;
  chain: string;
  exposure_usd: number;
  risk_score: number;         // 0-100
  audit_score: number;        // 0-100
}

// -----------------------------------------------------------------------------
// Transaction Types
// -----------------------------------------------------------------------------

export type TransactionStatus = "pending" | "confirmed" | "failed";
export type TransactionType = "swap" | "invest" | "bridge" | "fee" | "transfer";

export interface Transaction {
  id: string;
  type: TransactionType;
  status: TransactionStatus;
  from_token: string;
  to_token: string;
  amount_in: number;
  amount_out: number;
  value_usd: number;
  tx_hash: string;
  chain: string;
  gas_usd: number;
  slippage_pct: number;
  agent: AgentName;
  timestamp: string;
  block_number?: number;
}

// -----------------------------------------------------------------------------
// WebSocket Event Types
// -----------------------------------------------------------------------------

export type WSEventType =
  | "agent_status_update"
  | "agent_decision"
  | "agent_message"
  | "transaction_update"
  | "treasury_update"
  | "error";

export interface WSEvent<T = unknown> {
  event: WSEventType;
  data: T;
  timestamp: string;
}

// -----------------------------------------------------------------------------
// Economy / Fee Types
// -----------------------------------------------------------------------------

export interface PerformanceFee {
  id: string;
  amount_usd: number;
  trigger_profit_usd: number;
  fee_pct: number;
  timestamp: string;
  distributions: FeeDistribution[];
}

export interface FeeDistribution {
  agent: AgentName;
  amount_usd: number;
  pct: number;
  tx_hash: string;
}

// -----------------------------------------------------------------------------
// API Response Wrappers
// -----------------------------------------------------------------------------

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// -----------------------------------------------------------------------------
// UI State Types
// -----------------------------------------------------------------------------

export interface CommandResult {
  success: boolean;
  agent: AgentName;
  message: string;
  action?: string;
}
