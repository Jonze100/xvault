"""
Decisions API Routes

GET /api/decisions — Paginated decision log
"""

import uuid
from datetime import datetime, timezone, timedelta
import random

from fastapi import APIRouter, Query

router = APIRouter()

SAMPLE_DECISIONS = [
    {
        "id": str(uuid.uuid4()),
        "agent": "signal",
        "type": "signal_detected",
        "reasoning": "ETH showing strong momentum on okx-dex-signal with 73% confidence. Smart money inflows detected via okx-dex-trenches.",
        "confidence": 0.73,
        "data": {"token": "ETH", "action": "buy", "size_pct": 5.0},
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
        "tx_hash": None,
    },
    {
        "id": str(uuid.uuid4()),
        "agent": "risk",
        "type": "trade_approved",
        "reasoning": "ETH scored 88/100 on okx-security. Trail of Bits audit passed. No concentration issues.",
        "confidence": 0.95,
        "data": {"token": "ETH", "security_score": 88},
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1, seconds=45)).isoformat(),
        "tx_hash": None,
    },
    {
        "id": str(uuid.uuid4()),
        "agent": "execution",
        "type": "trade_executed",
        "reasoning": "Swapped 1000 USDC → 0.3125 ETH via okx-dex-swap on X Layer. Slippage: 0.3%",
        "confidence": 1.0,
        "data": {"from": "USDC", "to": "ETH", "amount": 1000},
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1, seconds=20)).isoformat(),
        "tx_hash": f"0x{uuid.uuid4().hex}",
    },
    {
        "id": str(uuid.uuid4()),
        "agent": "portfolio",
        "type": "position_opened",
        "reasoning": "ETH position updated. Portfolio now at 39.6% ETH, within 25% per-token limit.",
        "confidence": 1.0,
        "data": {"asset": "ETH", "new_allocation": 39.6},
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "tx_hash": None,
    },
    {
        "id": str(uuid.uuid4()),
        "agent": "economy",
        "type": "fee_collected",
        "reasoning": "Collected $34.20 performance fee (10%) on $342 profit via x402.",
        "confidence": 1.0,
        "data": {"fee_usd": 34.20, "profit_usd": 342.0},
        "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat(),
        "tx_hash": f"0x{uuid.uuid4().hex}",
    },
]


@router.get("")
async def get_decisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    agent: str | None = Query(None),
    limit: int | None = Query(None),
):
    """
    Paginated decision log from all agents.
    TODO: Query Supabase agent_logs table with ordering by timestamp DESC.
    """
    items = SAMPLE_DECISIONS
    if agent:
        items = [d for d in items if d["agent"] == agent]
    if limit:
        items = items[:limit]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return {
        "success": True,
        "data": {
            "items": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": end < total,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
