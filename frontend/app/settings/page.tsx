// =============================================================================
// Settings Page — Thresholds, API Keys, Agent Config
// =============================================================================

"use client";

import { useState } from "react";
import { Save, Eye, EyeOff } from "lucide-react";

interface SettingField {
  key: string;
  label: string;
  description: string;
  type: "text" | "number" | "password";
  value: string | number;
}

const AGENT_SETTINGS: SettingField[] = [
  {
    key: "max_trade_size_usd",
    label: "Max Trade Size (USD)",
    description: "Maximum single trade size the Execution Agent can make",
    type: "number",
    value: 10000,
  },
  {
    key: "min_security_score",
    label: "Min Security Score",
    description: "Risk Agent rejects protocols scoring below this (0-100)",
    type: "number",
    value: 80,
  },
  {
    key: "max_portfolio_concentration",
    label: "Max Concentration (%)",
    description: "Max % allocation to any single asset (0-100)",
    type: "number",
    value: 25,
  },
  {
    key: "performance_fee_bps",
    label: "Performance Fee (bps)",
    description: "Economy Agent fee on profits (100 bps = 1%)",
    type: "number",
    value: 1000,
  },
];

export default function SettingsPage() {
  const [showKeys, setShowKeys] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    // TODO: POST /api/settings with form values
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Settings</h1>
        <p className="text-sm text-zinc-500 mt-0.5">
          Configure agent thresholds, risk limits, and API keys
        </p>
      </div>

      {/* Agent Thresholds */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Agent Thresholds</h2>
        {AGENT_SETTINGS.map((field) => (
          <div key={field.key}>
            <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
              {field.label}
            </label>
            <input
              type={field.type}
              defaultValue={field.value}
              className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-vault-500 transition-colors"
            />
            <p className="text-xs text-zinc-600 mt-1">{field.description}</p>
          </div>
        ))}
      </div>

      {/* API Keys */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">API Keys</h2>
          <button
            onClick={() => setShowKeys(!showKeys)}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            {showKeys ? (
              <EyeOff className="w-3 h-3" />
            ) : (
              <Eye className="w-3 h-3" />
            )}
            {showKeys ? "Hide" : "Show"}
          </button>
        </div>

        {[
          { label: "OKX API Key", key: "okx_api_key" },
          { label: "OKX Secret Key", key: "okx_secret_key" },
          { label: "Anthropic API Key", key: "anthropic_api_key" },
          { label: "Supabase URL", key: "supabase_url" },
        ].map((field) => (
          <div key={field.key}>
            <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
              {field.label}
            </label>
            <input
              type={showKeys ? "text" : "password"}
              placeholder="••••••••••••••••••••"
              className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-vault-500 transition-colors font-mono"
            />
          </div>
        ))}
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
          saved
            ? "bg-emerald-600 text-white"
            : "bg-vault-600 hover:bg-vault-500 text-white"
        }`}
      >
        <Save className="w-4 h-4" />
        {saved ? "Saved!" : "Save Settings"}
      </button>
    </div>
  );
}
