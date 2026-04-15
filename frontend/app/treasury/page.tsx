// =============================================================================
// Treasury Page — Full Asset Breakdown, Positions, Transactions
// =============================================================================

"use client";

import { useState } from "react";
import AssetTable from "@/components/dashboard/AssetTable";
import TransactionHistory from "@/components/dashboard/TransactionHistory";
import { useTreasury } from "@/hooks/useTreasury";
import { useTransactions } from "@/hooks/useTransactions";
import { RefreshCw } from "lucide-react";

export default function TreasuryPage() {
  const [activeTab, setActiveTab] = useState<"assets" | "transactions" | "defi">(
    "assets"
  );
  const { treasury, isLoading, refetch } = useTreasury();
  const { transactions } = useTransactions();

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Treasury</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Managed by Portfolio Agent · Execution Agent
          </p>
        </div>
        <button
          onClick={refetch}
          className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-500 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Refresh
        </button>
      </div>

      {/* Treasury Value Banner */}
      {treasury && (
        <div className="glass-card rounded-xl p-6 border border-vault-800/30">
          <div className="flex flex-wrap gap-8">
            <div>
              <p className="text-xs text-zinc-500">Total Value</p>
              <p className="text-3xl font-bold text-vault-400 mt-1">
                ${treasury.total_value_usd.toLocaleString("en-US", { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">24h PnL</p>
              <p
                className={`text-xl font-semibold mt-1 ${
                  treasury.total_pnl_24h_usd >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                {treasury.total_pnl_24h_usd >= 0 ? "+" : ""}$
                {Math.abs(treasury.total_pnl_24h_usd).toFixed(2)}
                <span className="text-sm ml-1">
                  ({treasury.total_pnl_24h_pct >= 0 ? "+" : ""}
                  {treasury.total_pnl_24h_pct.toFixed(2)}%)
                </span>
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">All-Time PnL</p>
              <p className="text-xl font-semibold text-emerald-400 mt-1">
                +${treasury.total_pnl_all_time_usd.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">Positions</p>
              <p className="text-xl font-semibold text-zinc-200 mt-1">
                {treasury.assets.length}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-zinc-800">
        {(["assets", "transactions", "defi"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? "border-vault-500 text-vault-400"
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {tab === "defi" ? "DeFi Positions" : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "assets" && (
        <AssetTable assets={treasury?.assets ?? []} loading={isLoading} />
      )}
      {activeTab === "transactions" && (
        <TransactionHistory transactions={transactions ?? []} />
      )}
      {activeTab === "defi" && (
        <div className="glass-card rounded-xl p-8 text-center text-zinc-500">
          {/* TODO: DeFi position cards — LP pools, yield farms via okx-defi-portfolio */}
          DeFi positions loaded from <code>okx-defi-portfolio</code> skill
        </div>
      )}
    </div>
  );
}
