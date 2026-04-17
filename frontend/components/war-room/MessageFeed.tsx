// =============================================================================
// Message Feed — Chronological agent-to-agent messages
// =============================================================================

"use client";

import { formatDistanceToNow, parseISO } from "date-fns";
import type { AgentMessage, AgentName } from "@/lib/types";
import { clsx } from "clsx";

const AGENT_COLORS: Record<AgentName, string> = {
  signal:    "bg-blue-500",
  risk:      "bg-amber-500",
  execution: "bg-emerald-500",
  portfolio: "bg-violet-500",
  economy:   "bg-rose-500",
};

const AGENT_EMOJIS: Record<AgentName, string> = {
  signal:    "📡",
  risk:      "🛡️",
  execution: "⚡",
  portfolio: "📊",
  economy:   "💸",
};

const TYPE_STYLES: Record<string, string> = {
  signal:    "border-blue-800/30",
  request:   "border-zinc-700/30",
  response:  "border-emerald-800/30",
  broadcast: "border-violet-800/30",
};

interface Props {
  messages: AgentMessage[];
}

export default function MessageFeed({ messages }: Props) {
  if (messages.length === 0) {
    return (
      <p className="text-xs text-zinc-600 text-center py-4">
        Waiting for agent messages...
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={clsx(
            "flex gap-2.5 p-2 rounded-lg border message-bubble",
            TYPE_STYLES[msg.type] ?? "border-zinc-800/30",
            "bg-white dark:bg-zinc-900/40"
          )}
        >
          {/* From avatar */}
          <div
            className={clsx(
              "w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0",
              AGENT_COLORS[msg.from_agent] + "/20"
            )}
          >
            {AGENT_EMOJIS[msg.from_agent]}
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 text-xs">
              <span className="font-semibold capitalize text-zinc-300">
                {msg.from_agent}
              </span>
              <span className="text-zinc-700">→</span>
              <span className="capitalize text-zinc-500">
                {msg.to_agent === "all" ? "all agents" : msg.to_agent}
              </span>
              <span
                className={clsx(
                  "ml-auto px-1 py-0.5 rounded text-xs",
                  msg.type === "signal"    ? "text-blue-400 bg-blue-900/20" :
                  msg.type === "broadcast" ? "text-violet-400 bg-violet-900/20" :
                  msg.type === "response"  ? "text-emerald-400 bg-emerald-900/20" :
                  "text-zinc-500 bg-zinc-800"
                )}
              >
                {msg.type}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5 truncate">{msg.content}</p>
          </div>

          {/* Timestamp */}
          <span className="text-xs text-zinc-700 shrink-0 self-end">
            {formatDistanceToNow(parseISO(msg.timestamp), { addSuffix: true })}
          </span>
        </div>
      ))}
    </div>
  );
}
