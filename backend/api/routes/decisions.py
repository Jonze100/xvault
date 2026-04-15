"""
Decisions API Routes

GET /api/decisions — Paginated decision log from Supabase agent_logs table.
Returns empty list (not demo data) when Supabase is not configured.
"""

import structlog
from datetime import datetime, timezone
from fastapi import APIRouter, Query

from db.client import get_supabase

log = structlog.get_logger(__name__)
router = APIRouter()


def _row_to_decision(row: dict) -> dict:
    """Map Supabase agent_logs row to the shape the frontend expects."""
    return {
        "id": row.get("id", ""),
        "agent": row.get("agent_name", ""),
        "type": row.get("decision_type", ""),
        "reasoning": row.get("reasoning", ""),
        "confidence": float(row.get("confidence") or 0),
        "data": row.get("data") or {},
        "tx_hash": row.get("tx_hash"),
        "timestamp": row.get("created_at", ""),
    }


@router.get("")
async def get_decisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    agent: str | None = Query(None),
    limit: int | None = Query(None),
):
    """
    Paginated decision log from Supabase agent_logs table.
    Falls back to an empty list when Supabase is unavailable.
    Live inserts arrive via WebSocket agent_decision events — the frontend
    merges them in real-time without polling.
    """
    db = get_supabase()

    if db:
        try:
            start = (page - 1) * page_size
            end = start + page_size - 1

            query = (
                db.table("agent_logs")
                .select("*")
                .order("created_at", desc=True)
                .range(start, end)
            )
            if agent:
                query = query.eq("agent_name", agent)
            if limit:
                query = query.limit(limit)

            result = query.execute()
            items = [_row_to_decision(r) for r in (result.data or [])]

            # Approximate total (Supabase count requires separate query)
            total = len(items) + start

        except Exception as exc:
            log.warning("decisions.supabase_error", error=str(exc))
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
