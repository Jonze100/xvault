// =============================================================================
// Risk Heatmap — Protocol exposure vs risk score grid
// =============================================================================

"use client";

import { useRiskHeatmap } from "@/hooks/useRiskHeatmap";
import { clsx } from "clsx";
import { Shield } from "lucide-react";

function riskColor(score: number): string {
  if (score < 30) return "bg-emerald-500/20 border-emerald-500/30 text-emerald-400";
  if (score < 60) return "bg-amber-500/20 border-amber-500/30 text-amber-400";
  return "bg-red-500/20 border-red-500/30 text-red-400";
}

function riskLabel(score: number): string {
  if (score < 30) return "Low";
  if (score < 60) return "Med";
  return "High";
}

export default function RiskHeatmap() {
  const { data, isLoading, isOffline } = useRiskHeatmap();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {Array(6).fill(0).map((_, i) => (
          <div key={i} className="h-20 rounded-lg bg-zinc-800 animate-pulse" />
        ))}
      </div>
    );
  }

  if (isOffline) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-2">
        <Shield className="w-8 h-8 text-zinc-700" />
        <p className="text-xs text-zinc-500 text-center">
          Backend offline — risk data unavailable
        </p>
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-2">
        <Shield className="w-8 h-8 text-zinc-700 opacity-40" />
        <p className="text-xs text-zinc-600 text-center">
          No protocol exposures yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-zinc-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-emerald-500/50" /> Low (&lt;30)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-amber-500/50" /> Medium (30–60)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-red-500/50" /> High (&gt;60)
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {data.map((cell) => (
          <div
            key={`${cell.protocol}-${cell.chain}`}
            className={clsx(
              "rounded-lg border p-3 transition-all hover:scale-[1.02]",
              riskColor(cell.risk_score)
            )}
          >
            <div className="flex items-start justify-between">
              <p className="text-xs font-semibold">{cell.protocol}</p>
              <span className="text-xs opacity-70">{riskLabel(cell.risk_score)}</span>
            </div>
            <p className="text-xs opacity-60 mt-0.5">{cell.chain}</p>
            <p className="text-sm font-bold mt-1">
              ${(cell.exposure_usd / 1000).toFixed(1)}K
            </p>
            <div className="mt-1.5 h-1 rounded-full bg-black/20">
              <div
                className="h-full rounded-full bg-current opacity-60"
                style={{ width: `${cell.risk_score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
