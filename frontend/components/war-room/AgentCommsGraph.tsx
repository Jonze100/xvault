// =============================================================================
// Agent Communications Graph — SVG visualization of inter-agent messages
// Agents arranged in a pentagon; active comms draw animated edges
// =============================================================================

"use client";

import { useMemo } from "react";
import type { Agent, AgentName, AgentMessage } from "@/lib/types";

interface Props {
  agents: Agent[];
  messages: AgentMessage[];
}

// Pentagon layout positions (center at 0,0 in a 400x400 viewBox)
const AGENT_POSITIONS: Record<AgentName, { x: number; y: number }> = {
  signal:    { x: 200, y:  40 },
  risk:      { x: 360, y: 155 },
  execution: { x: 295, y: 340 },
  portfolio: { x: 105, y: 340 },
  economy:   { x:  40, y: 155 },
};

const AGENT_META: Record<AgentName, { emoji: string; color: string }> = {
  signal:    { emoji: "📡", color: "#3b82f6" },
  risk:      { emoji: "🛡️", color: "#f59e0b" },
  execution: { emoji: "⚡", color: "#10b981" },
  portfolio: { emoji: "📊", color: "#8b5cf6" },
  economy:   { emoji: "💸", color: "#f43f5e" },
};

export default function AgentCommsGraph({ agents, messages }: Props) {
  // Get the 5 most recent unique agent pairs that communicated
  const activeEdges = useMemo(() => {
    const seen = new Set<string>();
    const edges: Array<{ from: AgentName; to: AgentName; key: string }> = [];

    for (const msg of messages.slice(0, 20)) {
      if (msg.to_agent === "all") continue;
      const key = [msg.from_agent, msg.to_agent].sort().join("--");
      if (!seen.has(key)) {
        seen.add(key);
        edges.push({ from: msg.from_agent, to: msg.to_agent as AgentName, key });
      }
      if (edges.length >= 5) break;
    }
    return edges;
  }, [messages]);

  const agentNames = Object.keys(AGENT_POSITIONS) as AgentName[];

  return (
    <svg viewBox="0 0 400 400" className="w-full h-full max-h-[400px]">
      {/* Background grid */}
      <defs>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
          <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
        </pattern>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect width="400" height="400" fill="url(#grid)" />

      {/* Static background edges */}
      {agentNames.map((a, i) =>
        agentNames.slice(i + 1).map((b) => {
          const p1 = AGENT_POSITIONS[a];
          const p2 = AGENT_POSITIONS[b];
          return (
            <line
              key={`${a}-${b}-bg`}
              x1={p1.x} y1={p1.y}
              x2={p2.x} y2={p2.y}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1"
            />
          );
        })
      )}

      {/* Active communication edges */}
      {activeEdges.map((edge) => {
        const p1 = AGENT_POSITIONS[edge.from];
        const p2 = AGENT_POSITIONS[edge.to];
        const color = AGENT_META[edge.from].color;
        return (
          <g key={edge.key}>
            <line
              x1={p1.x} y1={p1.y}
              x2={p2.x} y2={p2.y}
              stroke={color}
              strokeWidth="1.5"
              strokeOpacity="0.6"
              strokeDasharray="6 4"
              className="agent-connector"
            />
            {/* Animated packet dot */}
            <circle r="3" fill={color} opacity="0.9" filter="url(#glow)">
              <animateMotion
                dur="1.5s"
                repeatCount="indefinite"
                path={`M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`}
              />
            </circle>
          </g>
        );
      })}

      {/* Agent nodes */}
      {agentNames.map((name) => {
        const pos = AGENT_POSITIONS[name];
        const meta = AGENT_META[name];
        const agent = agents.find((a) => a.name === name);
        const isActive = agent?.status === "active" || agent?.status === "thinking";

        return (
          <g key={name} transform={`translate(${pos.x}, ${pos.y})`}>
            {/* Glow ring for active agents */}
            {isActive && (
              <circle
                r="28"
                fill="none"
                stroke={meta.color}
                strokeWidth="1"
                strokeOpacity="0.4"
              >
                <animate attributeName="r" values="24;32;24" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite" />
              </circle>
            )}

            {/* Node circle */}
            <circle
              r="24"
              fill={`${meta.color}20`}
              stroke={meta.color}
              strokeWidth={isActive ? "2" : "1"}
              strokeOpacity={isActive ? "0.8" : "0.3"}
              filter={isActive ? "url(#glow)" : undefined}
            />

            {/* Emoji */}
            <text
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="18"
              y="-1"
            >
              {meta.emoji}
            </text>

            {/* Label */}
            <text
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="9"
              fill="#a1a1aa"
              y="36"
              className="capitalize"
            >
              {name}
            </text>

            {/* Status dot */}
            <circle
              cx="17" cy="-17" r="4"
              fill={
                agent?.status === "active"   ? "#22c55e" :
                agent?.status === "thinking" ? "#f59e0b" :
                agent?.status === "error"    ? "#ef4444" :
                "#52525b"
              }
            />
          </g>
        );
      })}
    </svg>
  );
}
