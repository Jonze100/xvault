"""
XVault LangGraph Orchestrator

Coordinates all 5 agents in a directed state machine:

    SCAN (SignalAgent)
         │
         ▼
    RISK_ASSESS (RiskAgent, per signal in parallel)
         │
         ├── approved → EXECUTE (ExecutionAgent)
         └── rejected → back to SCAN
                │
                ▼
         MONITOR (PortfolioAgent)
                │
                ├── profit detected → FEE_COLLECT (EconomyAgent)
                └── rebalance needed → back to SCAN
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from langgraph.graph import StateGraph, END

from .state import OrchestratorState
from agents import (
    SignalAgent,
    RiskAgent,
    ExecutionAgent,
    PortfolioAgent,
    EconomyAgent,
)
from api.websocket import broadcast

log = structlog.get_logger(__name__)


class XVaultOrchestrator:
    """
    LangGraph state machine coordinating all 5 XVault agents.
    Can be triggered by:
    1. APScheduler cron jobs (automatic)
    2. Natural language command from frontend
    3. Direct API call
    """

    def __init__(self):
        self.signal_agent    = SignalAgent()
        self.risk_agent      = RiskAgent()
        self.execution_agent = ExecutionAgent()
        self.portfolio_agent = PortfolioAgent()
        self.economy_agent   = EconomyAgent()

        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph state machine."""
        builder = StateGraph(OrchestratorState)

        # Add nodes (each maps to an agent action)
        builder.add_node("scan",          self._node_scan)
        builder.add_node("risk_assess",   self._node_risk_assess)
        builder.add_node("execute",       self._node_execute)
        builder.add_node("monitor",       self._node_monitor)
        builder.add_node("fee_collect",   self._node_fee_collect)
        builder.add_node("handle_error",  self._node_handle_error)

        # Entry point
        builder.set_entry_point("scan")

        # Edges
        builder.add_edge("scan", "risk_assess")

        builder.add_conditional_edges(
            "risk_assess",
            self._route_after_risk,
            {
                "execute":       "execute",
                "scan":          "scan",      # all rejected → re-scan next cycle
                "handle_error":  "handle_error",
            },
        )

        builder.add_edge("execute", "monitor")

        builder.add_conditional_edges(
            "monitor",
            self._route_after_monitor,
            {
                "fee_collect":   "fee_collect",
                "scan":          "scan",
                "complete":      END,
            },
        )

        builder.add_edge("fee_collect", END)
        builder.add_edge("handle_error", END)

        return builder.compile()

    # -------------------------------------------------------------------------
    # Node Implementations
    # -------------------------------------------------------------------------

    async def _node_scan(self, state: OrchestratorState) -> dict:
        """Signal Agent: scan markets and generate trade signals."""
        log.info("orchestrator.node.scan")

        await broadcast("agent_message", {
            "id": str(uuid.uuid4()),
            "from_agent": "signal",
            "to_agent": "all",
            "content": "Starting market scan...",
            "type": "broadcast",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        signals = await self.signal_agent.run()

        return {
            "phase": "risk_assessment",
            "signals": signals,
        }

    async def _node_risk_assess(self, state: OrchestratorState) -> dict:
        """Risk Agent: vet each signal in sequence (can be parallelized later)."""
        log.info("orchestrator.node.risk_assess", signals_count=len(state.signals))

        assessments: dict[str, Any] = {}
        approved: list[dict] = []

        for signal in state.signals:
            assessment = await self.risk_agent.assess(signal)
            assessments[signal["id"]] = assessment

            if assessment.get("approved"):
                approved.append({**signal, "assessment": assessment})
            else:
                log.info("orchestrator.signal_rejected", token=signal.get("token"))

        return {
            "phase": "execution" if approved else "idle",
            "assessments": assessments,
            "approved_signals": approved,
        }

    async def _node_execute(self, state: OrchestratorState) -> dict:
        """Execution Agent: execute all approved signals."""
        log.info("orchestrator.node.execute", count=len(state.approved_signals))

        results: dict[str, Any] = {}

        for signal in state.approved_signals:
            result = await self.execution_agent.execute(
                signal=signal,
                assessment=signal["assessment"],
            )
            results[signal["id"]] = result

        return {
            "phase": "monitoring",
            "execution_results": results,
        }

    async def _node_monitor(self, state: OrchestratorState) -> dict:
        """Portfolio Agent: update positions and check for profit/rebalance triggers."""
        log.info("orchestrator.node.monitor")

        portfolio_data = await self.portfolio_agent.run()

        profit = portfolio_data.get("unrealized_pnl_usd", 0)
        rebalance = portfolio_data.get("rebalance_needed", False)

        return {
            "phase": "fee_collection" if profit >= 500 else ("scanning" if rebalance else "complete"),
            "portfolio": portfolio_data,
            "detected_profit_usd": profit,
        }

    async def _node_fee_collect(self, state: OrchestratorState) -> dict:
        """Economy Agent: collect performance fee and distribute to agents."""
        log.info("orchestrator.node.fee_collect", profit=state.detected_profit_usd)

        fee_result = await self.economy_agent.collect_performance_fee(
            state.detected_profit_usd
        )

        return {
            "phase": "complete",
            "fee_result": fee_result,
        }

    async def _node_handle_error(self, state: OrchestratorState) -> dict:
        """Handle pipeline errors gracefully."""
        log.error("orchestrator.error", error=state.error)
        return {"phase": "error", "completed_at": datetime.now(timezone.utc).isoformat()}

    # -------------------------------------------------------------------------
    # Routing Functions
    # -------------------------------------------------------------------------

    def _route_after_risk(self, state: OrchestratorState) -> str:
        if state.error:
            return "handle_error"
        if state.approved_signals:
            return "execute"
        return "scan"  # nothing approved, wait for next cycle

    def _route_after_monitor(self, state: OrchestratorState) -> str:
        if state.detected_profit_usd >= 500:
            return "fee_collect"
        if state.portfolio.get("rebalance_needed"):
            return "scan"
        return "complete"

    # -------------------------------------------------------------------------
    # Public Interface
    # -------------------------------------------------------------------------

    async def run_cycle(self, nl_command: str | None = None) -> OrchestratorState:
        """
        Run a complete agent pipeline cycle.
        Called by APScheduler or via natural language command.
        """
        run_id = str(uuid.uuid4())
        initial_state = OrchestratorState(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            nl_command=nl_command,
        )

        log.info("orchestrator.cycle.start", run_id=run_id, command=nl_command)

        result = await self.graph.ainvoke(initial_state)
        final_state = OrchestratorState(**result) if isinstance(result, dict) else result

        final_state.completed_at = datetime.now(timezone.utc).isoformat()
        log.info("orchestrator.cycle.complete", run_id=run_id, phase=final_state.phase)

        return final_state

    async def handle_command(self, command: str) -> dict[str, Any]:
        """
        Process a natural language command from the frontend.
        Uses Claude to parse intent and route to appropriate agent.
        """
        # TODO: Use Claude to classify the command and route:
        # - "buy X" → run scan with forced signal for X
        # - "pause signal agent" → update agent status
        # - "show risk" → return current risk assessment
        # - "rebalance" → trigger rebalance cycle

        from anthropic import AsyncAnthropic
        from config import get_settings
        settings = get_settings()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": f"""You are controlling an autonomous DeFi treasury called XVault.

User command: "{command}"

Classify this command and respond with JSON:
{{
  "intent": "buy" | "sell" | "pause_agent" | "resume_agent" | "rebalance" | "query" | "unknown",
  "agent": "signal" | "risk" | "execution" | "portfolio" | "economy" | null,
  "token": "<token symbol or null>",
  "message": "<brief response to show user>"
}}"""
            }],
        )

        # TODO: Parse and act on classified intent
        return {
            "success": True,
            "agent": "signal",
            "message": f"Command received: '{command}'. Processing...",
            "action": "cycle_triggered",
        }
