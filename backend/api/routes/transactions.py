"""
Transactions API Routes

GET /api/transactions      — Paginated transaction history from Supabase
GET /api/transactions/{hash} — Single transaction by tx_hash
"""

import structlog
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException

from db.client import get_supabase

log = structlog.get_logger(__name__)
router = APIRouter()


def _row_to_transaction(row: dict) -> dict:
    """Map Supabase transactions row to the shape the frontend expects."""
    return {
        "id": row.get("id", ""),
        "type": row.get("type", "swap"),
        "status": row.get("status", "confirmed"),
        "from_token": row.get("from_token", ""),
        "to_token": row.get("to_token", ""),
        "amount_in": float(row.get("amount_in", 0)),
        "amount_out": float(row.get("amount_out", 0)),
        "value_usd": float(row.get("value_usd", 0)),
        "tx_hash": row.get("tx_hash", ""),
        "chain": row.get("chain", "xlayer"),
        "gas_usd": float(row.get("gas_usd", 0)),
        "slippage_pct": float(row.get("slippage_pct", 0)),
        "agent": row.get("agent_name", ""),
        "timestamp": row.get("created_at", ""),
        "block_number": row.get("block_number"),
    }


@router.get("")
async def get_transactions(page: int = Query(1, ge=1)):
    """Paginated transaction history from Supabase transactions table."""
    db = get_supabase()
    page_size = 20

    if db:
        try:
            start = (page - 1) * page_size
            end = start + page_size - 1

            result = (
                db.table("transactions")
                .select("*")
                .order("created_at", desc=True)
                .range(start, end)
                .execute()
            )
            items = [_row_to_transaction(r) for r in (result.data or [])]
            total = len(items) + start
        except Exception as exc:
            log.warning("transactions.query_failed", error=str(exc))
            items = []
            total = 0
    else:
        items = []
        total = 0

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": len(items) == page_size,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{tx_hash}")
async def get_transaction(tx_hash: str):
    """Get single transaction by hash from Supabase."""
    db = get_supabase()

    if db:
        try:
            result = (
                db.table("transactions")
                .select("*")
                .eq("tx_hash", tx_hash)
                .limit(1)
                .execute()
            )
            if result.data:
                return {
                    "success": True,
                    "data": _row_to_transaction(result.data[0]),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:
            log.warning("transactions.get_by_hash_failed", error=str(exc))

    raise HTTPException(status_code=404, detail="Transaction not found")
