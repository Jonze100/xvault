"""
Execution Agent — Trade Execution & DeFi Deployment

Agentic Wallet: execution.xvault.eth
OKX Onchain OS Skills used:
  - okx-dex-swap          Execute on-chain token swaps via OKX DEX aggregator
                          (routes across all liquidity sources for best price)
  - okx-defi-invest       Deploy funds into yield-bearing DeFi positions
                          (lending pools, LP positions, staking vaults)
  - okx-onchain-gateway   Cross-chain bridging via OKX's unified bridge
                          (supports xlayer ↔ ethereum ↔ bsc ↔ polygon etc.)

On-demand: receives approved signals from Risk Agent.
Executes swaps, LP deposits, yield farming positions on OKX X Layer.

Execution Pipeline:
  Approved signal → Claude strategy planning
  → okx-dex-swap (for direct swaps) OR okx-defi-invest (for yield)
  → okx-onchain-gateway (if cross-chain) → record tx → notify Portfolio Agent
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
from api.state import update_agent_status as _update_state, increment_decisions
import api.state as _state

log = structlog.get_logger(__name__)
settings = get_settings()

ONCHAINOS = os.path.expanduser("~/.local/bin/onchainos")

# Token contract addresses on OKX X Layer (chainIndex 196)
XLAYER_USDC = "0x74b7f16337b8972027f6196a17a631ac6de26d22"
XLAYER_TOKENS = {
    "OKB":  "",                                           # native
    "USDC": XLAYER_USDC,
    "ETH":  "0x5a77f1443d16ee5761d310e38b62f77f726bc71c",  # WETH
    "USDT": "0x1e4a5963abfd975d8c9021ce480b42188849d41d",
}


class ExecutionAgent:
    """
    Executes approved trades on OKX X Layer using onchainos CLI.

    Responsibilities:
    - Execute token swaps via onchainos swap execute (okx-dex-swap)
    - Deploy funds to yield strategies via onchainos defi (okx-defi-invest)
    - Handle cross-chain bridging via onchainos gateway (okx-onchain-gateway)
    - Report execution results back to Portfolio Agent
    """

    NAME = "execution"

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.db = get_supabase()

    # ─── onchainos subprocess helper ────────────────────────────────────────

    async def _run_onchainos(self, *args: str, timeout: int = 60) -> Any:
        """
        Execute onchainos CLI and return parsed JSON output.
        Swap/invest operations get a longer timeout (60s) due to on-chain signing.
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

    # ─── main entry ─────────────────────────────────────────────────────────

    async def execute(
        self,
        signal: dict[str, Any],
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute an approved trade signal.

        Args:
            signal: From SignalAgent — includes token, action, size
            assessment: From RiskAgent — includes max_size_usd, adjusted_size_pct

        Returns:
            Execution result with tx_hash, actual amounts, gas used
        """
        log.info("execution_agent.execute.start", token=signal["token"])
        await self._broadcast_status("thinking")

        # Notify war room
        await broadcast("agent_message", {
            "id": str(uuid.uuid4()),
            "from_agent": "risk",
            "to_agent": self.NAME,
            "content": f"Approved signal for {signal['token']} — execute {signal['action']}",
            "type": "request",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        try:
            # Determine execution strategy
            strategy = await self._plan_execution(signal, assessment)

            result: dict[str, Any]
            if strategy["type"] == "swap":
                result = await self._execute_swap(signal, assessment, strategy)
            elif strategy["type"] == "invest":
                result = await self._execute_defi_invest(signal, assessment, strategy)
            else:
                result = {"success": False, "error": "Unknown strategy type"}

            # Persist transaction to DB
            if result.get("success"):
                await self._record_transaction(signal, result)
                increment_decisions(self.NAME)

                await broadcast("agent_decision", {
                    "id": str(uuid.uuid4()),
                    "agent": self.NAME,
                    "type": "trade_executed",
                    "reasoning": (
                        f"Executed {signal['action']} {signal['token']}: "
                        f"{result.get('amount_out', 0):.4f} received"
                    ),
                    "confidence": 1.0,
                    "data": result,
                    "tx_hash": result.get("tx_hash"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            await self._broadcast_status("active")
            return result

        except Exception as e:
            log.error("execution_agent.execute.error", error=str(e))
            await self._broadcast_status("error")
            return {"success": False, "error": str(e)}

    # ─── strategy planning ──────────────────────────────────────────────────

    async def _plan_execution(
        self, signal: dict, assessment: dict
    ) -> dict[str, Any]:
        """
        Use Claude to decide the best execution strategy for this signal.
        Chooses between direct swap and DeFi invest.
        """
        prompt = f"""You are the Execution Agent in XVault DeFi treasury on OKX X Layer.

Signal: {json.dumps(signal)}
Risk Assessment: {json.dumps(assessment)}

Available strategies:
1. "swap" — direct token swap via okx-dex-swap (best for liquid pairs, immediate exposure)
2. "invest" — deploy to DeFi yield strategy via okx-defi-invest (better for size, earn yield)

Choose the optimal strategy. For amounts < $5,000 prefer "swap". For amounts > $5,000 with stable tokens prefer "invest".

Respond ONLY with valid JSON:
{{
  "type": "swap" or "invest",
  "reasoning": "one sentence",
  "target_protocol": "okx_dex" or "aave_v3" or "stargate",
  "slippage_tolerance": 0.005
}}"""

        from agents.spend_tracker import is_budget_exceeded, record_usage
        if is_budget_exceeded():
            return {
                "type": "swap",
                "reasoning": "Budget cap reached — defaulting to swap",
                "target_protocol": "okx_dex",
                "slippage_tolerance": 0.005,
            }

        response = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        record_usage(response.usage.input_tokens, response.usage.output_tokens)

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "type": "swap",
                "reasoning": "Default to swap for simplicity",
                "target_protocol": "okx_dex",
                "slippage_tolerance": 0.005,
            }

    # ─── execution methods ──────────────────────────────────────────────────

    async def _execute_swap(
        self, signal: dict, assessment: dict, strategy: dict
    ) -> dict[str, Any]:
        """
        Onchain OS Skill: okx-dex-swap
        CLI: onchainos swap execute --from <contractAddr> --to <contractAddr>
                                    --readable-amount <amount>
                                    --chain xlayer
                                    --wallet <treasuryWalletAddress>
                                    --slippage <pct>

        --from / --to:         token contract addresses on XLayer (196)
                               Use the token's contract address; empty = native OKB
        --readable-amount:     Human-readable units (e.g. "100" for 100 USDC).
                               CLI resolves decimals automatically.
        --wallet:              The wallet that will sign and pay gas.
                               Must have been registered via `onchainos wallet login`.
        --slippage:            Slippage tolerance as a percent string (e.g. "0.5" = 0.5%).
                               Omit to use OKX auto-slippage.

        Response shape:
          {
            "txHash": "0xabc123...",
            "fromToken": { "symbol": "USDC", "contractAddress": "0x..." },
            "toToken":   { "symbol": "OKB",  "contractAddress": "" },
            "amountIn":  "100",        // human-readable input
            "amountOut": "2.05",       // human-readable output
            "priceImpact": "0.12",     // percent
            "gasUsed":   "185000",
            "chain":     "xlayer"
          }
        """
        token = signal["token"]
        amount_usd = assessment.get("max_size_usd", 1000)
        to_contract = XLAYER_TOKENS.get(token, "")
        slippage = str(strategy.get("slippage_tolerance", 0.005) * 100)  # percent

        # Readable amount: we're spending USDC (1:1 with USD)
        readable_amount = str(round(amount_usd, 2))

        log.info(
            "execution_agent.swap",
            token=token,
            amount_usd=amount_usd,
            to_contract=to_contract,
        )

        # Use agentic wallet (logged in via onchainos wallet login) for execution
        wallet_addr = _state.get_active_wallet() or settings.execution_agent_wallet_address or settings.treasury_wallet_address
        if not wallet_addr:
            log.warning("execution_agent.swap.no_wallet_configured")
            return self._mock_swap_result(signal, assessment)

        result = await self._run_onchainos(
            "swap", "execute",
            "--from", XLAYER_USDC,
            "--to", to_contract or "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "--readable-amount", readable_amount,
            "--chain", "xlayer",
            "--wallet", wallet_addr,
            "--slippage", slippage,
        )

        if result:
            # Real API shape: { "ok": true, "data": { "txHash": ..., ... } }
            data = result.get("data", result) if isinstance(result, dict) else result
            if isinstance(data, dict):
                return {
                    "success": True,
                    "type": "swap",
                    "tx_hash": data.get("txHash", ""),
                    "from_token": data.get("fromToken", {}).get("symbol", "USDC") if isinstance(data.get("fromToken"), dict) else "USDC",
                    "to_token": data.get("toToken", {}).get("symbol", token) if isinstance(data.get("toToken"), dict) else token,
                    "amount_in": float(data.get("amountIn", 0)),
                    "amount_out": float(data.get("amountOut", 0)),
                    "price_impact": float(data.get("priceImpact", 0)),
                    "gas_used": data.get("gasUsed", ""),
                    "chain": "xlayer",
                }

        log.warning("execution_agent.swap.fallback_result", token=token)
        return self._mock_swap_result(signal, assessment)

    async def _execute_defi_invest(
        self, signal: dict, assessment: dict, strategy: dict
    ) -> dict[str, Any]:
        """
        Onchain OS Skill: okx-defi-invest
        CLI: onchainos defi search --token <symbol> --chain xlayer
             → returns investmentId for best yield opportunity
             Then: onchainos defi invest --investment-id <id>
                                         --amount <readable_amount>
                                         --wallet <address>

        defi search response shape:
          [
            {
              "investmentId": "aave-v3-usdc-xlayer",
              "platform": "Aave V3",
              "apy": "8.42",           // percent string
              "tvl": "12500000",       // USD
              "token": "USDC",
              "chain": "xlayer"
            },
            ...
          ]

        defi invest (deposit) response shape:
          {
            "txHash": "0xdef456...",
            "platform": "Aave V3",
            "token": "USDC",
            "amountDeposited": "10000",
            "sharesReceived": "9998.5",
            "apy": "8.42",
            "chain": "xlayer"
          }
        """
        token = signal["token"]
        amount_usd = assessment.get("max_size_usd", 1000)

        log.info("execution_agent.defi_invest", token=token, amount_usd=amount_usd)

        wallet_addr = _state.get_active_wallet() or settings.execution_agent_wallet_address or settings.treasury_wallet_address
        if not wallet_addr:
            log.warning("execution_agent.defi_invest.no_wallet_configured")
            return self._mock_invest_result(signal, assessment, strategy)

        # 1. Find best yield opportunity
        search_result = await self._run_onchainos(
            "defi", "search",
            "--token", token,
            "--chain", "xlayer",
        )

        best_opportunity = None
        if search_result:
            opportunities = search_result if isinstance(search_result, list) else search_result.get("data", [])
            if opportunities:
                # Pick highest APY
                best_opportunity = max(
                    opportunities,
                    key=lambda x: float(x.get("apy", 0)),
                )

        if not best_opportunity:
            log.warning("execution_agent.defi_invest.no_opportunities", token=token)
            return self._mock_invest_result(signal, assessment, strategy)

        # 2. Execute the investment
        invest_result = await self._run_onchainos(
            "defi", "invest",
            "--investment-id", best_opportunity["investmentId"],
            "--amount", str(round(amount_usd, 2)),
            "--wallet", wallet_addr,
        )

        if invest_result:
            return {
                "success": True,
                "type": "invest",
                "tx_hash": invest_result.get("txHash", ""),
                "protocol": invest_result.get("platform", strategy.get("target_protocol")),
                "amount_deposited": float(invest_result.get("amountDeposited", 0)),
                "apy_estimate": float(invest_result.get("apy", 0)) / 100,
                "chain": "xlayer",
            }

        return self._mock_invest_result(signal, assessment, strategy)

    # ─── helpers ────────────────────────────────────────────────────────────

    def _mock_swap_result(self, signal: dict, assessment: dict) -> dict[str, Any]:
        """Return a FAILED result when CLI is unavailable — never fake success."""
        log.error("execution_agent.swap.REAL_CLI_FAILED", token=signal["token"])
        return {
            "success": False,
            "type": "swap",
            "error": "onchainos CLI swap failed — no real transaction executed",
            "simulated": True,
            "from_token": "USDC",
            "to_token": signal["token"],
            "chain": "xlayer",
        }

    def _mock_invest_result(
        self, signal: dict, assessment: dict, strategy: dict
    ) -> dict[str, Any]:
        """Return a FAILED result when CLI is unavailable — never fake success."""
        log.error("execution_agent.invest.REAL_CLI_FAILED", token=signal["token"])
        return {
            "success": False,
            "type": "invest",
            "error": "onchainos CLI defi invest failed — no real transaction executed",
            "simulated": True,
            "chain": "xlayer",
        }

    async def _record_transaction(self, signal: dict, result: dict) -> None:
        """Persist executed transaction to Supabase transactions table.
        Only records transactions with real tx hashes (64 hex chars after 0x prefix)."""
        if not self.db:
            return
        tx_hash = result.get("tx_hash", "")
        # Reject fake/empty tx hashes — real hashes are 66 chars (0x + 64 hex)
        if not tx_hash or len(tx_hash.replace("0x", "")) < 64:
            log.warning("execution_agent.record_tx.skipped_fake_hash", tx_hash=tx_hash)
            return
        try:
            token = signal.get("token", "UNKNOWN")
            amount_in = float(result.get("amount_in", 0))
            amount_out = float(result.get("amount_out", 0))
            row: dict = {
                "agent_name": self.NAME,
                "type": result.get("type", "swap"),
                "status": "confirmed",
                "from_token": "USDC",
                "to_token": token,
                "amount_in": amount_in,
                "amount_out": amount_out,
                "value_usd": amount_in,
                "tx_hash": tx_hash,
                "chain": "xlayer",
            }
            if _state.default_treasury_id:
                row["treasury_id"] = _state.default_treasury_id
            self.db.table("transactions").insert(row).execute()
        except Exception as e:
            log.warning("execution_agent.record_tx.failed", error=str(e))

    async def _broadcast_status(self, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        _update_state(self.NAME, status, "Trade execution", now)
        await broadcast("agent_status_update", {
            "name": self.NAME,
            "status": status,
            "last_action": "Trade execution",
            "last_action_at": now,
        })
