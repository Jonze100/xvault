# XVault — Autonomous Multi-Agent DeFi Treasury Management

> Built for the OKX X Layer Hackathon. XVault deploys five specialized AI agents that collaborate in real-time to manage an onchain treasury — scanning signals, vetting risk, executing trades, monitoring portfolio health, and managing agent economics via x402 micropayments.

---

## Onchain Identity

| | |
|---|---|
| **Economy Agent Master Wallet** | [`0xb5c600f74627c63476f7a7e89a6a616723783fce`](https://www.okx.com/explorer/xlayer/address/0xb5c600f74627c63476f7a7e89a6a616723783fce) |
| **Network** | OKX X Layer (Chain ID: 196) |
| **Role** | Collects performance fees & distributes agent earnings via x402 |

This wallet is the Economy Agent's agentic wallet — it autonomously collects 10% performance fees from treasury profits and distributes earnings to the four other agent wallets using x402 micropayments.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        XVault Platform                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Next.js Frontend                       │  │
│  │  Dashboard │ Treasury │ Agents │ War Room │ Settings      │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │ REST + WebSocket                          │
│  ┌──────────────────▼───────────────────────────────────────┐  │
│  │                   FastAPI Backend                         │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │              LangGraph Orchestrator                  │ │  │
│  │  │                                                      │ │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │ │  │
│  │  │  │  Signal  │  │  Risk    │  │    Execution     │  │ │  │
│  │  │  │  Agent   │──│  Agent   │──│      Agent       │  │ │  │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘  │ │  │
│  │  │       │               │               │             │ │  │
│  │  │  ┌────▼───────────────▼───────────────▼──────────┐ │ │  │
│  │  │  │          Portfolio Agent                       │ │ │  │
│  │  │  └────────────────────┬───────────────────────────┘ │ │  │
│  │  │                       │ profit detected              │ │  │
│  │  │  ┌────────────────────▼───────────────────────────┐ │ │  │
│  │  │  │     Economy Agent (x402) · 0xb5c6...3fce        │ │ │  │
│  │  │  └────────────────────────────────────────────────┘ │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │            OKX Onchain OS Skills (14 skills)         │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Supabase (PostgreSQL)                   │  │
│  │  users │ treasuries │ agent_wallets │ transactions        │  │
│  │  agent_logs │ decisions │ performance_fees                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Roles

| Agent | Role | Agentic Wallet | Loop Interval |
|-------|------|----------------|---------------|
| **Signal Agent** | Scans market data, generates trade opportunities | `signal.xvault.eth` | 5 min |
| **Risk Agent** | Security vetting, audit checks before any trade | `risk.xvault.eth` | On-demand |
| **Execution Agent** | Executes approved swaps and DeFi investments | `execution.xvault.eth` | On-demand |
| **Portfolio Agent** | Monitors positions, PnL, rebalancing triggers | `portfolio.xvault.eth` | 5 min |
| **Economy Agent** | Collects performance fees, distributes agent pay | [`0xb5c600f74627c63476f7a7e89a6a616723783fce`](https://www.okx.com/explorer/xlayer/address/0xb5c600f74627c63476f7a7e89a6a616723783fce) | 15 min |

---

## OKX Skill Usage

| Agent | OKX Skills Used | Purpose |
|-------|----------------|---------|
| Signal Agent | `okx-dex-signal` | ML-powered trade signals |
| Signal Agent | `okx-dex-trenches` | Mempool / sentiment scanning |
| Signal Agent | `okx-dex-market` | Real-time price feeds |
| Signal Agent | `okx-dex-token` | Token metadata & analytics |
| Risk Agent | `okx-security` | Smart contract security scoring |
| Risk Agent | `okx-audit-log` | Protocol audit history |
| Execution Agent | `okx-dex-swap` | On-chain token swaps |
| Execution Agent | `okx-defi-invest` | LP/yield deployment |
| Execution Agent | `okx-onchain-gateway` | Cross-chain bridging |
| Portfolio Agent | `okx-wallet-portfolio` | Wallet position tracking |
| Portfolio Agent | `okx-defi-portfolio` | DeFi position aggregation |
| Portfolio Agent | `okx-agentic-wallet` | Agentic wallet management |
| Economy Agent | `x402` | Agent micropayments & fee collection |

---

## Economy Loop

```
Portfolio Agent detects profit
         │
         ▼
Economy Agent (0xb5c600f74627c63476f7a7e89a6a616723783fce)
collects 10% performance fee via x402
         │
         ├──► 40% → Signal Agent  (premium signal subscriptions)
         ├──► 30% → Risk Agent    (security oracle fees)
         ├──► 20% → Execution Agent (gas optimization tools)
         └──► 10% → Portfolio Agent (analytics data)
```

Agents use their earnings to pay for premium data or reinvest in treasury positions.

---

## Demo Mode

Set `NEXT_PUBLIC_DEMO_MODE=true` in `frontend/.env.local` (already enabled) to run the full UI without a live backend:

- **War Room** — agent-to-agent messages appear every few seconds
- **Dashboard** — live PnL chart, asset allocation pie, risk heatmap, decisions feed
- **All agents** — shown as active with realistic wallet balances and success rates
- **Graceful fallbacks** — every component shows a skeleton/empty state if the backend is offline

---

## Folder Structure

```
xvault/
├── frontend/                    # Next.js 15 App Router
│   ├── app/
│   │   ├── layout.tsx           # Root layout with sidebar
│   │   ├── page.tsx             # Redirect to dashboard
│   │   ├── dashboard/           # PnL charts, treasury overview
│   │   ├── treasury/            # Asset breakdown, positions
│   │   ├── agents/              # Agent status, config
│   │   ├── war-room/            # Real-time agent comms
│   │   └── settings/            # API keys, thresholds
│   ├── components/
│   │   ├── dashboard/           # PnL, risk heatmap widgets
│   │   ├── agents/              # Agent cards, feed
│   │   ├── war-room/            # WebSocket visualization
│   │   └── layout/              # Sidebar, TopBar, LayoutShell
│   ├── lib/
│   │   ├── api.ts               # Backend REST client
│   │   ├── websocket.ts         # WS connection manager
│   │   ├── demo-data.ts         # Demo mode simulation data
│   │   └── types.ts             # Shared TypeScript types
│   └── hooks/                   # React hooks (all with isOffline fallback)
│
├── backend/                     # Python FastAPI
│   ├── main.py                  # App entrypoint
│   ├── config.py                # Settings & env
│   ├── agents/
│   │   ├── signal_agent.py      # Market signal scanning
│   │   ├── risk_agent.py        # Security vetting
│   │   ├── execution_agent.py   # Trade execution
│   │   ├── portfolio_agent.py   # Position monitoring
│   │   └── economy_agent.py     # x402 fee management
│   ├── orchestrator/
│   │   ├── graph.py             # LangGraph state machine
│   │   └── state.py             # Shared agent state
│   ├── mcp/
│   │   └── server.py            # OKX MCP integration (14 skills)
│   ├── api/
│   │   ├── routes/              # REST endpoints
│   │   └── websocket.py         # WS broadcast
│   ├── db/
│   │   ├── client.py            # Supabase client
│   │   └── models.py            # Table models
│   └── crons/
│       └── scheduler.py         # APScheduler jobs
│
├── .agents/skills/              # OKX Onchain OS skills (14 installed)
├── .env.example                 # Environment template
├── docker-compose.yml
└── README.md
```

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Jonze100/xvault
cd xvault

# 2. Configure environment
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE

# 3. Install OKX Onchain OS skills
npx skills add okx/onchainos-skills --yes

# 4. Start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 5. Start frontend (demo mode enabled by default)
cd frontend
npm install
npm run dev

# 6. (Optional) Docker
docker-compose up
```

---

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Recharts
- **Backend**: Python 3.11, FastAPI, LangGraph
- **AI**: Claude claude-sonnet-4-6 (Anthropic) for agent reasoning
- **Onchain**: OKX X Layer (Chain ID: 196), 14 OKX Onchain OS skills
- **Database**: Supabase (PostgreSQL + Realtime)
- **Payments**: x402 protocol for agent micropayments
- **Infra**: Docker, APScheduler, WebSockets

---

## License

MIT — Built for OKX X Layer Hackathon 2025
