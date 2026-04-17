// =============================================================================
// Asset Table — Full treasury position table
// =============================================================================

"use client";

import type { TreasuryAsset } from "@/lib/types";

interface Props {
  assets: TreasuryAsset[];
  loading: boolean;
}

export default function AssetTable({ assets, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array(5).fill(0).map((_, i) => (
          <div key={i} className="h-12 glass-card rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="glass-card rounded-xl p-8 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-600">No assets in treasury</p>
        <p className="text-xs text-zinc-400 dark:text-zinc-700 mt-1">Connect your Agentic Wallet to see real balances</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl overflow-x-auto">
      <table className="w-full text-sm min-w-[540px]">
        <thead>
          <tr className="border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500">
            <th className="text-left px-4 py-3 font-medium">Asset</th>
            <th className="text-right px-4 py-3 font-medium">Balance</th>
            <th className="text-right px-4 py-3 font-medium">Price</th>
            <th className="text-right px-4 py-3 font-medium">Value</th>
            <th className="text-right px-4 py-3 font-medium">Allocation</th>
            <th className="text-right px-4 py-3 font-medium">24h PnL</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr
              key={asset.symbol}
              className="border-b border-zinc-200/50 dark:border-zinc-800/50 hover:bg-zinc-50 dark:hover:bg-zinc-800/30 transition-colors"
            >
              <td className="px-4 py-3">
                <div>
                  <p className="font-semibold text-zinc-800 dark:text-zinc-200">{asset.symbol}</p>
                  <p className="text-xs text-zinc-600">{asset.chain}</p>
                </div>
              </td>
              <td className="px-4 py-3 text-right font-mono text-zinc-600 dark:text-zinc-300">
                {asset.balance.toFixed(4)}
              </td>
              <td className="px-4 py-3 text-right text-zinc-600 dark:text-zinc-300">
                ${asset.price_usd.toLocaleString("en-US", { maximumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right font-semibold text-zinc-800 dark:text-zinc-200">
                ${asset.value_usd.toLocaleString("en-US", { maximumFractionDigits: 0 })}
              </td>
              <td className="px-4 py-3 text-right text-zinc-400">
                {asset.allocation_pct.toFixed(1)}%
              </td>
              <td
                className={`px-4 py-3 text-right font-medium ${
                  asset.pnl_24h_pct >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {asset.pnl_24h_pct >= 0 ? "+" : ""}{asset.pnl_24h_pct.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
