// =============================================================================
// Agents Page — Agent Status Cards, Config, Earnings
// =============================================================================

"use client";

import AgentCard from "@/components/agents/AgentCard";
import AgentEarningsChart from "@/components/agents/AgentEarningsChart";
import SkillsTable from "@/components/agents/SkillsTable";
import { useAgents } from "@/hooks/useAgents";

export default function AgentsPage() {
  const { agents, isLoading, refetch } = useAgents();

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Agents</h1>
        <p className="text-sm text-zinc-500 mt-0.5">
          Five autonomous agents with dedicated agentic wallets on OKX X Layer
        </p>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {isLoading
          ? Array(5)
              .fill(0)
              .map((_, i) => (
                <div
                  key={i}
                  className="glass-card rounded-xl p-5 h-48 animate-pulse"
                />
              ))
          : agents?.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onRefresh={refetch}
              />
            ))}
      </div>

      {/* Economy Section */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="glass-card rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-4">
            Agent Earnings (x402)
          </h2>
          <AgentEarningsChart />
        </div>

        <div className="glass-card rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-4">
            OKX Skill Usage
          </h2>
          <SkillsTable />
        </div>
      </div>
    </div>
  );
}
