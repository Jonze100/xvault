// =============================================================================
// Metric Card — Key stat display with trend indicator
// =============================================================================

"use client";

import { TrendingUp, TrendingDown } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  icon: React.ReactNode;
  label: string;
  value: string;
  change?: number;   // percent, positive or negative
  loading?: boolean;
  color?: "vault" | "emerald" | "amber" | "red" | "blue" | "violet";
}

const COLOR_MAP: Record<NonNullable<Props["color"]>, string> = {
  vault:   "text-vault-400 bg-vault-900/40",
  emerald: "text-emerald-400 bg-emerald-900/40",
  amber:   "text-amber-400 bg-amber-900/40",
  red:     "text-red-400 bg-red-900/40",
  blue:    "text-blue-400 bg-blue-900/40",
  violet:  "text-violet-400 bg-violet-900/40",
};

export default function MetricCard({
  icon,
  label,
  value,
  change,
  loading = false,
  color = "vault",
}: Props) {
  const colorClasses = COLOR_MAP[color];

  if (loading) {
    return (
      <div className="glass-card rounded-xl p-4 animate-pulse">
        <div className="h-4 bg-zinc-800 rounded w-20 mb-3" />
        <div className="h-7 bg-zinc-800 rounded w-28" />
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl p-4 hover:border-zinc-700 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-zinc-500">{label}</p>
        <div className={clsx("p-1.5 rounded-md", colorClasses)}>
          {icon}
        </div>
      </div>
      <p className="text-xl font-bold text-zinc-100">{value}</p>
      {change !== undefined && (
        <div
          className={clsx(
            "flex items-center gap-0.5 text-xs mt-1",
            change >= 0 ? "text-emerald-400" : "text-red-400"
          )}
        >
          {change >= 0 ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          {Math.abs(change).toFixed(2)}%
        </div>
      )}
    </div>
  );
}
