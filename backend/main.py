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

log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("xvault.starting", env=settings.app_env)

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
