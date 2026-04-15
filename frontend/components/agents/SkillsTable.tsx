// =============================================================================
// Skills Table — OKX skill usage by agent
// =============================================================================

"use client";

const SKILLS_DATA = [
  { agent: "Signal",    skill: "okx-dex-signal",       usage: "ML trade signals",         calls: 142 },
  { agent: "Signal",    skill: "okx-dex-trenches",      usage: "Mempool sentiment",        calls: 89 },
  { agent: "Signal",    skill: "okx-dex-market",        usage: "Real-time prices",         calls: 512 },
  { agent: "Signal",    skill: "okx-dex-token",         usage: "Token analytics",          calls: 67 },
  { agent: "Risk",      skill: "okx-security",          usage: "Contract scoring",         calls: 45 },
  { agent: "Risk",      skill: "okx-audit-log",         usage: "Protocol audit history",   calls: 23 },
  { agent: "Execution", skill: "okx-dex-swap",          usage: "Onchain token swaps",      calls: 18 },
  { agent: "Execution", skill: "okx-defi-invest",       usage: "LP/yield deployment",      calls: 7  },
  { agent: "Execution", skill: "okx-onchain-gateway",   usage: "Cross-chain bridging",     calls: 3  },
  { agent: "Portfolio", skill: "okx-wallet-portfolio",  usage: "Wallet position tracking", calls: 288 },
  { agent: "Portfolio", skill: "okx-defi-portfolio",    usage: "DeFi aggregation",         calls: 144 },
  { agent: "Portfolio", skill: "okx-agentic-wallet",    usage: "Agent wallet mgmt",        calls: 36 },
  { agent: "Economy",   skill: "x402",                  usage: "Micropayments",            calls: 12 },
];

const AGENT_COLORS: Record<string, string> = {
  Signal:    "text-blue-400 bg-blue-900/30",
  Risk:      "text-amber-400 bg-amber-900/30",
  Execution: "text-emerald-400 bg-emerald-900/30",
  Portfolio: "text-violet-400 bg-violet-900/30",
  Economy:   "text-rose-400 bg-rose-900/30",
};

export default function SkillsTable() {
  return (
    <div className="overflow-y-auto max-h-64">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-zinc-600 border-b border-zinc-800">
            <th className="text-left py-2 font-medium">Agent</th>
            <th className="text-left py-2 font-medium">Skill</th>
            <th className="text-right py-2 font-medium">Calls</th>
          </tr>
        </thead>
        <tbody>
          {SKILLS_DATA.map((row, i) => (
            <tr key={i} className="border-b border-zinc-800/40 hover:bg-zinc-800/20">
              <td className="py-1.5">
                <span
                  className={`px-1.5 py-0.5 rounded text-xs font-medium ${AGENT_COLORS[row.agent]}`}
                >
                  {row.agent}
                </span>
              </td>
              <td className="py-1.5 font-mono text-zinc-400">{row.skill}</td>
              <td className="py-1.5 text-right text-zinc-500">{row.calls}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
