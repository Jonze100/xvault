"use client";

import { useEffect, useRef, useState } from "react";
import MessageFeed from "@/components/war-room/MessageFeed";
import AgentCommsGraph from "@/components/war-room/AgentCommsGraph";
import LiveDecisionPanel from "@/components/war-room/LiveDecisionPanel";
import { useAgents } from "@/hooks/useAgents";
import { useWSEvents } from "@/hooks/useWSEvents";
import type { AgentMessage, AgentDecision } from "@/lib/types";

export default function WarRoomPage() {
  const { agents } = useAgents();
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const messageEndRef = useRef<HTMLDivElement>(null);

  useWSEvents("agent_message", (data: AgentMessage) => {
    setMessages((prev) => [data, ...prev].slice(0, 200));
  });

  useWSEvents("agent_decision", (data: AgentDecision) => {
    setDecisions((prev) => [data, ...prev].slice(0, 100));
  });

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col space-y-4 animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-zinc-100">War Room</h1>
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
        <div className="xl:col-span-2 glass-card rounded-xl p-4 min-h-[300px] md:min-h-[420px] xl:min-h-[500px]">
          <h2 className="text-sm font-semibold text-zinc-400 mb-3">
            Agent Network
          </h2>
          <AgentCommsGraph agents={agents ?? []} messages={messages} />
        </div>

        <div className="glass-card rounded-xl p-4 flex flex-col min-h-[300px] md:min-h-[420px] xl:min-h-[500px]">
          <h2 className="text-sm font-semibold text-zinc-400 mb-3">
            Live Decisions
          </h2>
          <LiveDecisionPanel decisions={decisions} />
        </div>
      </div>

      <div className="glass-card rounded-xl p-4 max-h-72 overflow-y-auto">
        <h2 className="text-sm font-semibold text-zinc-400 mb-3">
          Agent Message Feed
        </h2>
        <MessageFeed messages={messages} />
        <div ref={messageEndRef} />
      </div>
    </div>
  );
}
