# XVault — Autonomous Multi-Agent DeFi Treasury

> **OKX X Layer Hackathon submission** — Five specialized AI agents collaborate in real-time to manage an onchain DeFi treasury. They scan signals, vet risk, execute trades, monitor portfolio health, and pay each other using x402 micropayments — all autonomously, all onchain.

**Live Demo** → [xxxvaullt-g333cyg68-jonze100s-projects.vercel.app](https://xxxvaullt-g333cyg68-jonze100s-projects.vercel.app)  
**Backend API** → [xvault-backend-production.up.railway.app](https://xvault-backend-production.up.railway.app/docs)  
**GitHub** → [github.com/Jonze100/xvault](https://github.com/Jonze100/xvault)

---

## What It Does

XVault is a fully autonomous DeFi treasury manager. You deposit assets, set risk thresholds, and five AI agents take over:

1. **Signal Agent** scans OKX DEX data every 5 minutes for trade opportunities
2. **Risk Agent** vets every opportunity for security risks before anything is touched
3. **Execution Agent** executes approved swaps and yield deployments via OKX DEX
4. **Portfolio Agent** monitors positions, tracks PnL, and flags rebalancing needs
5. **Economy Agent** collects 10% performance fees and pays each agent for their work using x402

The agents communicate through a LangGraph state machine — each decision is logged, every transaction is visible on the dashboard in real-time.

---

## Onchain Identity

| | |
|---|---|
| **Economy Agent Wallet** | [`0xb5c600f74627c63476f7a7e89a6a616723783fce`](https://www.okx.com/explorer/xlayer/address/0xb5c600f74627c63476f7a7e89a6a616723783fce) |
| **Network** | OKX X Layer — Chain ID 196 |

---

## Agent Pipeline

```
Market Data (OKX DEX)
       │
       ▼
 ┌─────────────┐     signal      ┌────────────┐    approved    ┌───────────────┐
 │ Signal Agent │ ─────────────► │ Risk Agent │ ─────────────► │ Execution     │
 │ okx-dex-    │                 │ okx-       │                 │ Agent         │
 │ signal      │                 │ security   │                 │ okx-dex-swap  │
 └─────────────┘                 └────────────┘                 └───────┬───────┘
                                                                        │ tx confirmed
                                                                        ▼
                                                               ┌─────────────────┐
                                                               │ Portfolio Agent │
                                                               │ okx-wallet-     │
                                                               │ portfolio       │
                                                               └────────┬────────┘
                                                                        │ profit detected
                                                                        ▼
                                                               ┌─────────────────┐
                                                               │ Economy Agent   │
                                                               │ x402 payments   │
                                                               │ 0xb5c6...3fce   │
                                                               └─────────────────┘
```

---

## x402 Economy Loop

Agents earn by doing their job. The Economy Agent holds the master wallet and distributes performance fees automatically:

```
Treasury profit detected by Portfolio Agent
         │
         ▼
Economy Agent collects 10% performance fee via x402
         │
         ├──► 40% → Signal Agent   (rewarded per valid signal)
         ├──► 30% → Risk Agent     (rewarded per security check)
         ├──► 20% → Execution Agent (rewarded per successful trade)
         └──► 10% → Portfolio Agent (rewarded per snapshot)
```

Agents use their earnings to pay for premium OKX data feeds — creating a self-sustaining economy where better-performing agents earn more and invest more into improving their performance.

---

## OKX Skills Used (14 skills)

| Agent | Skill | What It Does |
|-------|-------|-------------|
| Signal | `okx-dex-signal` | ML-powered momentum signals |
| Signal | `okx-dex-trenches` | Whale / smart money tracking |
| Signal | `okx-dex-market` | Real-time OHLC price data |
| Signal | `okx-dex-token` | Token metadata, holder distribution |
| Risk | `okx-security` | Smart contract security scoring, honeypot detection |
| Risk | `okx-audit-log` | Protocol audit history |
| Execution | `okx-dex-swap` | On-chain token swaps with best routing |
| Execution | `okx-defi-invest` | Yield farming, LP deployment |
| Execution | `okx-onchain-gateway` | Cross-chain bridging |
| Portfolio | `okx-wallet-portfolio` | Wallet balance & position tracking |
| Portfolio | `okx-defi-portfolio` | DeFi position aggregation |
| Portfolio | `okx-agentic-wallet` | Agentic wallet management |
| Economy | `okx-x402-payment` | x402 micropayment execution |
| All | `okx-audit-log` | Full agent action audit trail |

---

## Dashboard Features

- **Treasury Dashboard** — Real-time AUM, 24h PnL, risk score, asset allocation pie chart
- **Portfolio Performance** — Interactive PnL chart (24h / 7d / 30d / all-time)
- **Risk Heatmap** — Protocol exposure vs risk score across all DeFi positions
- **Agent Status Row** — Live status of all 5 agents (active / thinking / idle)
- **War Room** — Real-time agent-to-agent message visualization with animated network graph
- **Live Decisions Feed** — Every agent decision with reasoning, confidence %, and tx hash
- **Natural Language Commands** — Tell the agents what to do in plain English
- **OKX Wallet Connect** — Connect OKX Wallet, MetaMask, or any EIP-1193 wallet
- **Light / Dark theme** — Fully themed with OKX brand colors

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Recharts, SWR |
| Backend | Python 3.11, FastAPI, LangGraph, APScheduler |
| AI | Claude Sonnet (Anthropic) — agent reasoning engine |
| Blockchain | OKX X Layer (Chain ID 196) |
| OKX Integration | 14 OKX Onchain OS skills via Claude Code MCP |
| Database | Supabase (PostgreSQL) |
| Payments | x402 protocol |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Architecture

```
xvault/
├── frontend/                    # Next.js 16 App Router
│   ├── app/
│   │   ├── dashboard/           # PnL, treasury, risk heatmap, decisions
│   │   ├── treasury/            # Full asset table, transaction history
│   │   ├── agents/              # Agent cards, earnings chart, skills table
│   │   ├── war-room/            # Real-time agent comms + network graph
│   │   └── settings/            # Risk thresholds, API config
│   ├── components/
│   │   ├── dashboard/           # MetricCard, PnLChart, RiskHeatmap, etc.
│   │   ├── war-room/            # AgentCommsGraph, MessageFeed, LiveDecisions
│   │   └── layout/              # Sidebar, TopBar (wallet connect), LayoutShell
│   └── hooks/                   # SWR data hooks with offline graceful fallback
│
├── backend/                     # Python FastAPI
│   ├── agents/
│   │   ├── signal_agent.py      # okx-dex-signal + trenches + market
│   │   ├── risk_agent.py        # okx-security + audit-log
│   │   ├── execution_agent.py   # okx-dex-swap + defi-invest + gateway
│   │   ├── portfolio_agent.py   # okx-wallet-portfolio + defi-portfolio
│   │   └── economy_agent.py     # x402 fee collection + distribution
│   ├── orchestrator/
│   │   └── graph.py             # LangGraph multi-agent state machine
│   ├── api/
│   │   ├── routes/              # /api/treasury, /agents, /decisions, etc.
│   │   └── websocket.py         # Real-time event broadcast
│   └── db/
│       └── client.py            # Supabase client (optional, graceful fallback)
│
└── .agents/skills/              # 14 OKX Onchain OS skills installed
```

---

## Run Locally

```bash
# Clone
git clone https://github.com/Jonze100/xvault
cd xvault

# Configure
cp .env.example .env
# Required: ANTHROPIC_API_KEY, OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE, OKX_PROJECT_ID

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Built By

[@Jonze100](https://github.com/Jonze100) — OKX X Layer Hackathon 2026

MIT License
