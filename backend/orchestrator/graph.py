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
        Uses Claude to classify intent, then executes the appropriate action.

        Supported intents:
          run_cycle      → trigger full signal→risk→execution pipeline
          run_portfolio  → run portfolio agent immediately
          run_economy    → run economy agent immediately
          rebalance      → trigger rebalance cycle
          query_treasury → return current treasury snapshot
          query_agents   → return live agent statuses
          query_risk     → return current risk score
          pause_agent    → pause a named agent
          resume_agent   → resume a named agent
          unknown        → Claude answers directly as the treasury AI
        """
        import json
        import asyncio
        from anthropic import AsyncAnthropic
        from config import get_settings
        from db.client import get_supabase
        import api.state as _state

        settings = get_settings()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        # ── Step 1: classify intent ──────────────────────────────────────────
        classify_prompt = f"""You are the AI brain of XVault — an autonomous 5-agent DeFi treasury on OKX X Layer.

Current treasury value: ~$147,000 on OKX X Layer (Chain ID 196)
Active agents: Signal, Risk, Execution, Portfolio, Economy
Wallet: 0x10bfbc3a505e78c3721993945ccbd391f8048f91

User command: "{command}"

Classify the command. Respond ONLY with valid JSON, no markdown:
{{
  "intent": "run_cycle" | "run_portfolio" | "run_economy" | "rebalance" | "query_treasury" | "query_agents" | "query_risk" | "pause_agent" | "resume_agent" | "unknown",
  "agent_name": "signal" | "risk" | "execution" | "portfolio" | "economy" | null,
  "token": "<token symbol if mentioned, else null>",
  "answer": "<if intent is query_* or unknown: answer the question directly in 1-2 sentences as the XVault AI, else null>"
}}"""

        try:
            classify_resp = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": classify_prompt}],
            )
            raw = classify_resp.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
        except Exception as exc:
            log.warning("handle_command.classify_failed", error=str(exc))
            parsed = {"intent": "unknown", "agent_name": None, "token": None, "answer": None}

        intent     = parsed.get("intent", "unknown")
        agent_name = parsed.get("agent_name")
        answer     = parsed.get("answer")

        # ── Step 2: execute intent ───────────────────────────────────────────
        try:
            # --- Query intents (fast, no agent run) -------------------------
            if intent == "query_treasury":
                db = get_supabase()
                value = 0.0
                risk  = 0
                if db:
                    snap = db.table("treasury_snapshots").select("total_value_usd,pnl_usd,risk_score").order("snapshot_at", desc=True).limit(1).execute()
                    if snap.data:
                        value = float(snap.data[0].get("total_value_usd", 0))
                        risk  = int(snap.data[0].get("risk_score") or 0)
                msg = answer or f"Treasury is currently at ${value:,.2f} with a risk score of {risk}/100 on OKX X Layer."
                return {"success": True, "agent": "portfolio", "message": msg, "action": "query"}

            if intent == "query_risk":
                score = 0
                db = get_supabase()
                if db:
                    snap = db.table("treasury_snapshots").select("risk_score").order("snapshot_at", desc=True).limit(1).execute()
                    if snap.data:
                        score = int(snap.data[0].get("risk_score") or 0)
                level = "LOW" if score < 40 else ("MEDIUM" if score < 70 else "HIGH")
                msg = answer or f"Current risk score is {score}/100 ({level}). Portfolio concentration and stablecoin ratio are within acceptable thresholds."
                return {"success": True, "agent": "risk", "message": msg, "action": "query"}

            if intent == "query_agents":
                statuses = [
                    f"{name}: {data['status']}"
                    for name, data in _state.agent_states.items()
                ]
                msg = answer or "Agent status — " + " | ".join(statuses)
                return {"success": True, "agent": "signal", "message": msg, "action": "query"}

            # --- Pause / Resume ---------------------------------------------
            if intent == "pause_agent" and agent_name:
                if agent_name in _state.agent_states:
                    _state.update_agent_status(agent_name, "paused", f"Paused via command: {command}")
                    await broadcast("agent_status_update", {
                        "name": agent_name, "status": "paused",
                        "last_action": f"Paused via NL command",
                        "last_action_at": datetime.now(timezone.utc).isoformat(),
                    })
                return {"success": True, "agent": agent_name or "signal",
                        "message": f"{(agent_name or 'agent').title()} Agent paused.",
                        "action": "pause"}

            if intent == "resume_agent" and agent_name:
                if agent_name in _state.agent_states:
                    _state.update_agent_status(agent_name, "active", f"Resumed via command: {command}")
                    await broadcast("agent_status_update", {
                        "name": agent_name, "status": "active",
                        "last_action": "Resumed via NL command",
                        "last_action_at": datetime.now(timezone.utc).isoformat(),
                    })
                return {"success": True, "agent": agent_name or "signal",
                        "message": f"{(agent_name or 'agent').title()} Agent resumed.",
                        "action": "resume"}

            # --- Agent runs (fire-and-forget, return immediately) -----------
            if intent == "run_portfolio":
                asyncio.create_task(self.portfolio_agent.run())
                return {"success": True, "agent": "portfolio",
                        "message": "Portfolio Agent triggered — scanning positions and updating PnL.",
                        "action": "run_portfolio"}

            if intent == "run_economy":
                asyncio.create_task(self.economy_agent.run())
                return {"success": True, "agent": "economy",
                        "message": "Economy Agent triggered — reconciling fees and agent balances.",
                        "action": "run_economy"}

            if intent in ("run_cycle", "rebalance"):
                asyncio.create_task(self.run_cycle(nl_command=command))
                action_label = "Rebalance" if intent == "rebalance" else "Full cycle"
                return {"success": True, "agent": "signal",
                        "message": f"{action_label} triggered — Signal → Risk → Execution pipeline running in background.",
                        "action": intent}

            # --- Unknown: Claude answers directly ----------------------------
            if not answer:
                answer_resp = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=200,
                    messages=[{"role": "user", "content":
                        f"You are the XVault DeFi treasury AI on OKX X Layer. Answer briefly (1-2 sentences): {command}"}],
                )
                answer = answer_resp.content[0].text.strip()

            return {"success": True, "agent": "signal", "message": answer, "action": "answer"}

        except Exception as exc:
            log.error("handle_command.execute_failed", error=str(exc), intent=intent)
            return {"success": False, "agent": "signal",
                    "message": f"Error executing command: {str(exc)[:120]}", "action": "error"}
