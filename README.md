# XVault — Autonomous Multi-Agent DeFi Treasury

> **OKX X Layer Hackathon submission** — Five specialized AI agents collaborate in real-time to manage an onchain DeFi treasury. They scan signals, vet risk, execute trades, monitor portfolio health, and pay each other using x402 micropayments — all autonomously, all onchain.

**Live Demo** → [xxxxvaultt.vercel.app](https://xxxxvaultt.vercel.app)  
**Backend API** → [xvault-backend-production.up.railway.app](https://xvault-backend-production.up.railway.app/docs)  
**GitHub** → [github.com/Jonze100/xvault](https://github.com/Jonze100/xvault)

---

## What It Does

XVault is a fully autonomous DeFi treasury manager. You deposit assets, set risk thresholds, and five AI agents take over:

1. **Signal Agent** scans OKX DEX data every 60 minutes for trade opportunities
2. **Risk Agent** vets every opportunity for security risks before anything is touched
3. **Execution Agent** executes approved swaps and yield deployments via OKX DEX
4. **Portfolio Agent** monitors positions, tracks PnL, and flags rebalancing needs
5. **Economy Agent** collects 10% performance fees and pays each agent for their work using x402

The agents communicate through a LangGraph state machine — each decision is logged, every transaction is visible on the dashboard in real-time.

---

## Onchain Identity

| | |
|---|---|
| **Agentic Wallet** | [`0x10bfbc3a505e78c3721993945ccbd391f8048f91`](https://www.okx.com/explorer/xlayer/address/0x10bfbc3a505e78c3721993945ccbd391f8048f91) |
| **Network** | OKX X Layer — Chain ID 196 |

---

## Real Onchain Transactions

All transactions executed via `onchainos swap execute` (okx-dex-swap) on OKX X Layer:

| Tx Hash | Swap | Amount | Explorer |
|---------|------|--------|----------|
| `0x3bc4ff64...b662` | USDC → OKB | $0.50 | [View](https://www.okx.com/explorer/xlayer/tx/0x3bc4ff649474718a5e429357c6ef0b2390d4a8eed0e8d1566cc9345a9574b662) |
| `0xe0073953...5291` | USDC → WETH | $0.50 | [View](https://www.okx.com/explorer/xlayer/tx/0xe0073953c57a1477ce932adeae4eb8beff832fd9e1221ba4eab4968c6b735291) |
| `0x108587cb...d7b5` | USDC → XDOG | $0.30 | [View](https://www.okx.com/explorer/xlayer/tx/0x108587cbeefaf06f9d98dcb2e965d077b785327fc2716ab4b0bd632ced01d7b5) |
| `0xb51d503e...e5a3` | USDC → XSHIB | $0.30 | [View](https://www.okx.com/explorer/xlayer/tx/0xb51d503eca9733d85909d39d136f19b675c1d274c23d73f393a4be5098d8e5a3) |
| `0x63a5b0d9...6ae0` | USDC → FDOG | $0.20 | [View](https://www.okx.com/explorer/xlayer/tx/0x63a5b0d954aa789322cb20ff95168d34fe70c6e71b668ce6722c6990178c6ae0) |
| `0x5643670f...4c9a` | OKB → USDC | $0.87 | [View](https://www.okx.com/explorer/xlayer/tx/0x5643670f3fd6c483cd16d430f0abc84d43691ad8561cf474efe97a8e02704c9a) |
| `0x8da9fd96...ed3c` | USDC → WETH | $0.20 | [View](https://www.okx.com/explorer/xlayer/tx/0x8da9fd9609eda2faa4cb0431899821dccda6dcbfe5ce461c6717e7cb207ced3c) |
| `0xcccbbf79...5b18` | XDOG → USDC | 200 XDOG | [View](https://www.okx.com/explorer/xlayer/tx/0xcccbbf796bf8a3e8c1f53557072cffb23f29efb05fe63349296f94c8d0555b18) |
| `0x51bb3b91...5d76` | USDC → WETH | $0.30 | [View](https://www.okx.com/explorer/xlayer/tx/0x51bb3b91d14b3b75b5015919df752992a8702f7463a14a61277dba04751c5d76) |
| `0x9a6557d6...a16e` | USDC → WETH | $0.05 | [View](https://www.okx.com/explorer/xlayer/tx/0x9a6557d691a15b81ae998006bb5da369139aaee6af1e35750c30710caa20a16e) |
| `0x51b32e86...578e` | USDC → WETH | $0.05 | [View](https://www.okx.com/explorer/xlayer/tx/0x51b32e86e94db5e47bc0d6fd3678299315d2412a7a7e1e3546ff5071fffc578e) |
| `0x49489608...ac0e` | USDC → XDOG | $0.05 | [View](https://www.okx.com/explorer/xlayer/tx/0x4948960889486346d600f64c1f601008dcecb9089373d7ab2ae809880b82ac0e) |
| `0x10e28f64...8a6c` | USDC → XSHIB | $0.05 | [View](https://www.okx.com/explorer/xlayer/tx/0x10e28f64e5d09e8a2b65022d0f7e9501e4b162c469ae7601a9c44e4fc4878a6c) |

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
                                                               │ 0x10bf...8f91   │
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
- **Agentic Wallet Login** — Email OTP login via OKX Onchain OS agentic wallet
- **Light / Dark theme** — Fully themed with OKX brand colors

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Recharts, SWR |
| Backend | Python 3.11, FastAPI, LangGraph, APScheduler |
| AI | Claude Sonnet 4.6 (Anthropic) — agent reasoning engine |
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
