"""
Economy API Routes

GET /api/economy/fees     — Performance fee history from Supabase
GET /api/economy/earnings — Agent earnings breakdown from Supabase
GET /api/economy/totals   — Lifetime totals from Supabase

Falls back to zeros when Supabase is not configured.
"""

import structlog
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from db.client import get_supabase

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/fees")
async def get_fees_history(limit: int = Query(20, ge=1, le=100)):
    """Performance fee collection events from Supabase performance_fees table."""
    db = get_supabase()
    fees: list[dict] = []

    if db:
        try:
            result = (
                db.table("performance_fees")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            for row in (result.data or []):
                fees.append({
                    "id": row.get("id", ""),
                    "amount_usd": float(row.get("amount_usd", 0)),
                    "trigger_profit_usd": float(row.get("trigger_profit_usd", 0)),
                    "fee_pct": float(row.get("fee_pct", 10)),
                    "timestamp": row.get("created_at", ""),
                    "tx_hash": row.get("collection_tx_hash"),
                    "distributions": row.get("distributions") or [],
                })
        except Exception as exc:
            log.warning("economy.fees_query_failed", error=str(exc))

    return {
        "success": True,
        "data": fees,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/earnings")
async def get_agent_earnings():
    """
    Lifetime earnings per agent from fee_distributions table.
    """
    db = get_supabase()
    earnings: dict[str, float] = {
        "signal": 0.0,
        "risk": 0.0,
        "execution": 0.0,
        "portfolio": 0.0,
        "economy": 0.0,
    }

    if db:
        try:
            result = (
                db.table("fee_distributions")
                .select("agent_name, amount_usd")
                .execute()
            )
            for row in (result.data or []):
                agent = row.get("agent_name", "")
                if agent in earnings:
                    earnings[agent] += float(row.get("amount_usd", 0))
        except Exception as exc:
            log.warning("economy.earnings_query_failed", error=str(exc))

    return {
        "success": True,
        "data": earnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/totals")
async def get_totals():
    """Lifetime economy totals from Supabase."""
    db = get_supabase()
    total_fees = 0.0
    total_distributed = 0.0
    fee_events = 0

    if db:
        try:
            result = db.table("performance_fees").select("amount_usd").execute()
            rows = result.data or []
            total_fees = sum(float(r.get("amount_usd", 0)) for r in rows)
            fee_events = len(rows)

            dist_result = db.table("fee_distributions").select("amount_usd").execute()
            total_distributed = sum(
                float(r.get("amount_usd", 0)) for r in (dist_result.data or [])
            )
        except Exception as exc:
            log.warning("economy.totals_query_failed", error=str(exc))

    return {
        "success": True,
        "data": {
            "total_fees_usd": total_fees,
            "total_distributed_usd": total_distributed,
            "fee_events": fee_events,
            "avg_fee_usd": total_fees / fee_events if fee_events > 0 else 0.0,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
