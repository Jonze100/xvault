"use client";

import { useState, useEffect, useCallback } from "react";
import { formatDistanceToNow, parseISO } from "date-fns";
import { useWSEvents } from "@/hooks/useWSEvents";
import { decisionsApi } from "@/lib/api";
import type { AgentDecision, AgentName } from "@/lib/types";
import { clsx } from "clsx";

const AGENT_COLORS: Record<AgentName, string> = {
  signal:    "text-blue-400 bg-blue-900/30",
  risk:      "text-amber-400 bg-amber-900/30",
  execution: "text-emerald-400 bg-emerald-900/30",
  portfolio: "text-violet-400 bg-violet-900/30",
  economy:   "text-rose-400 bg-rose-900/30",
};

const TYPE_ICONS: Record<string, string> = {
  signal_detected:     "📡",
  risk_assessment:     "🛡️",
  trade_approved:      "✅",
  trade_rejected:      "❌",
  trade_executed:      "⚡",
  position_opened:     "📈",
  position_closed:     "📉",
  fee_collected:       "💰",
  fee_distributed:     "💸",
  rebalance_triggered: "⚖️",
};

export default function RecentDecisions() {
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [isOffline, setIsOffline] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    decisionsApi
      .getAll(1, 20)
      .then((res) => {
        if (res.success) {
          setDecisions(res.data.items);
          setIsOffline(false);
        }
      })
      .catch(() => {
        setIsOffline(true);
      })
      .finally(() => setIsLoading(false));
  }, []);

  // Live updates via WebSocket (works in demo + live mode)
  const handleDecision = useCallback((data: AgentDecision) => {
    setDecisions((prev) => [data, ...prev].slice(0, 50));
    setIsOffline(false);
  }, []);
  useWSEvents("agent_decision", handleDecision);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array(5).fill(0).map((_, i) => (
          <div key={i} className="h-14 rounded-lg bg-zinc-800/50 animate-pulse" />
        ))}
      </div>
    );
  }

  if (isOffline) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-2">
        <span className="text-2xl">📡</span>
        <p className="text-xs text-zinc-500 text-center">
          Backend offline — decisions will appear when connected
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-72 overflow-y-auto">
      {decisions.length === 0 ? (
        <p className="text-xs text-zinc-600 text-center py-8">
          Waiting for agent decisions...
        </p>
      ) : (
        decisions.map((d) => (
          <div
            key={d.id}
            className="flex gap-2.5 p-2.5 rounded-lg bg-zinc-900/50 hover:bg-zinc-900 transition-colors message-bubble"
          >
            {/* Agent Badge */}
            <span
              className={clsx(
                "text-xs px-1.5 py-0.5 rounded font-medium capitalize shrink-0 h-fit",
                AGENT_COLORS[d.agent]
              )}
            >
              {d.agent}
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="text-sm">{TYPE_ICONS[d.type] ?? "🔸"}</span>
                <p className="text-xs text-zinc-200 truncate">{d.reasoning}</p>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-zinc-600">
                  {formatDistanceToNow(parseISO(d.timestamp), {
                    addSuffix: true,
                  })}
                </span>
                {d.tx_hash && (
                  <a
                    href={`https://www.okx.com/explorer/xlayer/tx/${d.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-vault-500 hover:text-vault-400"
                  >
                    {d.tx_hash.slice(0, 6)}…
                  </a>
                )}
                <span className="text-xs text-zinc-700">
                  {(d.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
