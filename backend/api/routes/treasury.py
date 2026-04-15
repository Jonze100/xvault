"""
Treasury API Routes

GET /api/treasury            — Full treasury overview
GET /api/treasury/pnl        — Historical PnL data points
GET /api/treasury/risk-heatmap — Protocol risk exposure
POST /api/treasury/rebalance — Trigger rebalance cycle
"""

from datetime import datetime, timezone, timedelta
from typing import Literal
import random
import uuid

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("")
async def get_treasury():
    """
    Return current treasury state.
    TODO: Fetch from Supabase treasury snapshot table (populated by Portfolio Agent).
    """
    # Placeholder — replace with real Supabase query
    return {
        "success": True,
        "data": {
            "id": str(uuid.uuid4()),
            "name": "XVault Treasury",
            "total_value_usd": 25_840.50,
            "total_pnl_24h_usd": 342.18,
            "total_pnl_24h_pct": 1.34,
            "total_pnl_7d_usd": 1_240.00,
            "total_pnl_all_time_usd": 3_420.00,
            "risk_score": 38,
            "last_rebalance": "2025-04-14T10:30:00Z",
            "performance_fees_collected_usd": 342.00,
            "assets": [
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "address": "0x0000000000000000000000000000000000000000",
                    "chain": "xlayer",
                    "balance": 3.2,
                    "price_usd": 3200.0,
                    "value_usd": 10_240.0,
                    "allocation_pct": 39.6,
                    "pnl_24h_pct": 2.3,
                    "pnl_24h_usd": 230.0,
                },
                {
                    "symbol": "USDC",
                    "name": "USD Coin",
                    "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "chain": "xlayer",
                    "balance": 8_500.0,
                    "price_usd": 1.0,
                    "value_usd": 8_500.0,
                    "allocation_pct": 32.9,
                    "pnl_24h_pct": 0.0,
                    "pnl_24h_usd": 0.0,
                },
                {
                    "symbol": "OKB",
                    "name": "OKB Token",
                    "address": "0x75231f58b43240c9718dd58b4967c5114342a86c",
                    "chain": "xlayer",
                    "balance": 150.0,
                    "price_usd": 45.0,
                    "value_usd": 6_750.0,
                    "allocation_pct": 26.1,
                    "pnl_24h_pct": 3.8,
                    "pnl_24h_usd": 247.5,
                },
                {
                    "symbol": "WBTC",
                    "name": "Wrapped Bitcoin",
                    "address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "chain": "xlayer",
                    "balance": 0.003,
                    "price_usd": 98_000.0,
                    "value_usd": 294.0,
                    "allocation_pct": 1.1,
                    "pnl_24h_pct": 1.1,
                    "pnl_24h_usd": 3.2,
                },
            ],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/pnl")
async def get_pnl_history(
    range: Literal["24h", "7d", "30d", "all"] = Query("24h"),
):
    """
    Return historical PnL data points for chart rendering.
    TODO: Query Supabase treasury_snapshots table.
    """
    now = datetime.now(timezone.utc)
    points = []

    if range == "24h":
        for i in range(48):
            t = now - timedelta(minutes=30 * (47 - i))
            base = 25_000 + random.uniform(-200, 200)
            points.append({
                "timestamp": t.isoformat(),
                "value_usd": base + i * 17,
                "pnl_usd": i * 17 - 100,
                "pnl_pct": (i * 17 - 100) / 25_000 * 100,
            })
    elif range == "7d":
        for i in range(7 * 24):
            t = now - timedelta(hours=(7*24 - i))
            base = 24_000 + random.uniform(-500, 500)
            points.append({
                "timestamp": t.isoformat(),
                "value_usd": base + i * 2.4,
                "pnl_usd": i * 2.4 - 500,
                "pnl_pct": (i * 2.4 - 500) / 24_000 * 100,
            })

    return {
        "success": True,
        "data": points,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/risk-heatmap")
async def get_risk_heatmap():
    """
    Return risk heatmap data: protocol exposure vs risk score.
    TODO: Aggregate from Supabase + real-time okx-security scores.
    """
    return {
        "success": True,
        "data": [
            {"protocol": "Stargate", "chain": "xlayer", "exposure_usd": 2000, "risk_score": 22, "audit_score": 90},
            {"protocol": "Aave",    "chain": "xlayer", "exposure_usd": 1500, "risk_score": 18, "audit_score": 95},
            {"protocol": "Curve",   "chain": "ethereum", "exposure_usd": 800, "risk_score": 15, "audit_score": 97},
            {"protocol": "GMX",     "chain": "xlayer", "exposure_usd": 1200, "risk_score": 45, "audit_score": 82},
            {"protocol": "Unknown", "chain": "xlayer", "exposure_usd": 400,  "risk_score": 78, "audit_score": 40},
            {"protocol": "Uniswap", "chain": "xlayer", "exposure_usd": 2200, "risk_score": 12, "audit_score": 98},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/rebalance")
async def trigger_rebalance():
    """
    Trigger a manual rebalance cycle via the orchestrator.
    TODO: Enqueue a run_cycle() call to the orchestrator.
    """
    return {
        "success": True,
        "data": {"job_id": str(uuid.uuid4()), "status": "queued"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
