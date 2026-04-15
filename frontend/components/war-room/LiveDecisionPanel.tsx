// =============================================================================
// Live Decision Panel — Streaming agent decisions in war room
// =============================================================================

"use client";

import { formatDistanceToNow, parseISO } from "date-fns";
import type { AgentDecision, AgentName } from "@/lib/types";
import { clsx } from "clsx";

const AGENT_COLORS: Record<AgentName, string> = {
  signal:    "text-blue-400 border-blue-800/40",
  risk:      "text-amber-400 border-amber-800/40",
  execution: "text-emerald-400 border-emerald-800/40",
  portfolio: "text-violet-400 border-violet-800/40",
  economy:   "text-rose-400 border-rose-800/40",
};

interface Props {
  decisions: AgentDecision[];
}

export default function LiveDecisionPanel({ decisions }: Props) {
  if (decisions.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-xs text-zinc-600">No decisions yet...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto space-y-2">
      {decisions.map((d) => (
        <div
          key={d.id}
          className={clsx(
            "p-3 rounded-lg border bg-zinc-900/40 message-bubble",
            AGENT_COLORS[d.agent]
          )}
        >
          {/* Agent + confidence */}
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold capitalize">{d.agent}</span>
            <span className="text-xs opacity-60">
              {(d.confidence * 100).toFixed(0)}% conf
            </span>
          </div>

          {/* Reasoning */}
          <p className="text-xs text-zinc-300 leading-relaxed">{d.reasoning}</p>

          {/* Footer */}
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs opacity-50 capitalize">
              {d.type.replace(/_/g, " ")}
            </span>
            <span className="text-xs opacity-40">
              {formatDistanceToNow(parseISO(d.timestamp), { addSuffix: true })}
            </span>
          </div>

          {/* Confidence bar */}
          <div className="mt-2 h-0.5 rounded-full bg-black/30">
            <div
              className="h-full rounded-full bg-current opacity-40"
              style={{ width: `${d.confidence * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
