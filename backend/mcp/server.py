"""
XVault MCP (Model Context Protocol) Client

Integrates with the OKX Onchain OS MCP server to call OKX-specific skills.
Each skill maps to a real HTTP endpoint on the MCP server. Agents call
self.mcp.call(skill_name, params) or the typed convenience methods below.

=============================================================================
OKX Onchain OS Skills Catalogue
=============================================================================

MARKET DATA & SIGNALS
  okx-dex-market    Real-time OHLCV prices, volume, liquidity for any token
                    on OKX X Layer and other supported chains.
                    Endpoint: POST /tools/okx-dex-market
                    Used by: Signal Agent

  okx-dex-signal    ML-generated directional trade signals (long/short + strength)
                    trained on order book data, on-chain flows, and price history.
                    Endpoint: POST /tools/okx-dex-signal
                    Used by: Signal Agent

  okx-dex-trenches  Mempool scanning, smart-money wallet tracking, social sentiment.
                    Detects whale movements and large pending transactions.
                    Endpoint: POST /tools/okx-dex-trenches
                    Used by: Signal Agent

  okx-dex-token     Token metadata: holder count, top wallets, contract details,
                    supply info, listing history.
                    Endpoint: POST /tools/okx-dex-token
                    Used by: Signal Agent (token due diligence)

SECURITY & AUDIT
  okx-security      Smart contract security scanner: rug-pull risk, honeypot
                    detection, ownership renouncement check, liquidity lock status,
                    mint authority, transfer pause capability.
                    Endpoint: POST /tools/okx-security
                    Used by: Risk Agent

  okx-audit-log     Protocol audit history from known firms (Trail of Bits, Certik,
                    OpenZeppelin, Consensys Diligence). Returns finding severity.
                    Endpoint: POST /tools/okx-audit-log
                    Used by: Risk Agent

EXECUTION
  okx-dex-swap      Execute on-chain token swaps via OKX DEX aggregator. Routes
                    across all liquidity sources for best execution price.
                    Endpoint: POST /tools/okx-dex-swap
                    Used by: Execution Agent

  okx-defi-invest   Deploy funds into DeFi yield strategies: lending pools (Aave,
                    Compound), LP positions (Uniswap V3, Curve), staking vaults.
                    Endpoint: POST /tools/okx-defi-invest
                    Used by: Execution Agent

  okx-onchain-gateway  Cross-chain bridging. Supports xlayer ↔ ethereum ↔ bsc
                    ↔ polygon ↔ arbitrum ↔ optimism. Unified bridge interface.
                    Endpoint: POST /tools/okx-onchain-gateway
                    Used by: Execution Agent

PORTFOLIO MONITORING
  okx-wallet-portfolio  Aggregate all token balances in a wallet address across
                    multiple chains. Returns balances with USD prices embedded.
                    Endpoint: POST /tools/okx-wallet-portfolio
                    Used by: Portfolio Agent

  okx-defi-portfolio  Enumerate active DeFi positions: LP shares, lending deposits,
                    staked tokens, vault receipts, with current APYs and rewards.
                    Endpoint: POST /tools/okx-defi-portfolio
                    Used by: Portfolio Agent

  okx-agentic-wallet  Manage agentic wallet operations: top up gas, check ERC20
                    allowances, rotate keys, set spending limits.
                    Endpoint: POST /tools/okx-agentic-wallet
                    Used by: Portfolio Agent (wallet management)

PAYMENTS
  x402             HTTP 402 Payment Required micropayment protocol for autonomous
                    machine-to-machine payments. Used for performance fee collection
                    and distribution to agent wallets.
                    Endpoint: POST /tools/x402
                    Used by: Economy Agent
                    Actions: collect | pay | balance | history

=============================================================================
MCP Transport
=============================================================================
The MCP server exposes all skills as HTTP POST endpoints at /tools/{skill_name}.
Authentication: Bearer token in Authorization header (settings.mcp_api_key).
Retry: exponential backoff via tenacity (3 attempts, 2-10s delay).
Timeout: 30 seconds per call.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger(__name__)


class MCPClient:
    """
    HTTP client for the OKX Onchain OS MCP server.

    The MCP server runs locally (or remotely) and exposes OKX blockchain
    skills as HTTP endpoints. Claude agents call these skills via tool_use.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def call(self, skill: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Call an OKX MCP skill by name.

        Args:
            skill: Skill name e.g. "okx-dex-swap", "x402"
            params: Skill-specific parameters (see skill docstrings below)

        Returns:
            Skill response as dict

        Raises:
            httpx.HTTPError: On network/server error (retried automatically)

        Example:
            result = await mcp.call("okx-dex-swap", {
                "from_token": "USDC",
                "to_token": "ETH",
                "amount": 1000.0,
                "slippage": 0.005,
                "chain": "xlayer",
                "wallet_private_key": "0x...",
            })
        """
        url = f"{self.base_url}/tools/{skill}"
        log.info("mcp.call", skill=skill, params_keys=list(params.keys()))

        response = await self._client.post(url, json=params)
        response.raise_for_status()

        result = response.json()
        log.info("mcp.call.success", skill=skill)
        return result

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List all available MCP tools/skills from the server.
        Used for Claude tool_use registration.
        """
        response = await self._client.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()

    async def health(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            response = await self._client.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    # =========================================================================
    # Skill-Specific Convenience Methods
    # Each wraps call() with typed parameters and documents the full API shape.
    # =========================================================================

    async def dex_market(
        self,
        tokens: list[str],
        chain: str = "xlayer",
        interval: str = "5m",
        limit: int = 100,
    ) -> dict:
        """
        Skill: okx-dex-market
        Real-time price feeds and OHLCV candle data.

        Params:
          tokens   — list of token symbols e.g. ["ETH", "OKB", "USDC"]
          chain    — target chain (xlayer | ethereum | bsc)
          interval — candle interval: 1m | 5m | 15m | 1h | 4h | 1d
          limit    — number of candles per token (max 500)

        Response keys per token: price, open, high, low, close, volume_24h,
          change_24h, liquidity_usd, candles[]
        """
        return await self.call("okx-dex-market", {
            "tokens": tokens,
            "chain": chain,
            "interval": interval,
            "limit": limit,
        })

    async def dex_signal(
        self,
        market_data: dict,
        strategy: str = "momentum",
        min_confidence: float = 0.6,
    ) -> dict:
        """
        Skill: okx-dex-signal
        ML-generated trade signals.

        Params:
          market_data     — output of dex_market() (pass through directly)
          strategy        — momentum | mean_reversion | breakout | combined
          min_confidence  — filter threshold 0.0–1.0

        Response: { signals: [{ token, direction, strength, factors, expires_at }] }
        """
        return await self.call("okx-dex-signal", {
            "market_data": market_data,
            "strategy": strategy,
            "min_confidence": min_confidence,
        })

    async def dex_trenches(
        self,
        tokens: list[str],
        lookback_hours: int = 1,
        include_whale_wallets: bool = True,
    ) -> dict:
        """
        Skill: okx-dex-trenches
        Mempool and social sentiment scanning.

        Params:
          tokens                — tokens to monitor
          lookback_hours        — time window for activity scan
          include_whale_wallets — track wallets with > $1M holdings

        Response per token: sentiment_score (0–1), smart_money_flow
          (inflow|outflow|neutral), whale_buys, whale_sells,
          mempool_large_pending, social_mentions_delta
        """
        return await self.call("okx-dex-trenches", {
            "tokens": tokens,
            "lookback_hours": lookback_hours,
            "include_whale_wallets": include_whale_wallets,
        })

    async def dex_token(self, token: str, chain: str = "xlayer") -> dict:
        """
        Skill: okx-dex-token
        Token metadata and fundamentals.

        Response: name, symbol, contract, total_supply, holder_count,
          top_holders[], market_cap, listing_exchanges[], description
        """
        return await self.call("okx-dex-token", {"token": token, "chain": chain})

    async def security_score(
        self,
        token: str,
        chain: str = "xlayer",
        checks: list[str] | None = None,
    ) -> dict:
        """
        Skill: okx-security
        Smart contract security scoring.

        Params:
          checks — subset of: rug_pull, honeypot, ownership, liquidity_lock,
                   code_audit, transfer_pausable, mint_authority

        Response: score (0–100), flags[], is_verified, liquidity_locked,
          ownership_renounced, can_mint, honeypot_risk, rug_pull_risk
        """
        return await self.call("okx-security", {
            "token": token,
            "chain": chain,
            "checks": checks or [
                "rug_pull", "honeypot", "ownership",
                "liquidity_lock", "code_audit", "mint_authority",
            ],
        })

    async def audit_log(self, token: str, chain: str = "xlayer") -> dict:
        """
        Skill: okx-audit-log
        Protocol audit history and findings.

        Response: audited, audit_firms[], last_audit_date, audits[],
          critical_issues (unresolved), high_issues, report_url
        """
        return await self.call("okx-audit-log", {"token": token, "chain": chain})

    async def dex_swap(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        slippage: float = 0.005,
        chain: str = "xlayer",
        wallet_key: str = "",
        deadline_seconds: int = 300,
    ) -> dict:
        """
        Skill: okx-dex-swap
        Execute on-chain token swap via OKX DEX aggregator.

        Params:
          from_token       — source token symbol or address
          to_token         — destination token symbol or address
          amount           — amount in from_token units
          slippage         — max acceptable slippage (0.005 = 0.5%)
          chain            — execution chain
          wallet_key       — private key of execution wallet
          deadline_seconds — transaction deadline (seconds from now)

        Response: success, tx_hash, amount_in, amount_out, price,
          price_impact, gas_usd, slippage_actual, route[], block_number
        """
        return await self.call("okx-dex-swap", {
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "slippage": slippage,
            "chain": chain,
            "wallet_private_key": wallet_key,
            "deadline_seconds": deadline_seconds,
        })

    async def defi_invest(
        self,
        token: str,
        amount_usd: float,
        protocol: str,
        chain: str = "xlayer",
        wallet_key: str = "",
        position_type: str = "lending",
    ) -> dict:
        """
        Skill: okx-defi-invest
        Deploy funds to DeFi yield strategies.

        Params:
          token         — token to deposit
          amount_usd    — amount in USD
          protocol      — aave_v3 | uniswap_v3 | curve | stargate | compound
          position_type — lending | lp | staking | vault

        Response: success, tx_hash, protocol, amount_deposited, shares_received,
          apy_current, gas_usd, position_id
        """
        return await self.call("okx-defi-invest", {
            "token": token,
            "amount_usd": amount_usd,
            "protocol": protocol,
            "chain": chain,
            "wallet_private_key": wallet_key,
            "position_type": position_type,
        })

    async def onchain_gateway(
        self,
        from_chain: str,
        to_chain: str,
        token: str,
        amount: float,
        wallet_key: str = "",
    ) -> dict:
        """
        Skill: okx-onchain-gateway
        Cross-chain bridging via OKX unified bridge.

        Supported routes include: xlayer ↔ ethereum ↔ bsc ↔ polygon
          ↔ arbitrum ↔ optimism ↔ base

        Response: success, source_tx_hash, destination_tx_hash (when finalized),
          amount_received, bridge_fee_usd, estimated_time_seconds
        """
        return await self.call("okx-onchain-gateway", {
            "from_chain": from_chain,
            "to_chain": to_chain,
            "token": token,
            "amount": amount,
            "wallet_private_key": wallet_key,
        })

    async def wallet_portfolio(
        self,
        address: str,
        chains: list[str] | None = None,
        hide_dust: bool = True,
    ) -> dict:
        """
        Skill: okx-wallet-portfolio
        Aggregate wallet token balances across chains.

        Response: total_usd, positions[{ symbol, chain, balance, price_usd,
          value_usd, contract, logo }]
        """
        return await self.call("okx-wallet-portfolio", {
            "address": address,
            "chains": chains or ["xlayer"],
            "include_prices": True,
            "hide_dust": hide_dust,
        })

    async def defi_portfolio(
        self,
        address: str,
        chains: list[str] | None = None,
    ) -> dict:
        """
        Skill: okx-defi-portfolio
        DeFi positions — LP shares, staking, lending, vault receipts.

        Response: total_usd, positions[{ protocol, type, token_a, token_b,
          value_usd, apy, rewards_usd, health_factor, position_id }]
        """
        return await self.call("okx-defi-portfolio", {
            "address": address,
            "chains": chains or ["xlayer"],
        })

    async def agentic_wallet(self, action: str, **kwargs: Any) -> dict:
        """
        Skill: okx-agentic-wallet
        Agentic wallet management operations.

        Actions:
          balance     — get wallet ETH + ERC20 balances
          approve     — set ERC20 allowance for a spender
          topup_gas   — bridge ETH from another chain to cover gas
          rotate_key  — rotate the agent's private key (security)
          set_limit   — configure daily spending limit

        Example: await mcp.agentic_wallet("balance", address="0x...")
        """
        return await self.call("okx-agentic-wallet", {"action": action, **kwargs})

    async def x402_pay(
        self,
        from_key: str,
        to_address: str,
        amount_usd: float,
        memo: str = "",
        token: str = "USDC",
        network: str = "xlayer",
    ) -> dict:
        """
        Skill: x402
        HTTP 402 Payment Required micropayment protocol.

        x402 enables autonomous machine-to-machine payments without
        human confirmation. Used for agent earnings distribution and
        premium service purchases.

        Actions: pay | collect | balance | history

        Params (action=pay):
          from_key    — sender private key (agentic wallet)
          to_address  — recipient wallet address
          amount_usd  — payment amount in USD
          memo        — payment description (logged on-chain)
          token       — settlement token (USDC default)
          network     — xlayer | ethereum | base

        Response: success, tx_hash, amount_usd, amount_token, from, to,
          payment_id, network, timestamp
        """
        return await self.call("x402", {
            "action": "pay",
            "from_private_key": from_key,
            "to_address": to_address,
            "amount_usd": amount_usd,
            "memo": memo,
            "token": token,
            "network": network,
        })
