"""
Portfolio Agent — Position Monitoring & Rebalancing

Agentic Wallet: portfolio.xvault.eth
OKX Onchain OS Skills used:
  - okx-wallet-portfolio  Aggregate all on-chain token balances across chains
                          for the treasury wallet address
  - okx-defi-portfolio    Enumerate active DeFi positions: LP shares, staked
                          tokens, lending deposits, yield vault receipts
  - okx-agentic-wallet    Manage the agentic wallet — top up gas, check allowances,
                          confirm the treasury wallet is properly funded

Runs every 5 minutes via APScheduler. Monitors all positions, calculates PnL,
detects profit events that trigger Economy Agent fee collection, and triggers
rebalancing when needed.

Monitoring Pipeline:
  okx-wallet-portfolio → spot balances (onchainos portfolio all-balances)
  okx-defi-portfolio   → DeFi positions (onchainos portfolio overview)
  → aggregate + calculate PnL vs last snapshot
  → if profit > $500 → notify Economy Agent via agent_message
  → if concentration > 25% → trigger rebalance signal
  → persist treasury snapshot to Supabase → broadcast treasury_update to frontend
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from anthropic import AsyncAnthropic

from config import get_settings
from db.client import get_supabase
from api.websocket import broadcast
from api.state import update_agent_status as _update_state
import api.state as _state

log = structlog.get_logger(__name__)
settings = get_settings()

ONCHAINOS = os.path.expanduser("~/.local/bin/onchainos")


class PortfolioAgent:
    """
    Monitors treasury positions and triggers actions when thresholds are met.

    Responsibilities:
    - Aggregate all wallet/DeFi positions via OKX portfolio CLI commands
    - Calculate real-time PnL against cost basis
    - Detect significant profit events (> $500) for Economy Agent
    - Trigger rebalancing if concentration exceeds limits
    - Maintain treasury snapshot in Supabase
    """

    NAME = "portfolio"
    LOOP_INTERVAL = 300  # 5 minutes
    PROFIT_TRIGGER_USD = 500  # Economy Agent collects fee when profit exceeds this

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.db = get_supabase()
        self._last_portfolio_value: float | None = None

    # ─── onchainos subprocess helper ────────────────────────────────────────

    async def _run_onchainos(self, *args: str, timeout: int = 30) -> Any:
        """
        Execute onchainos CLI and return parsed JSON output.
        Returns None on any error so callers can fall back gracefully.
        """
        cmd = [ONCHAINOS, *args]
        log.debug("onchainos.call", cmd=cmd)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if proc.returncode != 0:
                log.warning(
                    "onchainos.nonzero",
                    cmd=cmd,
                    returncode=proc.returncode,
                    stderr=stderr.decode().strip(),
                )
                return None
            return json.loads(stdout.decode().strip())
        except (asyncio.TimeoutError, json.JSONDecodeError, FileNotFoundError) as exc:
            log.warning("onchainos.error", cmd=cmd, error=str(exc))
            return None

    # ─── main loop ──────────────────────────────────────────────────────────

    async def run(self) -> dict[str, Any]:
        """
        Main monitoring loop — returns current portfolio state.
        Emits PROFIT_DETECTED event if applicable.
        """
        log.info("portfolio_agent.run.start")
        await self._broadcast_status("thinking")

        try:
            # 1. Fetch wallet balances via onchainos portfolio all-balances (okx-wallet-portfolio)
            wallet_positions = await self._fetch_wallet_portfolio()

            # 2. Fetch PnL overview via onchainos portfolio overview (okx-defi-portfolio)
            pnl_overview = await self._fetch_pnl_overview()

            # 3. Combine and calculate total portfolio value
            portfolio = await self._aggregate_portfolio(wallet_positions, pnl_overview)

            # 4. Calculate PnL vs last snapshot
            pnl = await self._calculate_pnl(portfolio, pnl_overview)

            # 5. Check if profit trigger met → notify Economy Agent
            if pnl.get("unrealized_pnl_usd", 0) >= self.PROFIT_TRIGGER_USD:
                await self._emit_profit_event(pnl, portfolio)

            # 6. Check rebalance need
            rebalance_needed = await self._check_rebalance(portfolio)

            # 7. Persist snapshot to Supabase
            await self._persist_snapshot(portfolio, pnl)

            # 8. Broadcast treasury update to frontend
            await broadcast("treasury_update", {
                "total_value_usd": portfolio["total_value_usd"],
                "total_pnl_24h_usd": pnl.get("pnl_24h_usd", 0),
                "total_pnl_24h_pct": pnl.get("pnl_24h_pct", 0),
                "assets": portfolio["assets"],
                "risk_score": portfolio.get("risk_score", 50),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            await self._broadcast_status("active")
            return {**portfolio, **pnl, "rebalance_needed": rebalance_needed}

        except Exception as e:
            log.error("portfolio_agent.run.error", error=str(e))
            await self._broadcast_status("error")
            return {}

    # ─── data fetchers ──────────────────────────────────────────────────────

    async def _fetch_wallet_portfolio(self) -> list[dict]:
        """
        Onchain OS Skill: okx-wallet-portfolio
        CLI: onchainos portfolio all-balances --address <treasury> --chains 196

        --address:  The treasury wallet address to inspect.
        --chains:   Comma-separated chain IDs or names. We use "196" (XLayer chain ID).
                    Supports up to 50 chains.
        --filter 1: Include all tokens (pass 1 to see everything including risky tokens;
                    pass 0 to hide dust/risk tokens — default).

        Response shape (top-level object with tokenAssets array):
          {
            "tokenAssets": [
              {
                "chainIndex": "196",
                "tokenContractAddress": "0x74b7...",
                "symbol": "USDC",
                "balance": "65800.0",       // human-readable balance
                "rawBalance": "65800000000", // base units
                "tokenPrice": "1.0",        // USD
                "isRiskToken": false
              },
              {
                "chainIndex": "196",
                "tokenContractAddress": "",
                "symbol": "OKB",
                "balance": "48.5",
                "tokenPrice": "48.20",
                "isRiskToken": false
              },
              ...
            ]
          }
        """
        address = settings.treasury_wallet_address
        if not address:
            log.warning("portfolio_agent.wallet.no_address_configured")
            return self._empty_positions()

        result = await self._run_onchainos(
            "portfolio", "all-balances",
            "--address", address,
            "--chains", "196",
        )

        if result:
            # Real API shape: { "ok": true, "data": [ { "tokenAssets": [...] } ] }
            # or { "ok": true, "data": { "details": [...] } }
            raw_data = result.get("data", result) if isinstance(result, dict) else result
            assets = []
            if isinstance(raw_data, list):
                # data is array of chain groups, each with tokenAssets
                for group in raw_data:
                    if isinstance(group, dict) and "tokenAssets" in group:
                        assets.extend(group["tokenAssets"])
                    elif isinstance(group, dict) and "symbol" in group:
                        assets.append(group)  # flat list of assets
            elif isinstance(raw_data, dict):
                details = raw_data.get("details", [])
                if details and isinstance(details, list):
                    for d in details:
                        assets.extend(d.get("tokenAssets", []))
                else:
                    assets = raw_data.get("tokenAssets", [])
            return [
                {
                    "symbol": a.get("symbol", "UNKNOWN"),
                    "contract": a.get("tokenContractAddress", ""),
                    "balance": float(a.get("balance", 0)),
                    "price_usd": float(a.get("tokenPrice", 0)),
                    "chain": "xlayer",
                    "is_risk": a.get("isRiskToken", False),
                }
                for a in assets
                if not a.get("isRiskToken", False)
                   and float(a.get("balance", 0)) > 0
            ]

        # No fallback to fake data — return empty so the UI shows real state
        log.error("portfolio_agent.wallet.REAL_CLI_FAILED — returning empty positions")
        return []

    async def _fetch_pnl_overview(self) -> dict[str, Any]:
        """
        Onchain OS Skill: okx-wallet-portfolio (overview endpoint)
        CLI: onchainos portfolio overview --address <treasury>
                                          --chain xlayer
                                          --time-frame 1d

        --time-frame options: 1d, 3d, 7d, 1m, 3m  (default: 7d)
        We use 1d for the dashboard's 24h PnL figure.

        Response shape:
          {
            "realizedPnlUsd": "234.50",
            "unrealizedPnlUsd": "890.20",
            "totalPnlUsd": "1124.70",
            "totalPnlPercent": "0.79",      // percent as string
            "winRate": "0.68",
            "buyTxCount": "12",
            "sellTxCount": "7",
            "topPnlTokenList": [
              { "tokenSymbol": "OKB", "totalPnl": "567.80" },
              ...
            ]
          }
        """
        address = settings.treasury_wallet_address
        if not address:
            return {}

        result = await self._run_onchainos(
            "market", "portfolio-overview",
            "--address", address,
            "--chain", "xlayer",
            "--time-frame", "1",  # 1=1D, 2=3D, 3=7D, 4=1M
        )

        if result:
            # Real API shape: { "ok": true, "data": { "realizedPnlUsd": ..., ... } }
            data = result.get("data", result) if isinstance(result, dict) else result
            if isinstance(data, dict):
                return {
                    "realized_pnl_usd": float(data.get("realizedPnlUsd", 0)),
                    "unrealized_pnl_usd": float(data.get("unrealizedPnlUsd", 0)),
                    "total_pnl_usd": float(data.get("totalPnlUsd", 0)),
                    "total_pnl_pct": float(data.get("totalPnlPercent", 0)),
                    "win_rate": float(data.get("winRate", 0)),
                }

        return {}

    # ─── aggregation & calculations ─────────────────────────────────────────

    async def _aggregate_portfolio(
        self, wallet: list[dict], pnl_overview: dict
    ) -> dict[str, Any]:
        """Combine wallet positions into unified portfolio snapshot."""
        wallet_total = sum(p["balance"] * p["price_usd"] for p in wallet)

        assets = []
        for pos in wallet:
            value = pos["balance"] * pos["price_usd"]
            assets.append({
                "symbol": pos["symbol"],
                "balance": pos["balance"],
                "price_usd": pos["price_usd"],
                "value_usd": value,
                "allocation_pct": (value / wallet_total * 100) if wallet_total > 0 else 0,
                "chain": pos["chain"],
                "pnl_24h_pct": 0.0,
                "pnl_24h_usd": 0.0,
            })

        return {
            "total_value_usd": wallet_total,
            "wallet_value_usd": wallet_total,
            "defi_value_usd": 0.0,
            "assets": assets,
            "risk_score": await self._calculate_risk_score(assets),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _calculate_pnl(
        self, portfolio: dict, pnl_overview: dict
    ) -> dict[str, Any]:
        """Calculate PnL: prefer live onchainos data, fall back to snapshot diff."""
        if pnl_overview:
            return {
                "unrealized_pnl_usd": pnl_overview.get("unrealized_pnl_usd", 0),
                "pnl_24h_usd": pnl_overview.get("total_pnl_usd", 0),
                "pnl_24h_pct": pnl_overview.get("total_pnl_pct", 0),
            }

        current_value = portfolio["total_value_usd"]
        if self._last_portfolio_value is None:
            self._last_portfolio_value = current_value
            return {"unrealized_pnl_usd": 0, "pnl_24h_usd": 0, "pnl_24h_pct": 0}

        pnl_usd = current_value - self._last_portfolio_value
        pnl_pct = (pnl_usd / self._last_portfolio_value * 100) if self._last_portfolio_value > 0 else 0
        self._last_portfolio_value = current_value
        return {
            "unrealized_pnl_usd": pnl_usd,
            "pnl_24h_usd": pnl_usd,
            "pnl_24h_pct": pnl_pct,
        }

    async def _calculate_risk_score(self, assets: list[dict]) -> int:
        """
        Calculate portfolio risk score 0-100.
        Higher concentration → higher risk. More stablecoins → lower risk.
        """
        if not assets:
            return 0
        max_concentration = max(a["allocation_pct"] for a in assets) / 100
        stable_pct = sum(
            a["allocation_pct"] for a in assets if a["symbol"] in ("USDC", "USDT", "DAI")
        ) / 100
        risk = int((max_concentration * 60) + ((1 - stable_pct) * 40))
        return min(100, max(0, risk))

    async def _check_rebalance(self, portfolio: dict) -> bool:
        """Check if any asset exceeds MAX_PORTFOLIO_CONCENTRATION."""
        for asset in portfolio.get("assets", []):
            if asset["allocation_pct"] / 100 > settings.max_portfolio_concentration:
                log.warning("portfolio_agent.rebalance_needed", asset=asset["symbol"])
                await broadcast("agent_decision", {
                    "id": str(uuid.uuid4()),
                    "agent": self.NAME,
                    "type": "rebalance_triggered",
                    "reasoning": (
                        f"{asset['symbol']} at {asset['allocation_pct']:.1f}% "
                        f"exceeds 25% max concentration"
                    ),
                    "confidence": 1.0,
                    "data": {"asset": asset["symbol"], "current_pct": asset["allocation_pct"]},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return True
        return False

    async def _emit_profit_event(self, pnl: dict, portfolio: dict) -> None:
        """Notify orchestrator and Economy Agent of significant profit."""
        log.info("portfolio_agent.profit_detected", pnl=pnl["unrealized_pnl_usd"])
        await broadcast("agent_message", {
            "id": str(uuid.uuid4()),
            "from_agent": self.NAME,
            "to_agent": "economy",
            "content": (
                f"Profit detected: +${pnl['unrealized_pnl_usd']:.2f}. "
                f"Triggering 10% performance fee collection."
            ),
            "type": "signal",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def _persist_snapshot(self, portfolio: dict, pnl: dict) -> None:
        """Save portfolio snapshot to Supabase for historical PnL charts."""
        if not self.db:
            return
        try:
            # Column names match the treasury_snapshots schema exactly:
            #   pnl_usd, pnl_pct, snapshot_at (auto), risk_score (added in migration 002)
            assets = portfolio.get("assets", [])
            # Embed risk_score inside assets as extra metadata AND as top-level
            # so the API can read it without schema migration on Supabase Free.
            payload: dict = {
                "total_value_usd": float(portfolio.get("total_value_usd", 0)),
                "pnl_usd": float(pnl.get("pnl_24h_usd", 0)),
                "pnl_pct": float(pnl.get("pnl_24h_pct", 0)),
                "assets": assets,
            }
            if _state.default_treasury_id:
                payload["treasury_id"] = _state.default_treasury_id
            # Include risk_score if the column exists (migration 002); ignore if not.
            try:
                payload["risk_score"] = int(portfolio.get("risk_score", 0))
                self.db.table("treasury_snapshots").insert(payload).execute()
            except Exception:
                # Fall back without risk_score if column doesn't exist yet
                payload.pop("risk_score", None)
                self.db.table("treasury_snapshots").insert(payload).execute()
        except Exception as e:
            log.warning("portfolio_agent.persist_snapshot.failed", error=str(e))

    # ─── fallback ─────────────────────────────────────────────────────────────

    def _empty_positions(self) -> list[dict]:
        """Return empty positions when treasury address is not configured."""
        log.warning("portfolio_agent.no_treasury_address — returning empty")
        return []

    async def _broadcast_status(self, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        _update_state(self.NAME, status, "Portfolio monitoring", now)
        await broadcast("agent_status_update", {
            "name": self.NAME,
            "status": status,
            "last_action": "Portfolio monitoring",
            "last_action_at": now,
        })
