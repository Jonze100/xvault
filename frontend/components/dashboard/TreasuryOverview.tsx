// =============================================================================
// Treasury Overview — Pie chart + asset list
// =============================================================================

"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { Treasury } from "@/lib/types";
import { Vault } from "lucide-react";
import { useTheme } from "next-themes";

const COLORS = ["#14b8a6", "#3b82f6", "#8b5cf6", "#f59e0b", "#f43f5e", "#10b981"];

interface Props {
  treasury: Treasury | undefined;
  loading: boolean;
  isOffline?: boolean;
}

export default function TreasuryOverview({ treasury, loading, isOffline }: Props) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-36 bg-zinc-800 rounded-lg animate-pulse mx-auto w-36" />
        {Array(4).fill(0).map((_, i) => (
          <div key={i} className="h-8 bg-zinc-800 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (isOffline) {
    return (
      <div className="flex flex-col items-center justify-center py-8 gap-2">
        <Vault className="w-8 h-8 text-zinc-700" />
        <p className="text-xs text-zinc-500 text-center">
          Backend offline — asset data unavailable
        </p>
      </div>
    );
  }

  const assets = treasury?.assets ?? [];

  if (!assets.length) {
    return (
      <div className="flex flex-col items-center justify-center py-8 gap-2">
        <Vault className="w-8 h-8 text-zinc-700 opacity-40" />
        <p className="text-xs text-zinc-600 text-center">No assets in treasury yet</p>
      </div>
    );
  }

  const pieData = assets.map((a) => ({ name: a.symbol, value: a.value_usd }));

  return (
    <div className="space-y-3">
      {/* Pie Chart */}
      <ResponsiveContainer width="100%" height={140}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            innerRadius={42}
            outerRadius={60}
            paddingAngle={3}
            dataKey="value"
          >
            {pieData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                opacity={0.85}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(val: number) => [
              `$${val.toLocaleString("en-US", { maximumFractionDigits: 0 })}`,
              "Value",
            ]}
            contentStyle={{
              background: isDark ? "#18181b" : "#ffffff",
              border: isDark ? "1px solid #27272a" : "1px solid #e4e4e7",
              borderRadius: "8px",
              fontSize: "12px",
              color: isDark ? "#f4f4f5" : "#18181b",
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Asset List */}
      <div className="space-y-1.5">
        {assets.map((asset, i) => (
          <div key={asset.symbol} className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-sm shrink-0"
              style={{ backgroundColor: COLORS[i % COLORS.length] }}
            />
            <span className="text-xs text-zinc-300 font-medium w-12">
              {asset.symbol}
            </span>
            <div className="flex-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${asset.allocation_pct}%`,
                  backgroundColor: COLORS[i % COLORS.length],
                  opacity: 0.7,
                }}
              />
            </div>
            <span className="text-xs text-zinc-500 w-10 text-right">
              {asset.allocation_pct.toFixed(1)}%
            </span>
            <span
              className={`text-xs w-14 text-right ${
                asset.pnl_24h_pct >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {asset.pnl_24h_pct >= 0 ? "+" : ""}{asset.pnl_24h_pct.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
