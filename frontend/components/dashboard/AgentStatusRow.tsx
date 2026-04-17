// =============================================================================
// Agent Status Row — Compact strip showing all 5 agent statuses
// =============================================================================

"use client";

import { clsx } from "clsx";
import type { Agent, AgentName } from "@/lib/types";

const AGENT_META: Record<AgentName, { emoji: string; color: string }> = {
  signal:    { emoji: "📡", color: "bg-blue-500" },
  risk:      { emoji: "🛡️", color: "bg-amber-500" },
  execution: { emoji: "⚡", color: "bg-emerald-500" },
  portfolio: { emoji: "📊", color: "bg-violet-500" },
  economy:   { emoji: "💸", color: "bg-rose-500" },
};

const STATUS_RING: Record<string, string> = {
  active:   "status-ring-active",
  thinking: "status-ring-thinking",
  error:    "status-ring-error",
  idle:     "",
  paused:   "",
};

interface Props {
  agents: Agent[];
  loading: boolean;
}

export default function AgentStatusRow({ agents, loading }: Props) {
  if (loading) {
    return (
      <div className="flex gap-3">
        {Array(5).fill(0).map((_, i) => (
          <div key={i} className="flex-1 h-14 glass-card rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-3">
      {agents.map((agent) => {
        const meta = AGENT_META[agent.name];
        return (
          <div
            key={agent.id}
            className="flex-1 min-w-[140px] glass-card rounded-lg px-3 py-2.5 flex items-center gap-2.5"
          >
            {/* Avatar */}
            <div
              className={clsx(
                "w-8 h-8 rounded-full flex items-center justify-center text-base shrink-0",
                meta.color + "/20",
                STATUS_RING[agent.status]
              )}
            >
              {meta.emoji}
            </div>

            {/* Info */}
            <div className="min-w-0">
              <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 capitalize truncate">
                {agent.name} Agent
              </p>
              <p className="text-xs text-zinc-600 capitalize">{agent.status}</p>
            </div>

            {/* Status dot */}
            <div
              className={clsx(
                "w-2 h-2 rounded-full shrink-0 ml-auto",
                agent.status === "active"   ? "bg-emerald-400 animate-pulse" :
                agent.status === "thinking" ? "bg-amber-400 animate-pulse" :
                agent.status === "error"    ? "bg-red-400" :
                "bg-zinc-600"
              )}
            />
          </div>
        );
      })}
    </div>
  );
}
