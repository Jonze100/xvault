"""
Daily Claude API spend tracker.

Tracks estimated cost per call and pauses Claude reasoning when the daily cap
is exceeded, falling back to direct OKX scoring.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone, date
from config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# Approximate cost per 1K tokens (Sonnet 4.6 pricing estimate)
_INPUT_COST_PER_1K = 0.003
_OUTPUT_COST_PER_1K = 0.015

# Daily tracking
_today: date | None = None
_daily_spend: float = 0.0
_daily_calls: int = 0


def _reset_if_new_day() -> None:
    global _today, _daily_spend, _daily_calls
    now = date.today()
    if _today != now:
        if _today is not None:
            log.info("spend_tracker.day_reset", prev_day=str(_today), total_spend=_daily_spend, total_calls=_daily_calls)
        _today = now
        _daily_spend = 0.0
        _daily_calls = 0


def record_usage(input_tokens: int, output_tokens: int) -> None:
    """Record token usage from a Claude API call."""
    global _daily_spend, _daily_calls
    _reset_if_new_day()
    cost = (input_tokens / 1000 * _INPUT_COST_PER_1K) + (output_tokens / 1000 * _OUTPUT_COST_PER_1K)
    _daily_spend += cost
    _daily_calls += 1
    log.debug("spend_tracker.record", cost=round(cost, 6), daily_total=round(_daily_spend, 4), calls=_daily_calls)


def is_budget_exceeded() -> bool:
    """Check if daily spend cap has been exceeded."""
    _reset_if_new_day()
    exceeded = _daily_spend >= settings.daily_spend_cap_usd
    if exceeded:
        log.warning("spend_tracker.budget_exceeded", daily_spend=round(_daily_spend, 4), cap=settings.daily_spend_cap_usd)
    return exceeded


def get_daily_stats() -> dict:
    """Return current daily spend stats."""
    _reset_if_new_day()
    return {
        "date": str(_today),
        "spend_usd": round(_daily_spend, 4),
        "cap_usd": settings.daily_spend_cap_usd,
        "calls": _daily_calls,
        "budget_remaining": round(max(0, settings.daily_spend_cap_usd - _daily_spend), 4),
        "paused": is_budget_exceeded(),
    }


async def log_to_supabase() -> None:
    """Persist daily spend stats to Supabase for auditing."""
    from db.client import get_supabase
    db = get_supabase()
    if not db:
        return
    try:
        stats = get_daily_stats()
        db.table("agent_logs").insert({
            "agent_name": "economy",
            "decision_type": "spend_report",
            "reasoning": f"Daily Claude spend: ${stats['spend_usd']:.4f} / ${stats['cap_usd']:.2f} cap ({stats['calls']} calls)",
            "confidence": min(1.0, stats["spend_usd"] / max(stats["cap_usd"], 0.01)),
            "data": stats,
        }).execute()
    except Exception as exc:
        log.warning("spend_tracker.log_failed", error=str(exc)[:80])
