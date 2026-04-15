"""
Shared in-memory agent state.

Single source of truth for agent status, imported by:
  - api/routes/agents.py  (serves GET /api/agents)
  - agents/*.py           (updates status on every loop tick)

Avoids circular imports: this module only imports from config.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from config import get_settings

settings = get_settings()

_NAMES = ["signal", "risk", "execution", "portfolio", "economy"]

_WALLET_ATTRS = [
    "signal_agent_wallet_address",
    "risk_agent_wallet_address",
    "execution_agent_wallet_address",
    "portfolio_agent_wallet_address",
    "economy_agent_wallet_address",
]

_FALLBACK_SUFFIX = ["11", "22", "33", "44", "55"]

_SKILLS: list[list[str]] = [
    ["okx-dex-signal", "okx-dex-trenches", "okx-dex-market", "okx-dex-token"],
    ["okx-security", "okx-audit-log"],
    ["okx-dex-swap", "okx-defi-invest", "okx-onchain-gateway"],
    ["okx-wallet-portfolio", "okx-defi-portfolio", "okx-agentic-wallet"],
    ["x402"],
]

_INTERVALS = [300, 0, 0, 300, 900]


def _wallet_address(i: int) -> str:
    """Return configured wallet address or a deterministic placeholder."""
    addr = getattr(settings, _WALLET_ATTRS[i], "")
    return addr if addr else f"0x{'0' * 38}{_FALLBACK_SUFFIX[i]}"


agent_states: dict[str, dict] = {
    name: {
        "id": str(uuid.uuid4()),
        "name": name,
        "display_name": f"{name.title()} Agent",
        "status": "active",
        "wallet": {
            "address": _wallet_address(i),
            "balance_eth": 0.0,
            "balance_usd": 0.0,
            "earnings_total_usd": 0.0,
        },
        "last_action": "Initialized",
        "last_action_at": datetime.now(timezone.utc).isoformat(),
        "loop_interval_seconds": _INTERVALS[i],
        "decisions_today": 0,
        "success_rate": 0.0,
        "skills": _SKILLS[i],
    }
    for i, name in enumerate(_NAMES)
}


def update_agent_status(
    name: str,
    status: str,
    last_action: str = "",
    last_action_at: str = "",
) -> None:
    """
    Update in-memory agent state.
    Called by agents on every status change so GET /api/agents reflects live state.
    """
    if name not in agent_states:
        return
    agent_states[name]["status"] = status
    if last_action:
        agent_states[name]["last_action"] = last_action
    agent_states[name]["last_action_at"] = (
        last_action_at or datetime.now(timezone.utc).isoformat()
    )


def increment_decisions(name: str) -> None:
    """Increment the decisions_today counter for an agent."""
    if name in agent_states:
        agent_states[name]["decisions_today"] += 1


# Default treasury UUID — set at startup by _ensure_default_treasury() in main.py.
# Agents include this as treasury_id when persisting snapshots/transactions.
default_treasury_id: str | None = None
