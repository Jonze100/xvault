// =============================================================================
// Agent Earnings Chart — Bar chart showing x402 earnings per agent
// =============================================================================

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useEconomyEarnings } from "@/hooks/useEconomy";
import { useTheme } from "next-themes";

const AGENT_COLORS: Record<string, string> = {
  signal:    "#3b82f6",
  risk:      "#f59e0b",
  execution: "#10b981",
  portfolio: "#8b5cf6",
  economy:   "#f43f5e",
};

export default function AgentEarningsChart() {
  const { earnings, isLoading } = useEconomyEarnings();
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  if (isLoading) {
    return <div className="h-48 bg-zinc-800 rounded-lg animate-pulse" />;
  }

  const data = Object.entries(earnings ?? {}).map(([agent, amount]) => ({
    agent: agent.charAt(0).toUpperCase() + agent.slice(1),
    agent_key: agent,
    amount,
  }));

  return (
    <ResponsiveContainer width="100%" height={192}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 0 }}>
        <XAxis
          dataKey="agent"
          tick={{ fontSize: 11, fill: "#71717a" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#71717a" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${v.toFixed(0)}`}
          width={44}
        />
        <Tooltip
          formatter={(val: number) => [`$${val.toFixed(2)}`, "Earnings"]}
          contentStyle={{
            background: isDark ? "#18181b" : "#ffffff",
            border: isDark ? "1px solid #27272a" : "1px solid #e4e4e7",
            borderRadius: "8px",
            fontSize: "12px",
            color: isDark ? "#f4f4f5" : "#18181b",
          }}
        />
        <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell
              key={entry.agent_key}
              fill={AGENT_COLORS[entry.agent_key] ?? "#71717a"}
              opacity={0.8}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
