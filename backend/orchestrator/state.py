"""
XVault Orchestrator State — Shared state passed between LangGraph nodes.
"""

from __future__ import annotations

from typing import Any, Literal
from dataclasses import dataclass, field


AgentName = Literal["signal", "risk", "execution", "portfolio", "economy"]


@dataclass
class OrchestratorState:
    """
    Shared state passed through the LangGraph agent pipeline.
    Each node reads from and writes to this state.
    """

    # Current pipeline phase
    phase: Literal[
        "idle",
        "scanning",
        "risk_assessment",
        "execution",
        "monitoring",
        "fee_collection",
        "complete",
        "error",
    ] = "idle"

    # Signals from Signal Agent
    signals: list[dict[str, Any]] = field(default_factory=list)

    # Risk assessment results (keyed by signal id)
    assessments: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Approved signals ready for execution
    approved_signals: list[dict[str, Any]] = field(default_factory=list)

    # Execution results (keyed by signal id)
    execution_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Current portfolio snapshot
    portfolio: dict[str, Any] = field(default_factory=dict)

    # Detected profit for Economy Agent
    detected_profit_usd: float = 0.0

    # Fee collection results
    fee_result: dict[str, Any] = field(default_factory=dict)

    # Natural language command (if triggered by user)
    nl_command: str | None = None

    # Error state
    error: str | None = None

    # Metadata
    run_id: str = ""
    started_at: str = ""
    completed_at: str | None = None
