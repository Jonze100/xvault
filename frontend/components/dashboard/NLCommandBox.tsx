// =============================================================================
// Natural Language Command Box
// Sends plain-text commands to the orchestrator (e.g. "rotate 10% to ETH")
// =============================================================================

"use client";

import { useState, useRef } from "react";
import { Send, Loader2, Terminal } from "lucide-react";
import { commandApi } from "@/lib/api";
import type { CommandResult } from "@/lib/types";

const SUGGESTIONS = [
  "Rotate 10% allocation to ETH",
  "What is our current risk score?",
  "Pause the Signal Agent",
  "Show me top yield opportunities",
  "Rebalance to 60/40 ETH/USDC",
];

export default function NLCommandBox() {
  const [command, setCommand] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CommandResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent | string) => {
    if (typeof e !== "string") e.preventDefault();
    const cmd = typeof e === "string" ? e : command;
    if (!cmd.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      const res = await commandApi.execute(cmd);
      setResult(res.data);
      setCommand("");
    } catch (err) {
      setResult({
        success: false,
        agent: "economy",
        message: "Failed to process command. Check backend connection.",
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="glass-card rounded-xl p-4 border border-vault-800/20">
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="w-3.5 h-3.5 text-vault-500" />
        <p className="text-xs font-medium text-zinc-400">Natural Language Command</p>
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSubmit(s)}
            className="text-xs px-2 py-1 rounded-md bg-zinc-800 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-700 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          ref={inputRef}
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Tell the agents what to do..."
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-vault-500 transition-colors"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !command.trim()}
          className="px-3 py-2 rounded-lg bg-vault-600 hover:bg-vault-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 text-white animate-spin" />
          ) : (
            <Send className="w-4 h-4 text-white" />
          )}
        </button>
      </form>

      {/* Result */}
      {result && (
        <div
          className={`mt-2 p-2.5 rounded-lg text-xs border ${
            result.success
              ? "bg-emerald-900/20 border-emerald-800/30 text-emerald-400"
              : "bg-red-900/20 border-red-800/30 text-red-400"
          }`}
        >
          <span className="font-medium capitalize">[{result.agent}]</span>{" "}
          {result.message}
          {result.action && (
            <span className="ml-2 text-zinc-500">→ {result.action}</span>
          )}
        </div>
      )}
    </div>
  );
}
