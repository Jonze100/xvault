// =============================================================================
// Agent Card — Individual agent status, wallet, controls
// =============================================================================

"use client";

import { useState } from "react";
import { Play, Pause, Zap, ExternalLink, AlertCircle } from "lucide-react";
import { agentsApi } from "@/lib/api";
import type { Agent, AgentName } from "@/lib/types";
import { clsx } from "clsx";

const AGENT_CONFIG: Record<AgentName, {
  emoji: string;
  color: string;
  borderColor: string;
  skills: string[];
}> = {
  signal: {
    emoji: "📡",
    color: "text-blue-400",
    borderColor: "border-blue-800/40",
    skills: ["okx-dex-signal", "okx-dex-trenches", "okx-dex-market", "okx-dex-token"],
  },
  risk: {
    emoji: "🛡️",
    color: "text-amber-400",
    borderColor: "border-amber-800/40",
    skills: ["okx-security", "okx-audit-log"],
  },
  execution: {
    emoji: "⚡",
    color: "text-emerald-400",
    borderColor: "border-emerald-800/40",
    skills: ["okx-dex-swap", "okx-defi-invest", "okx-onchain-gateway"],
  },
  portfolio: {
    emoji: "📊",
    color: "text-violet-400",
    borderColor: "border-violet-800/40",
    skills: ["okx-wallet-portfolio", "okx-defi-portfolio", "okx-agentic-wallet"],
  },
  economy: {
    emoji: "💸",
    color: "text-rose-400",
    borderColor: "border-rose-800/40",
    skills: ["x402"],
  },
};

interface Props {
  agent: Agent;
  onRefresh: () => void;
}

export default function AgentCard({ agent, onRefresh }: Props) {
  const [isToggling, setIsToggling] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const config = AGENT_CONFIG[agent.name];

  const handleTogglePause = async () => {
    setIsToggling(true);
    setActionError(null);
    try {
      await agentsApi.togglePause(agent.name, agent.status !== "paused");
      onRefresh();
    } catch {
      setActionError("Backend offline — action unavailable");
    } finally {
      setIsToggling(false);
    }
  };

  const handleTriggerRun = async () => {
    setIsTriggering(true);
    setActionError(null);
    try {
      await agentsApi.triggerRun(agent.name);
    } catch {
      setActionError("Backend offline — action unavailable");
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div
      className={clsx(
        "glass-card rounded-xl p-5 border transition-all hover:scale-[1.01]",
        config.borderColor
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">{config.emoji}</span>
          <div>
            <p className={clsx("text-sm font-bold capitalize", config.color)}>
              {agent.name} Agent
            </p>
            <p className="text-xs text-zinc-600 capitalize">{agent.status}</p>
          </div>
        </div>

        {/* Status indicator */}
        <div
          className={clsx(
            "w-2.5 h-2.5 rounded-full mt-1",
            agent.status === "active"   ? "bg-emerald-400 animate-pulse" :
            agent.status === "thinking" ? "bg-amber-400 animate-pulse" :
            agent.status === "error"    ? "bg-red-400" :
            "bg-zinc-600"
          )}
        />
      </div>

      {/* Wallet */}
      <div className="bg-zinc-100 dark:bg-zinc-900/60 rounded-lg p-3 mb-3">
        <p className="text-xs text-zinc-500 dark:text-zinc-600 mb-1">Agentic Wallet</p>
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono text-zinc-600 dark:text-zinc-400">
            {agent.wallet.address.slice(0, 6)}…{agent.wallet.address.slice(-4)}
          </p>
          <a
            href={`https://www.okx.com/explorer/xlayer/address/${agent.wallet.address}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-400 dark:text-zinc-600 hover:text-zinc-600 dark:hover:text-zinc-400 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <div className="flex justify-between mt-2">
          <div>
            <p className="text-xs text-zinc-500 dark:text-zinc-600">Balance</p>
            <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
              ${agent.wallet.balance_usd.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-500 dark:text-zinc-600">Earned</p>
            <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
              +${agent.wallet.earnings_total_usd.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex justify-between text-xs mb-4">
        <div>
          <p className="text-zinc-500 dark:text-zinc-600">Decisions Today</p>
          <p className="text-zinc-800 dark:text-zinc-300 font-semibold">{agent.decisions_today}</p>
        </div>
        <div>
          <p className="text-zinc-500 dark:text-zinc-600">Success Rate</p>
          <p className="text-zinc-800 dark:text-zinc-300 font-semibold">
            {(agent.success_rate * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-zinc-500 dark:text-zinc-600">Loop</p>
          <p className="text-zinc-800 dark:text-zinc-300 font-semibold">
            {agent.loop_interval_seconds / 60}m
          </p>
        </div>
      </div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1 mb-4">
        {config.skills.map((skill) => (
          <span
            key={skill}
            className="text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-500 font-mono"
          >
            {skill}
          </span>
        ))}
      </div>

      {/* Action error */}
      {actionError && (
        <div className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400 mb-3 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800/30">
          <AlertCircle className="w-3 h-3 shrink-0" />
          {actionError}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleTogglePause}
          disabled={isToggling}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200 hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors disabled:opacity-50"
        >
          {agent.status === "paused" ? (
            <><Play className="w-3 h-3" /> Resume</>
          ) : (
            <><Pause className="w-3 h-3" /> Pause</>
          )}
        </button>
        <button
          onClick={handleTriggerRun}
          disabled={isTriggering}
          className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-vault-50 dark:bg-vault-900/50 border border-vault-200 dark:border-vault-800/50 text-xs text-vault-600 dark:text-vault-400 hover:bg-vault-100 dark:hover:bg-vault-900 transition-colors disabled:opacity-50"
        >
          <Zap className="w-3 h-3" />
          Run
        </button>
      </div>
    </div>
  );
}
