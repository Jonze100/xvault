"""
Economy API Routes

GET /api/economy/fees     — Performance fee history
GET /api/economy/earnings — Agent earnings breakdown
GET /api/economy/totals   — Lifetime totals
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/fees")
async def get_fees_history(limit: int = Query(20, ge=1, le=100)):
    """
    Recent performance fee collection events.
    TODO: Query Supabase performance_fees table.
    """
    fees = [
        {
            "id": str(uuid.uuid4()),
            "amount_usd": 34.20,
            "trigger_profit_usd": 342.0,
            "fee_pct": 10.0,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "distributions": [
                {"agent": "signal",    "amount_usd": 13.68, "pct": 40, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "risk",      "amount_usd": 10.26, "pct": 30, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "execution", "amount_usd": 6.84,  "pct": 20, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "portfolio", "amount_usd": 3.42,  "pct": 10, "tx_hash": f"0x{uuid.uuid4().hex}"},
            ],
        },
        {
            "id": str(uuid.uuid4()),
            "amount_usd": 82.50,
            "trigger_profit_usd": 825.0,
            "fee_pct": 10.0,
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            "distributions": [
                {"agent": "signal",    "amount_usd": 33.0,  "pct": 40, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "risk",      "amount_usd": 24.75, "pct": 30, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "execution", "amount_usd": 16.5,  "pct": 20, "tx_hash": f"0x{uuid.uuid4().hex}"},
                {"agent": "portfolio", "amount_usd": 8.25,  "pct": 10, "tx_hash": f"0x{uuid.uuid4().hex}"},
            ],
        },
    ]

    return {
        "success": True,
        "data": fees[:limit],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/earnings")
async def get_agent_earnings():
    """
    Lifetime earnings per agent from x402 fee distributions.
    TODO: Query Supabase agent_wallets table.
    """
    return {
        "success": True,
        "data": {
            "signal":    186.40,
            "risk":      139.80,
            "execution": 93.20,
            "portfolio": 46.60,
            "economy":   0.00,   # Economy collects, doesn't receive
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/totals")
async def get_totals():
    """Lifetime economy totals."""
    return {
        "success": True,
        "data": {
            "total_fees_usd": 466.00,
            "total_distributed_usd": 466.00,
            "fee_events": 12,
            "avg_fee_usd": 38.83,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
