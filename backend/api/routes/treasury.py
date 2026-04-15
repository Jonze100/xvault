"""
Treasury API Routes

All data comes from Supabase (populated by Portfolio Agent every 5 min).
Falls back to zeros / empty arrays when Supabase is not configured —
never returns fake hardcoded numbers.

GET /api/treasury             — Latest treasury snapshot
GET /api/treasury/pnl         — Historical PnL from treasury_snapshots
GET /api/treasury/risk-heatmap — Protocol risk exposure
POST /api/treasury/rebalance  — Trigger rebalance cycle
"""

import structlog
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Query

from db.client import get_supabase
from config import get_settings

log = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()


# ─── Treasury overview ───────────────────────────────────────────────────────

@router.get("")
async def get_treasury():
    """
    Return latest treasury state from Supabase treasury_snapshots.
    The Portfolio Agent inserts a new snapshot every 5 minutes.
    """
    db = get_supabase()
    snapshot = None

    if db:
        try:
            result = (
                db.table("treasury_snapshots")
                .select("*")
                .order("snapshot_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                snapshot = result.data[0]
        except Exception as exc:
            log.warning("treasury.snapshot_query_failed", error=str(exc))

    # Derive performance fees from performance_fees table if available
    total_fees = 0.0
    if db:
        try:
            fees_result = db.table("performance_fees").select("amount_usd").execute()
            total_fees = sum(
                float(r.get("amount_usd", 0))
                for r in (fees_result.data or [])
            )
        except Exception:
            pass

    if snapshot:
        assets = snapshot.get("assets") or []
        total_value = float(snapshot.get("total_value_usd", 0))
        pnl_24h_usd = float(snapshot.get("pnl_usd", 0))
        pnl_24h_pct = float(snapshot.get("pnl_pct", 0))
        risk_score = int(snapshot.get("risk_score", 0))

        return {
            "success": True,
            "data": {
                "id": snapshot.get("id", str(uuid.uuid4())),
                "name": "XVault Treasury",
                "total_value_usd": total_value,
                "total_pnl_24h_usd": pnl_24h_usd,
                "total_pnl_24h_pct": pnl_24h_pct,
                "total_pnl_7d_usd": 0.0,
                "total_pnl_all_time_usd": 0.0,
                "risk_score": risk_score,
                "last_rebalance": snapshot.get("snapshot_at", ""),
                "performance_fees_collected_usd": total_fees,
                "wallet_address": settings.treasury_wallet_address,
                "assets": assets,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # No snapshot yet — return zeros so the dashboard shows real emptiness
    return {
        "success": True,
        "data": {
            "id": str(uuid.uuid4()),
            "name": "XVault Treasury",
            "total_value_usd": 0.0,
            "total_pnl_24h_usd": 0.0,
            "total_pnl_24h_pct": 0.0,
            "total_pnl_7d_usd": 0.0,
            "total_pnl_all_time_usd": 0.0,
            "risk_score": 0,
            "last_rebalance": None,
            "performance_fees_collected_usd": total_fees,
            "wallet_address": settings.treasury_wallet_address,
            "assets": [],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── PnL history ─────────────────────────────────────────────────────────────

@router.get("/pnl")
async def get_pnl_history(
    time_range: Literal["24h", "7d", "30d", "all"] = Query("24h", alias="range"),
):
    """
    Return historical PnL data points from Supabase treasury_snapshots.
    Returns empty array before Portfolio Agent has run.
    """
    db = get_supabase()
    points: list[dict] = []

    if db:
        try:
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            cutoffs = {
                "24h": now - timedelta(hours=24),
                "7d":  now - timedelta(days=7),
                "30d": now - timedelta(days=30),
                "all": None,
            }
            cutoff = cutoffs[time_range]

            query = (
                db.table("treasury_snapshots")
                .select("total_value_usd, pnl_usd, pnl_pct, snapshot_at")
                .order("snapshot_at", desc=False)
                .limit(500)
            )
            if cutoff:
                query = query.gte("snapshot_at", cutoff.isoformat())

            result = query.execute()
            points = [
                {
                    "timestamp": r["snapshot_at"],
                    "value_usd": float(r.get("total_value_usd", 0)),
                    "pnl_usd": float(r.get("pnl_usd", 0)),
                    "pnl_pct": float(r.get("pnl_pct", 0)),
                }
                for r in (result.data or [])
            ]
        except Exception as exc:
            log.warning("treasury.pnl_query_failed", error=str(exc))

    return {
        "success": True,
        "data": points,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Risk heatmap ─────────────────────────────────────────────────────────────

@router.get("/risk-heatmap")
async def get_risk_heatmap():
    """
    Protocol risk heatmap. Risk scores are computed by Risk Agent via okx-security.
    Returns live data from Supabase if available; falls back to empty list.
    """
    db = get_supabase()
    data: list[dict] = []

    if db:
        try:
            # Risk assessments are stored in agent_logs by the Risk Agent
            result = (
                db.table("agent_logs")
                .select("data, created_at")
                .eq("agent_name", "risk")
                .eq("decision_type", "risk_assessment")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            seen: set[str] = set()
            for row in (result.data or []):
                row_data = row.get("data") or {}
                protocol = row_data.get("token") or row_data.get("protocol")
                if protocol and protocol not in seen:
                    seen.add(protocol)
                    data.append({
                        "protocol": protocol,
                        "chain": "xlayer",
                        "exposure_usd": float(row_data.get("exposure_usd", 0)),
                        "risk_score": int(100 - row_data.get("security_score", 100)),
                        "audit_score": int(row_data.get("security_score", 100)),
                    })
        except Exception as exc:
            log.warning("treasury.heatmap_query_failed", error=str(exc))

    return {
        "success": True,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Rebalance trigger ────────────────────────────────────────────────────────

@router.post("/rebalance")
async def trigger_rebalance():
    """Trigger a manual rebalance cycle via the orchestrator."""
    from crons.scheduler import get_orchestrator
    try:
        orchestrator = get_orchestrator()
        import asyncio
        asyncio.create_task(orchestrator.run_cycle())
        status = "queued"
    except Exception as exc:
        log.warning("treasury.rebalance_trigger_failed", error=str(exc))
        status = "failed"

    return {
        "success": status == "queued",
        "data": {"job_id": str(uuid.uuid4()), "status": status},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
