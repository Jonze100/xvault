"""
XVault Database Models — Pydantic models matching Supabase schema.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field
import uuid


# =============================================================================
# Users
# =============================================================================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settings: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Treasury
# =============================================================================

class Treasury(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str = "XVault Treasury"
    wallet_address: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_value_usd: float = 0.0
    risk_score: int = 0
    performance_fees_collected_usd: float = 0.0


class TreasurySnapshot(BaseModel):
    """Periodic portfolio snapshots for PnL charting."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    treasury_id: str
    total_value_usd: float
    pnl_usd: float
    pnl_pct: float
    assets: list[dict[str, Any]] = Field(default_factory=list)
    snapshot_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Agent Wallets
# =============================================================================

class AgentWallet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: Literal["signal", "risk", "execution", "portfolio", "economy"]
    address: str
    balance_eth: float = 0.0
    balance_usd: float = 0.0
    earnings_total_usd: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Transactions
# =============================================================================

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    treasury_id: str
    agent_name: str
    type: Literal["swap", "invest", "bridge", "fee", "transfer"]
    status: Literal["pending", "confirmed", "failed"] = "pending"
    from_token: str
    to_token: str
    amount_in: float
    amount_out: float
    value_usd: float
    tx_hash: str
    chain: str = "xlayer"
    gas_usd: float = 0.0
    slippage_pct: float = 0.0
    block_number: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: datetime | None = None


# =============================================================================
# Agent Logs / Decisions
# =============================================================================

class AgentLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    decision_type: str
    reasoning: str
    confidence: float
    data: dict[str, Any] = Field(default_factory=dict)
    tx_hash: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str  # agent name or "all"
    content: str
    message_type: Literal["signal", "request", "response", "broadcast"]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Performance Fees (Economy Agent)
# =============================================================================

class PerformanceFee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    treasury_id: str
    amount_usd: float
    trigger_profit_usd: float
    fee_pct: float = 10.0
    collection_tx_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeeDistribution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fee_id: str
    agent_name: str
    amount_usd: float
    pct: float
    tx_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
