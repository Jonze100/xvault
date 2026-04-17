"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import MessageFeed from "@/components/war-room/MessageFeed";
import AgentCommsGraph from "@/components/war-room/AgentCommsGraph";
import LiveDecisionPanel from "@/components/war-room/LiveDecisionPanel";
import { useAgents } from "@/hooks/useAgents";
import { useWSEvents } from "@/hooks/useWSEvents";
import { decisionsApi } from "@/lib/api";
import type { AgentMessage, AgentDecision, AgentName } from "@/lib/types";

/** Convert a decision log entry into a synthetic agent message for the feed. */
function decisionToMessage(d: AgentDecision): AgentMessage {
  return {
    id: d.id,
    from_agent: d.agent as AgentName,
    to_agent: "all",
    content: d.reasoning || `${d.type} — confidence ${(d.confidence * 100).toFixed(0)}%`,
    type: "broadcast",
    timestamp: d.timestamp,
  };
}

export default function WarRoomPage() {
  const { agents } = useAgents();
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const messageEndRef = useRef<HTMLDivElement>(null);

  // Load historical decisions on mount
  useEffect(() => {
    let cancelled = false;
    decisionsApi.getAll(1, 50).then((res) => {
      if (cancelled) return;
      const items = res?.data?.items ?? [];
      if (items.length) {
        setDecisions((prev) => {
          const ids = new Set(prev.map((d) => d.id));
          const merged = [...prev, ...items.filter((d) => !ids.has(d.id))];
          return merged.sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 100);
        });
        setMessages((prev) => {
          const ids = new Set(prev.map((m) => m.id));
          const newMsgs = items.filter((d) => !ids.has(d.id)).map(decisionToMessage);
          const merged = [...prev, ...newMsgs];
          return merged.sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 200);
        });
      }
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  useWSEvents("agent_message", useCallback((data: AgentMessage) => {
    setMessages((prev) => [data, ...prev].slice(0, 200));
  }, []));

  useWSEvents("agent_decision", useCallback((data: AgentDecision) => {
    setDecisions((prev) => [data, ...prev].slice(0, 100));
  }, []));

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col space-y-4 animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-zinc-900 dark:text-zinc-100">War Room</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Live agent-to-agent communication · decisions in real-time
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-400 shrink-0">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="hidden sm:inline">
            {messages.length} msgs · {decisions.length} decisions
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 glass-card rounded-xl p-4 h-[420px] xl:h-[500px]">
          <h2 className="text-sm font-semibold text-zinc-400 mb-3">
            Agent Network
          </h2>
          <AgentCommsGraph agents={agents ?? []} messages={messages} />
        </div>

        <div className="glass-card rounded-xl p-4 flex flex-col h-[420px] xl:h-[500px]">
          <h2 className="text-sm font-semibold text-zinc-400 mb-3 shrink-0">
            Live Decisions
          </h2>
          <div className="flex-1 overflow-y-auto min-h-0">
            <LiveDecisionPanel decisions={decisions} />
          </div>
        </div>
      </div>

      <div className="glass-card rounded-xl p-4 h-[400px] flex flex-col">
        <h2 className="text-sm font-semibold text-zinc-400 mb-3 shrink-0">
          Agent Message Feed
        </h2>
        <div className="flex-1 overflow-y-auto min-h-0">
          <MessageFeed messages={messages} />
          <div ref={messageEndRef} />
        </div>
      </div>
    </div>
  );
}
