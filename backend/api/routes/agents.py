"""
Agents API Routes

GET  /api/agents            — All 5 agents with status & wallet
GET  /api/agents/{name}     — Single agent detail
POST /api/agents/{name}/pause — Pause or resume
PATCH /api/agents/{name}/config — Update thresholds
POST /api/agents/{name}/run — Manual trigger
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

AgentName = Literal["signal", "risk", "execution", "portfolio", "economy"]


class PauseRequest(BaseModel):
    paused: bool


class ConfigUpdateRequest(BaseModel):
    max_trade_size_usd: float | None = None
    min_security_score: int | None = None
    loop_interval_seconds: int | None = None


# In-memory agent state (replace with Supabase in production)
_agent_states: dict[str, dict] = {
    name: {
        "id": str(uuid.uuid4()),
        "name": name,
        "display_name": f"{name.title()} Agent",
        "status": "active",
        "wallet": {
            "address": f"0x{'0' * 38}{['11', '22', '33', '44', '55'][i]}",
            "balance_eth": round(0.1 + i * 0.05, 3),
            "balance_usd": round(320 + i * 50, 2),
            "earnings_total_usd": round(i * 45.2, 2),
        },
        "last_action": "Initialized",
        "last_action_at": datetime.now(timezone.utc).isoformat(),
        "loop_interval_seconds": [300, 0, 0, 300, 900][i],
        "decisions_today": [42, 28, 8, 144, 5][i],
        "success_rate": [0.89, 0.97, 0.94, 0.99, 1.0][i],
        "skills": [
            ["okx-dex-signal", "okx-dex-trenches", "okx-dex-market", "okx-dex-token"],
            ["okx-security", "okx-audit-log"],
            ["okx-dex-swap", "okx-defi-invest", "okx-onchain-gateway"],
            ["okx-wallet-portfolio", "okx-defi-portfolio", "okx-agentic-wallet"],
            ["x402"],
        ][i],
    }
    for i, name in enumerate(["signal", "risk", "execution", "portfolio", "economy"])
}


@router.get("")
async def get_agents():
    """Return all 5 agents with current status."""
    return {
        "success": True,
        "data": list(_agent_states.values()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{name}")
async def get_agent(name: AgentName):
    """Return single agent detail."""
    if name not in _agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return {
        "success": True,
        "data": _agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{name}/pause")
async def toggle_pause(name: AgentName, body: PauseRequest):
    """Pause or resume an agent."""
    if name not in _agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    _agent_states[name]["status"] = "paused" if body.paused else "active"
    _agent_states[name]["last_action"] = "Paused" if body.paused else "Resumed"
    _agent_states[name]["last_action_at"] = datetime.now(timezone.utc).isoformat()

    # TODO: Signal scheduler to pause/resume the APScheduler job

    return {
        "success": True,
        "data": _agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/{name}/config")
async def update_config(name: AgentName, body: ConfigUpdateRequest):
    """Update agent configuration thresholds."""
    if name not in _agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # TODO: Persist to Supabase and hot-reload agent config
    if body.loop_interval_seconds:
        _agent_states[name]["loop_interval_seconds"] = body.loop_interval_seconds

    return {
        "success": True,
        "data": _agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{name}/run")
async def trigger_run(name: AgentName):
    """Manually trigger a single agent run."""
    if name not in _agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # TODO: Import orchestrator and trigger targeted run
    job_id = str(uuid.uuid4())
    _agent_states[name]["status"] = "thinking"
    _agent_states[name]["last_action"] = "Manual run triggered"
    _agent_states[name]["last_action_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "data": {"job_id": job_id, "agent": name, "status": "queued"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
