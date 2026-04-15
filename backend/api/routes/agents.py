"""
Agents API Routes

All state lives in api.state (shared with the agent loop processes).
GET /api/agents reflects real-time agent status because agents call
update_agent_status() on every loop tick.

GET  /api/agents            — All 5 agents with live status & wallet
GET  /api/agents/{name}     — Single agent detail
POST /api/agents/{name}/pause  — Pause or resume
PATCH /api/agents/{name}/config — Update thresholds
POST /api/agents/{name}/run — Manual trigger
"""

import asyncio
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.state import agent_states, update_agent_status
from api.websocket import broadcast

router = APIRouter()

AgentName = Literal["signal", "risk", "execution", "portfolio", "economy"]


class PauseRequest(BaseModel):
    paused: bool


class ConfigUpdateRequest(BaseModel):
    max_trade_size_usd: float | None = None
    min_security_score: int | None = None
    loop_interval_seconds: int | None = None


@router.get("")
async def get_agents():
    """Return all 5 agents with current live status."""
    return {
        "success": True,
        "data": list(agent_states.values()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{name}")
async def get_agent(name: AgentName):
    if name not in agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return {
        "success": True,
        "data": agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{name}/pause")
async def toggle_pause(name: AgentName, body: PauseRequest):
    if name not in agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    new_status = "paused" if body.paused else "active"
    action = "Paused by operator" if body.paused else "Resumed by operator"
    update_agent_status(name, new_status, action)

    await broadcast("agent_status_update", {
        "name": name,
        "status": new_status,
        "last_action": action,
        "last_action_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "data": agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/{name}/config")
async def update_config(name: AgentName, body: ConfigUpdateRequest):
    if name not in agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    if body.loop_interval_seconds:
        agent_states[name]["loop_interval_seconds"] = body.loop_interval_seconds

    return {
        "success": True,
        "data": agent_states[name],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{name}/run")
async def trigger_run(name: AgentName):
    if name not in agent_states:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    import uuid as _uuid
    job_id = str(_uuid.uuid4())
    update_agent_status(name, "thinking", "Manual run triggered")

    await broadcast("agent_status_update", {
        "name": name,
        "status": "thinking",
        "last_action": "Manual run triggered",
        "last_action_at": datetime.now(timezone.utc).isoformat(),
    })

    # Fire-and-forget targeted run via orchestrator
    try:
        from crons.scheduler import get_orchestrator
        orchestrator = get_orchestrator()

        async def _run():
            if name == "signal":
                await orchestrator.run_cycle()
            elif name == "portfolio":
                await orchestrator.portfolio_agent.run()
            elif name == "economy":
                await orchestrator.economy_agent.run()

        asyncio.create_task(_run())
    except Exception:
        pass

    return {
        "success": True,
        "data": {"job_id": job_id, "agent": name, "status": "queued"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
