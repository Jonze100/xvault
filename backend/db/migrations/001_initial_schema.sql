-- =============================================================================
-- XVault Initial Database Schema
-- Run in Supabase SQL Editor
-- =============================================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- =============================================================================
-- Users
-- =============================================================================

create table if not exists users (
  id          uuid primary key default uuid_generate_v4(),
  email       text unique not null,
  settings    jsonb default '{}',
  created_at  timestamptz default now()
);

alter table users enable row level security;

create policy "Users can read their own data"
  on users for select using (auth.uid() = id);

-- =============================================================================
-- Treasuries
-- =============================================================================

create table if not exists treasuries (
  id                              uuid primary key default uuid_generate_v4(),
  user_id                         uuid references users(id) on delete cascade,
  name                            text not null default 'XVault Treasury',
  wallet_address                  text not null,
  total_value_usd                 numeric(20, 4) default 0,
  risk_score                      integer default 0 check (risk_score between 0 and 100),
  performance_fees_collected_usd  numeric(20, 4) default 0,
  created_at                      timestamptz default now(),
  updated_at                      timestamptz default now()
);

alter table treasuries enable row level security;

create policy "Users can manage their treasury"
  on treasuries for all using (auth.uid() = user_id);

-- =============================================================================
-- Treasury Snapshots (PnL history)
-- =============================================================================

create table if not exists treasury_snapshots (
  id              uuid primary key default uuid_generate_v4(),
  treasury_id     uuid references treasuries(id) on delete cascade,
  total_value_usd numeric(20, 4) not null,
  pnl_usd         numeric(20, 4) default 0,
  pnl_pct         numeric(10, 4) default 0,
  assets          jsonb default '[]',
  snapshot_at     timestamptz default now()
);

create index idx_treasury_snapshots_treasury_id_snapshot_at
  on treasury_snapshots(treasury_id, snapshot_at desc);

-- =============================================================================
-- Agent Wallets
-- =============================================================================

create table if not exists agent_wallets (
  id                  uuid primary key default uuid_generate_v4(),
  agent_name          text not null check (agent_name in ('signal', 'risk', 'execution', 'portfolio', 'economy')),
  address             text not null unique,
  balance_eth         numeric(20, 8) default 0,
  balance_usd         numeric(20, 4) default 0,
  earnings_total_usd  numeric(20, 4) default 0,
  updated_at          timestamptz default now(),
  unique (agent_name)
);

-- =============================================================================
-- Transactions
-- =============================================================================

create table if not exists transactions (
  id            uuid primary key default uuid_generate_v4(),
  treasury_id   uuid references treasuries(id) on delete cascade,
  agent_name    text not null,
  type          text not null check (type in ('swap', 'invest', 'bridge', 'fee', 'transfer')),
  status        text not null default 'pending' check (status in ('pending', 'confirmed', 'failed')),
  from_token    text not null,
  to_token      text not null,
  amount_in     numeric(20, 8) not null,
  amount_out    numeric(20, 8) not null,
  value_usd     numeric(20, 4) not null,
  tx_hash       text unique,
  chain         text default 'xlayer',
  gas_usd       numeric(10, 4) default 0,
  slippage_pct  numeric(8, 4) default 0,
  block_number  bigint,
  created_at    timestamptz default now(),
  confirmed_at  timestamptz
);

create index idx_transactions_treasury_id_created_at
  on transactions(treasury_id, created_at desc);

create index idx_transactions_agent_name
  on transactions(agent_name);

-- =============================================================================
-- Agent Logs (Decisions)
-- =============================================================================

create table if not exists agent_logs (
  id              uuid primary key default uuid_generate_v4(),
  agent_name      text not null,
  decision_type   text not null,
  reasoning       text not null,
  confidence      numeric(4, 3) check (confidence between 0 and 1),
  data            jsonb default '{}',
  tx_hash         text,
  created_at      timestamptz default now()
);

create index idx_agent_logs_agent_name_created_at
  on agent_logs(agent_name, created_at desc);

-- =============================================================================
-- Agent Messages (War Room)
-- =============================================================================

create table if not exists agent_messages (
  id            uuid primary key default uuid_generate_v4(),
  from_agent    text not null,
  to_agent      text not null,  -- agent name or "all"
  content       text not null,
  message_type  text not null check (message_type in ('signal', 'request', 'response', 'broadcast')),
  created_at    timestamptz default now()
);

create index idx_agent_messages_created_at
  on agent_messages(created_at desc);

-- =============================================================================
-- Performance Fees (Economy Agent)
-- =============================================================================

create table if not exists performance_fees (
  id                  uuid primary key default uuid_generate_v4(),
  treasury_id         uuid references treasuries(id) on delete cascade,
  amount_usd          numeric(20, 4) not null,
  trigger_profit_usd  numeric(20, 4) not null,
  fee_pct             numeric(6, 2) default 10.0,
  collection_tx_hash  text,
  created_at          timestamptz default now()
);

create table if not exists fee_distributions (
  id          uuid primary key default uuid_generate_v4(),
  fee_id      uuid references performance_fees(id) on delete cascade,
  agent_name  text not null,
  amount_usd  numeric(20, 4) not null,
  pct         numeric(6, 2) not null,
  tx_hash     text,
  created_at  timestamptz default now()
);

-- =============================================================================
-- Realtime subscriptions for frontend WebSocket fallback
-- =============================================================================

alter publication supabase_realtime add table agent_logs;
alter publication supabase_realtime add table agent_messages;
alter publication supabase_realtime add table transactions;
alter publication supabase_realtime add table treasury_snapshots;
