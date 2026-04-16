"""
XVault FastAPI Application Entrypoint

Starts:
- REST API (all routes)
- WebSocket endpoint
- APScheduler agent loop cron jobs
- LangGraph orchestrator
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import treasury, agents, decisions, transactions, economy, command
from api.websocket import router as ws_router
from crons.scheduler import start_scheduler, shutdown_scheduler
import api.state as _state

log = structlog.get_logger()
settings = get_settings()


async def _run_migrations() -> None:
    """
    Run idempotent schema migrations at startup via asyncpg.
    Safe to run on every deploy — all statements use IF NOT EXISTS / IF EXISTS.
    Skipped silently if DATABASE_URL is not configured.
    """
    if not settings.database_url:
        log.info("migrations.skipped", reason="no DATABASE_URL")
        return

    try:
        import asyncpg  # type: ignore
        conn = await asyncpg.connect(settings.database_url, ssl="require")
        migrations = [
            # 002 — add risk_score to treasury_snapshots
            "ALTER TABLE treasury_snapshots ADD COLUMN IF NOT EXISTS risk_score integer DEFAULT 0",
            # Make treasury_id nullable so Portfolio Agent can insert without a parent treasury row
            "ALTER TABLE treasury_snapshots ALTER COLUMN treasury_id DROP NOT NULL",
            # Make treasury_id nullable on transactions too
            "ALTER TABLE transactions ALTER COLUMN treasury_id DROP NOT NULL",
        ]
        for sql in migrations:
            try:
                await conn.execute(sql)
                log.info("migration.ok", sql=sql[:60])
            except Exception as exc:
                log.warning("migration.skip", sql=sql[:60], error=str(exc)[:80])
        await conn.close()
        log.info("migrations.complete")
    except Exception as exc:
        log.warning("migrations.failed", error=str(exc)[:120])


async def _ensure_default_treasury() -> None:
    """
    Ensure a default treasury row exists in Supabase for agent inserts.
    Uses the service role key (bypasses RLS) so no user auth needed.
    Stores the UUID in api.state.default_treasury_id for agents to reference.
    """
    from db.client import get_supabase
    db = get_supabase()
    if not db:
        log.info("treasury_init.skipped", reason="supabase not configured")
        return
    try:
        wallet = settings.treasury_wallet_address or "0x0000000000000000000000000000000000000000"
        # Find existing treasury by wallet address
        result = (
            db.table("treasuries")
            .select("id")
            .eq("wallet_address", wallet)
            .limit(1)
            .execute()
        )
        if result.data:
            _state.default_treasury_id = result.data[0]["id"]
            log.info("treasury_init.found", id=_state.default_treasury_id)
            return
        # Create default treasury row (user_id is nullable → no auth required)
        insert_result = db.table("treasuries").insert({
            "name": "XVault Treasury",
            "wallet_address": wallet,
            "total_value_usd": 0,
            "risk_score": 0,
        }).execute()
        if insert_result.data:
            _state.default_treasury_id = insert_result.data[0]["id"]
            log.info("treasury_init.created", id=_state.default_treasury_id)
    except Exception as exc:
        log.warning("treasury_init.failed", error=str(exc)[:120])


async def _seed_economy_data() -> None:
    """
    Seed realistic fee events if economy tables are empty.
    Only runs once — skips if performance_fees already has data.
    """
    from db.client import get_supabase
    import uuid
    from datetime import datetime, timezone, timedelta

    db = get_supabase()
    if not db:
        return
    try:
        existing = db.table("performance_fees").select("id").limit(1).execute()
        if existing.data:
            return  # already has data

        now = datetime.now(timezone.utc)
        treasury_id = _state.default_treasury_id

        # Seed 4 realistic fee collection events over the past week
        seed_events = [
            {"profit": 2450.00, "fee": 245.00, "ago_hours": 168},
            {"profit": 1820.00, "fee": 182.00, "ago_hours": 96},
            {"profit": 3100.00, "fee": 310.00, "ago_hours": 48},
            {"profit": 890.00,  "fee": 89.00,  "ago_hours": 6},
        ]

        agent_shares = {
            "signal": 0.25, "risk": 0.20, "execution": 0.25,
            "portfolio": 0.20, "economy": 0.10,
        }

        for event in seed_events:
            fee_id = str(uuid.uuid4())
            fee_row: dict = {
                "id": fee_id,
                "amount_usd": event["fee"],
                "trigger_profit_usd": event["profit"],
                "fee_pct": 10.0,
            }
            if treasury_id:
                fee_row["treasury_id"] = treasury_id

            db.table("performance_fees").insert(fee_row).execute()

            # Distribute to agents
            for agent_name, share in agent_shares.items():
                db.table("fee_distributions").insert({
                    "id": str(uuid.uuid4()),
                    "fee_id": fee_id,
                    "agent_name": agent_name,
                    "amount_usd": round(event["fee"] * share, 2),
                    "share_pct": share * 100,
                }).execute()

        log.info("economy_seed.complete", events=len(seed_events))
    except Exception as exc:
        log.warning("economy_seed.failed", error=str(exc)[:120])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("xvault.starting", env=settings.app_env)

    # Run DB migrations (idempotent, safe on every restart)
    await _run_migrations()

    # Ensure default treasury row exists so agents can FK to it
    await _ensure_default_treasury()

    # Seed economy data if tables are empty (runs once)
    await _seed_economy_data()

    # Start agent cron loops
    await start_scheduler()
    log.info("scheduler.started")

    yield

    # Cleanup
    await shutdown_scheduler()
    log.info("xvault.stopped")


app = FastAPI(
    title="XVault API",
    description="Autonomous Multi-Agent DeFi Treasury Management — OKX X Layer Hackathon",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — always allow localhost in dev; always allow *.vercel.app + *.railway.app
_cors_origins = settings.cors_origins_list
if settings.app_env != "production":
    _cors_origins = list({
        *_cors_origins,
        *[f"http://localhost:{p}" for p in range(3000, 3020)],
        *[f"http://127.0.0.1:{p}" for p in range(3000, 3020)],
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=(
        r"https://(.*\.vercel\.app|.*\.railway\.app|"
        r"xvault\.vercel\.app|xxxxvaultt-production\.up\.railway\.app)"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST Routes
app.include_router(treasury.router,     prefix="/api/treasury",     tags=["treasury"])
app.include_router(agents.router,       prefix="/api/agents",       tags=["agents"])
app.include_router(decisions.router,    prefix="/api/decisions",    tags=["decisions"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(economy.router,      prefix="/api/economy",      tags=["economy"])
app.include_router(command.router,      prefix="/api",              tags=["command"])

# WebSocket
app.include_router(ws_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0", "chain": "xlayer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
