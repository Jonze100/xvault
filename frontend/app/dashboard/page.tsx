// =============================================================================
// Dashboard Page — PnL, Treasury Overview, Risk Heatmap, Agent Activity
// =============================================================================

"use client";

import { useState } from "react";
import PnLChart from "@/components/dashboard/PnLChart";
import TreasuryOverview from "@/components/dashboard/TreasuryOverview";
import RiskHeatmap from "@/components/dashboard/RiskHeatmap";
import AgentStatusRow from "@/components/dashboard/AgentStatusRow";
import RecentDecisions from "@/components/dashboard/RecentDecisions";
import NLCommandBox from "@/components/dashboard/NLCommandBox";
import MetricCard from "@/components/dashboard/MetricCard";
import { useTreasury } from "@/hooks/useTreasury";
import { useAgents } from "@/hooks/useAgents";
import { TrendingUp, Shield, Zap, DollarSign } from "lucide-react";

export default function DashboardPage() {
  const [pnlRange, setPnlRange] = useState<"24h" | "7d" | "30d" | "all">("24h");
  const { treasury, isLoading: treasuryLoading, isOffline: treasuryOffline } = useTreasury();
  const { agents, isLoading: agentsLoading } = useAgents();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            Treasury Dashboard
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Autonomous multi-agent DeFi management · OKX X Layer
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            All agents active
          </span>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<DollarSign className="w-4 h-4" />}
          label="Total AUM"
          value={treasury ? `$${(treasury.total_value_usd / 1000).toFixed(1)}K` : "—"}
          change={treasury?.total_pnl_24h_pct}
          loading={treasuryLoading}
          color="vault"
        />
        <MetricCard
          icon={<TrendingUp className="w-4 h-4" />}
          label="24h PnL"
          value={treasury ? `$${treasury.total_pnl_24h_usd.toFixed(0)}` : "—"}
          change={treasury?.total_pnl_24h_pct}
          loading={treasuryLoading}
          color="emerald"
        />
        <MetricCard
          icon={<Shield className="w-4 h-4" />}
          label="Risk Score"
          value={treasury ? `${treasury.risk_score}/100` : "—"}
          loading={treasuryLoading}
          color={
            treasury && treasury.risk_score < 40 ? "emerald" :
            treasury && treasury.risk_score < 70 ? "amber" : "red"
          }
        />
        <MetricCard
          icon={<Zap className="w-4 h-4" />}
          label="Fees Collected"
          value={
            treasury
              ? `$${treasury.performance_fees_collected_usd.toFixed(0)}`
              : "—"
          }
          loading={treasuryLoading}
          color="blue"
        />
      </div>

      {/* Agent Status Row */}
      <AgentStatusRow agents={agents ?? []} loading={agentsLoading} />

      {/* Main Grid: PnL Chart + Treasury Breakdown */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* PnL Chart — takes 2/3 width on xl */}
        <div className="xl:col-span-2 glass-card rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-300">
              Portfolio Performance
            </h2>
            <div className="flex gap-1">
              {(["24h", "7d", "30d", "all"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setPnlRange(r)}
                  className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                    pnlRange === r
                      ? "bg-vault-600 text-white"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <PnLChart range={pnlRange} />
        </div>

        {/* Treasury Asset Breakdown */}
        <div className="glass-card rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-300 mb-4">
            Asset Allocation
          </h2>
          <TreasuryOverview treasury={treasury} loading={treasuryLoading} isOffline={treasuryOffline} />
        </div>
      </div>

      {/* Bottom Grid: Risk Heatmap + Recent Decisions */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="glass-card rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-300 mb-4">
            Risk Heatmap
          </h2>
          <RiskHeatmap />
        </div>

        <div className="glass-card rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-300 mb-4">
            Recent Agent Decisions
          </h2>
          <RecentDecisions />
        </div>
      </div>

      {/* Natural Language Command Box — sticky at bottom */}
      <NLCommandBox />
    </div>
  );
}
