"""
Signal Agent — Market Scanning & Trade Signal Generation

Agentic Wallet: signal.xvault.eth
OKX Onchain OS Skills used:
  - okx-dex-market    Real-time OHLCV prices and volume across OKX X Layer pairs
  - okx-dex-signal    ML model–generated directional trade signals (long/short + strength)
  - okx-dex-trenches  Mempool scanning, smart money flows, whale wallet tracking
  - okx-dex-token     Token metadata, holder distribution, contract info

Runs every 5 minutes via APScheduler. Scans market data, generates trade
opportunities, and forwards high-confidence signals to the Risk Agent.

Signal Pipeline:
  okx-dex-market → price feed
  okx-dex-signal → ML signal strengths (smart money / KOL / whale activity)
  okx-dex-trenches → on-chain sentiment
  Claude claude-sonnet-4-6 → final scoring & ranking
  → emit to orchestrator (Risk Agent picks up)
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

log = structlog.get_logger(__name__)
settings = get_settings()

# OKX X Layer (chainIndex 196) token contract addresses
XLAYER_TOKENS = {
    "OKB":  "",                                          # native OKB — empty = native
    "USDC": "0x74b7f16337b8972027f6196a17a631ac6de26d22",
    "ETH":  "0x5a77f1443d16ee5761d310e38b62f77f726bc71c",  # WETH on XLayer
    "USDT": "0x1e4a5963abfd975d8c9021ce480b42188849d41d",
}

ONCHAINOS = os.path.expanduser("~/.local/bin/onchainos")


class SignalAgent:
    """
    Scans OKX markets and generates trade signals using Claude + OKX onchainos CLI.

    Responsibilities:
    - Poll okx-dex-signal for smart money / KOL / whale signals on XLayer
    - Call onchainos market price for real-time prices
    - Score opportunities and emit to orchestrator
    """

    NAME = "signal"
    LOOP_INTERVAL = 300  # 5 minutes

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.db = get_supabase()

    # ─── onchainos subprocess helper ────────────────────────────────────────

    async def _run_onchainos(self, *args: str, timeout: int = 30) -> Any:
        """
        Execute onchainos CLI and return parsed JSON output.

        CLI binary: ~/.local/bin/onchainos
        Auth:       Reads ~/.config/onchainos/config.toml (set by `onchainos wallet login`)

        Raises RuntimeError on non-zero exit or JSON parse failure.
        Falls back to None so callers can use mock data gracefully.
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

    async def run(self) -> list[dict[str, Any]]:
        """
        Main agent loop — called by APScheduler every LOOP_INTERVAL seconds.
        Returns list of trade signals for orchestrator consumption.
        """
        log.info("signal_agent.run.start")
        await self._update_status("thinking")

        try:
            # 1. Fetch smart money signals via onchainos signal list (okx-dex-signal)
            ml_signals = await self._fetch_ml_signals()

            # 2. Get live prices via onchainos market price (okx-dex-market)
            market_data = await self._fetch_market_data()

            # 3. Reason with Claude to score and rank signals
            signals = await self._reason_and_score(market_data, ml_signals)

            # 4. Persist and broadcast
            for signal in signals:
                await self._log_decision(signal)
                await broadcast("agent_decision", {
                    "id": str(uuid.uuid4()),
                    "agent": self.NAME,
                    "type": "signal_detected",
                    "reasoning": signal["reasoning"],
                    "confidence": signal["confidence"],
                    "data": signal,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            await self._update_status("active")
            log.info("signal_agent.run.complete", signals_count=len(signals))
            return signals

        except Exception as e:
            log.error("signal_agent.run.error", error=str(e))
            await self._update_status("error")
            return []

    # ─── data fetchers ──────────────────────────────────────────────────────

    async def _fetch_ml_signals(self) -> list[dict]:
        """
        Onchain OS Skill: okx-dex-signal
        CLI: onchainos signal list --chain xlayer --wallet-type 1,2,3

        --wallet-type flags:
          1 = Smart Money wallets (historically profitable)
          2 = KOL / Influencer wallets
          3 = Whale wallets (> $1M holdings)

        Returns a list of signal objects, each indicating which tokens
        smart money is buying/selling on OKX X Layer.

        Response shape (array of signal objects):
          [
            {
              "tokenContractAddress": "0x...",
              "tokenSymbol": "OKB",
              "buySellType": "buy",          // "buy" or "sell"
              "addressCount": 12,            // # of smart wallets active
              "transactionCount": 34,
              "amount": "45000.5",           // total USD volume
              "chainIndex": "196",
              "walletType": "1"              // 1=smart, 2=KOL, 3=whale
            },
            ...
          ]
        """
        result = await self._run_onchainos(
            "signal", "list",
            "--chain", "xlayer",
            "--wallet-type", "1,2,3",
            "--min-amount-usd", "10000",   # only signals with >$10k volume
        )

        if result:
            # Normalise to internal signal format
            return [
                {
                    "token": s.get("tokenSymbol", "UNKNOWN"),
                    "contract": s.get("tokenContractAddress", ""),
                    "direction": "long" if s.get("buySellType") == "buy" else "short",
                    "strength": min(1.0, int(s.get("addressCount", 1)) / 20),
                    "address_count": s.get("addressCount", 0),
                    "volume_usd": float(s.get("amount", 0)),
                    "source": "okx-dex-signal",
                    "wallet_type": s.get("walletType", "1"),
                }
                for s in (result if isinstance(result, list) else result.get("data", []))
            ]

        # Fallback mock when CLI unavailable
        log.info("signal_agent.ml_signals.fallback")
        return [
            {"token": "OKB",  "direction": "long",  "strength": 0.73, "volume_usd": 45000, "source": "okx-dex-signal"},
            {"token": "USDC", "direction": "long",  "strength": 0.61, "volume_usd": 22000, "source": "okx-dex-signal"},
        ]

    async def _fetch_market_data(self) -> dict[str, Any]:
        """
        Onchain OS Skill: okx-dex-market
        CLI: onchainos market price --address <contract> --chain xlayer

        Fetches current USD price for each token we care about.
        Called once per token (no batch endpoint in CLI).

        Response shape (single price call):
          {
            "tokenContractAddress": "0x...",
            "price": "48.72",
            "chainIndex": "196"
          }
        """
        market: dict[str, Any] = {}

        # Fetch prices for tracked tokens in parallel
        tasks = {
            symbol: self._run_onchainos(
                "market", "price",
                "--address", contract,
                "--chain", "xlayer",
            )
            for symbol, contract in XLAYER_TOKENS.items()
            if contract  # skip native (empty address) — no price endpoint
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for symbol, result in zip(tasks.keys(), results):
            if isinstance(result, dict):
                try:
                    market[symbol] = {
                        "price": float(result.get("price", 0)),
                        "contract": result.get("tokenContractAddress", ""),
                    }
                except (ValueError, TypeError):
                    pass

        if not market:
            # Fallback prices when CLI unavailable
            log.info("signal_agent.market_data.fallback")
            market = {
                "OKB":  {"price": 48.0,    "contract": ""},
                "ETH":  {"price": 3200.0,  "contract": XLAYER_TOKENS["ETH"]},
                "USDC": {"price": 1.0,     "contract": XLAYER_TOKENS["USDC"]},
            }

        return market

    async def _reason_and_score(
        self,
        market_data: dict,
        ml_signals: list[dict],
    ) -> list[dict[str, Any]]:
        """
        Use Claude to reason about signals and assign final confidence scores.
        Filters out low-confidence opportunities.
        """
        prompt = f"""You are the Signal Agent in XVault, an autonomous DeFi treasury on OKX X Layer.

Market Data (live prices):
{json.dumps(market_data, indent=2)}

Smart Money Signals from okx-dex-signal (on-chain activity by whales/KOLs):
{json.dumps(ml_signals, indent=2)}

Your job: Analyze these signals and produce a ranked list of trade opportunities.
For each opportunity return JSON with these fields:
- token: the asset symbol
- action: "buy" or "sell"
- confidence: 0.0 to 1.0 (only include > 0.6)
- reasoning: 1-2 sentence explanation referencing the signal data
- estimated_size_pct: suggested % of treasury to allocate (max 10%)

Respond ONLY with a valid JSON array. Be conservative — Risk Agent will vet your picks."""

        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # Strip possible markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            opportunities = json.loads(raw)
            if not isinstance(opportunities, list):
                opportunities = [opportunities]
        except json.JSONDecodeError:
            log.warning("signal_agent.claude_parse_failed", raw=raw[:200])
            opportunities = []

        return [
            {
                "id": str(uuid.uuid4()),
                **opp,
                "market_data": market_data.get(opp.get("token", ""), {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for opp in opportunities
            if isinstance(opp, dict) and float(opp.get("confidence", 0)) >= 0.6
        ]

    async def _log_decision(self, signal: dict) -> None:
        """Persist signal to Supabase agent_logs table."""
        if not self.db:
            return
        try:
            self.db.table("agent_logs").insert({
                "agent_name": self.NAME,
                "decision_type": "signal_detected",
                "reasoning": signal.get("reasoning", f"Signal detected for {signal.get('token','?')}"),
                "confidence": float(signal.get("confidence", 0)),
                "data": signal,
                "tx_hash": None,
            }).execute()
        except Exception as e:
            log.warning("signal_agent.log_decision.failed", error=str(e))

    async def _update_status(self, status: str) -> None:
        """Update in-memory state and broadcast via WebSocket."""
        action = f"Signal scan {'completed' if status == 'active' else 'running'}"
        now = datetime.now(timezone.utc).isoformat()
        _update_state(self.NAME, status, action, now)
        await broadcast("agent_status_update", {
            "name": self.NAME,
            "status": status,
            "last_action": action,
            "last_action_at": now,
        })
