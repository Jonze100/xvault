"""
XVault APScheduler — Agent Cron Loop Manager

Schedules and runs agent loops:
- Signal Agent:    every 5 minutes
- Portfolio Agent: every 5 minutes
- Economy Agent:   every 15 minutes

Execution and Risk Agents are triggered on-demand by the orchestrator.
"""

from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings
from orchestrator.graph import XVaultOrchestrator

log = structlog.get_logger(__name__)
settings = get_settings()

# Shared scheduler and orchestrator instances
_scheduler = AsyncIOScheduler()
_orchestrator: XVaultOrchestrator | None = None


def get_orchestrator() -> XVaultOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = XVaultOrchestrator()
    return _orchestrator


async def run_signal_scan():
    """
    Cron job: Run Signal Agent → Risk Agent → Execution Agent pipeline.
    Called every SIGNAL_AGENT_INTERVAL seconds (default: 5 min).
    """
    log.info("cron.signal_scan.start")
    try:
        orchestrator = get_orchestrator()
        await orchestrator.run_cycle()
        log.info("cron.signal_scan.complete")
    except Exception as e:
        log.error("cron.signal_scan.error", error=str(e))


async def run_portfolio_monitor():
    """
    Cron job: Run Portfolio Agent monitoring loop.
    Called every PORTFOLIO_AGENT_INTERVAL seconds (default: 5 min).
    Updates treasury snapshot and checks for rebalance triggers.
    """
    log.info("cron.portfolio_monitor.start")
    try:
        orchestrator = get_orchestrator()
        await orchestrator.portfolio_agent.run()
        log.info("cron.portfolio_monitor.complete")
    except Exception as e:
        log.error("cron.portfolio_monitor.error", error=str(e))


async def run_economy_maintenance():
    """
    Cron job: Economy Agent maintenance loop.
    Called every ECONOMY_AGENT_INTERVAL seconds (default: 15 min).
    Reconciles agent wallets, reports economy stats.
    """
    log.info("cron.economy_maintenance.start")
    try:
        orchestrator = get_orchestrator()
        await orchestrator.economy_agent.run()
        log.info("cron.economy_maintenance.complete")
    except Exception as e:
        log.error("cron.economy_maintenance.error", error=str(e))


async def start_scheduler() -> None:
    """Register all cron jobs and start the scheduler."""

    # Signal + Risk + Execution pipeline
    _scheduler.add_job(
        run_signal_scan,
        trigger=IntervalTrigger(seconds=settings.signal_agent_interval),
        id="signal_scan",
        name="Signal Agent Scan",
        replace_existing=True,
        coalesce=True,          # skip missed runs
        max_instances=1,        # never run twice simultaneously
    )

    # Portfolio monitoring
    _scheduler.add_job(
        run_portfolio_monitor,
        trigger=IntervalTrigger(seconds=settings.portfolio_agent_interval),
        id="portfolio_monitor",
        name="Portfolio Agent Monitor",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    # Economy maintenance
    _scheduler.add_job(
        run_economy_maintenance,
        trigger=IntervalTrigger(seconds=settings.economy_agent_interval),
        id="economy_maintenance",
        name="Economy Agent Maintenance",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    _scheduler.start()
    log.info(
        "scheduler.jobs_registered",
        signal_interval=settings.signal_agent_interval,
        portfolio_interval=settings.portfolio_agent_interval,
        economy_interval=settings.economy_agent_interval,
    )


async def shutdown_scheduler() -> None:
    """Gracefully stop the scheduler."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("scheduler.stopped")
