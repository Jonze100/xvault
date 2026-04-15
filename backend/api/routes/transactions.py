"""
Transactions API Routes

GET /api/transactions      — Paginated transaction history
GET /api/transactions/{hash} — Single transaction
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, HTTPException

router = APIRouter()

SAMPLE_TRANSACTIONS = [
    {
        "id": str(uuid.uuid4()),
        "type": "swap",
        "status": "confirmed",
        "from_token": "USDC",
        "to_token": "ETH",
        "amount_in": 1000.0,
        "amount_out": 0.3125,
        "value_usd": 1000.0,
        "tx_hash": f"0x{uuid.uuid4().hex}",
        "chain": "xlayer",
        "gas_usd": 0.23,
        "slippage_pct": 0.003,
        "agent": "execution",
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "block_number": 12_345_678,
    },
    {
        "id": str(uuid.uuid4()),
        "type": "fee",
        "status": "confirmed",
        "from_token": "USDC",
        "to_token": "USDC",
        "amount_in": 34.20,
        "amount_out": 34.20,
        "value_usd": 34.20,
        "tx_hash": f"0x{uuid.uuid4().hex}",
        "chain": "xlayer",
        "gas_usd": 0.05,
        "slippage_pct": 0.0,
        "agent": "economy",
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=4)).isoformat(),
        "block_number": 12_345_690,
    },
    {
        "id": str(uuid.uuid4()),
        "type": "invest",
        "status": "confirmed",
        "from_token": "USDC",
        "to_token": "USDC-LP",
        "amount_in": 2000.0,
        "amount_out": 1998.5,
        "value_usd": 2000.0,
        "tx_hash": f"0x{uuid.uuid4().hex}",
        "chain": "xlayer",
        "gas_usd": 0.41,
        "slippage_pct": 0.001,
        "agent": "execution",
        "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "block_number": 12_344_000,
    },
]


@router.get("")
async def get_transactions(page: int = Query(1, ge=1)):
    """
    Paginated transaction history.
    TODO: Query Supabase transactions table.
    """
    page_size = 20
    start = (page - 1) * page_size
    end = start + page_size
    items = SAMPLE_TRANSACTIONS[start:end]

    return {
        "success": True,
        "data": {
            "items": items,
            "total": len(SAMPLE_TRANSACTIONS),
            "page": page,
            "page_size": page_size,
            "has_more": end < len(SAMPLE_TRANSACTIONS),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{tx_hash}")
async def get_transaction(tx_hash: str):
    """Get single transaction by hash."""
    tx = next((t for t in SAMPLE_TRANSACTIONS if t["tx_hash"] == tx_hash), None)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "success": True,
        "data": tx,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
