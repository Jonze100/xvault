// =============================================================================
// PnL Chart — Area chart showing portfolio value over time
// =============================================================================

"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { usePnLHistory } from "@/hooks/usePnLHistory";
import { format, parseISO } from "date-fns";
import { TrendingUp } from "lucide-react";

interface Props {
  range: "24h" | "7d" | "30d" | "all";
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { pnl_usd: number } }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  const pnl = payload[0].payload.pnl_usd;

  return (
    <div className="glass-card rounded-lg p-3 text-xs shadow-xl">
      <p className="text-zinc-400 mb-1">{label}</p>
      <p className="font-semibold text-zinc-100">
        ${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}
      </p>
      <p className={pnl >= 0 ? "text-emerald-400" : "text-red-400"}>
        {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)} PnL
      </p>
    </div>
  );
}

export default function PnLChart({ range }: Props) {
  const { data, isLoading, isOffline } = usePnLHistory(range);

  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-vault-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isOffline || (!data?.length && !isLoading)) {
    return (
      <div className="h-64 flex flex-col items-center justify-center gap-2 text-zinc-600">
        <TrendingUp className="w-8 h-8 opacity-30" />
        <p className="text-xs text-center">
          {isOffline
            ? "Backend offline — PnL data unavailable"
            : "No chart data yet — agents are warming up"}
        </p>
      </div>
    );
  }

  const formatted = (data ?? []).map((d) => ({
    ...d,
    time:
      range === "24h"
        ? format(parseISO(d.timestamp), "HH:mm")
        : format(parseISO(d.timestamp), "MMM d"),
  }));

  const isPositive = (data?.at(-1)?.pnl_usd ?? 0) >= 0;

  return (
    <ResponsiveContainer width="100%" height={256}>
      <AreaChart data={formatted} margin={{ top: 4, right: 4, bottom: 4, left: 0 }}>
        <defs>
          <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor={isPositive ? "#14b8a6" : "#ef4444"}
              stopOpacity={0.3}
            />
            <stop
              offset="95%"
              stopColor={isPositive ? "#14b8a6" : "#ef4444"}
              stopOpacity={0}
            />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11, fill: "#71717a" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#71717a" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
          width={48}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="value_usd"
          stroke={isPositive ? "#14b8a6" : "#ef4444"}
          strokeWidth={2}
          fill="url(#pnlGradient)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
