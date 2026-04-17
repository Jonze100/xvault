// =============================================================================
// Transaction History — Swap, invest, and fee transactions
// =============================================================================

"use client";

import { formatDistanceToNow, parseISO } from "date-fns";
import type { Transaction } from "@/lib/types";
import { clsx } from "clsx";

const STATUS_STYLES: Record<string, string> = {
  pending:   "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  confirmed: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  failed:    "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

const TYPE_ICONS: Record<string, string> = {
  swap:     "🔄",
  invest:   "📈",
  bridge:   "🌉",
  fee:      "💸",
  transfer: "➡️",
};

interface Props {
  transactions: Transaction[];
}

export default function TransactionHistory({ transactions }: Props) {
  if (transactions.length === 0) {
    return (
      <div className="glass-card rounded-xl p-8 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-600">No transactions yet</p>
        <p className="text-xs text-zinc-400 dark:text-zinc-700 mt-1">Transactions will appear here when agents execute trades on X Layer</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl overflow-x-auto">
      <table className="w-full text-sm min-w-[560px]">
        <thead>
          <tr className="border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500">
            <th className="text-left px-4 py-3 font-medium">Type</th>
            <th className="text-left px-4 py-3 font-medium">Trade</th>
            <th className="text-right px-4 py-3 font-medium">Value</th>
            <th className="text-right px-4 py-3 font-medium">Agent</th>
            <th className="text-right px-4 py-3 font-medium">Status</th>
            <th className="text-right px-4 py-3 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr
              key={tx.id}
              className="border-b border-zinc-200/50 dark:border-zinc-800/50 hover:bg-zinc-50 dark:hover:bg-zinc-800/30 transition-colors"
            >
              <td className="px-4 py-3">
                <span className="text-base">{TYPE_ICONS[tx.type] ?? "🔸"}</span>
              </td>
              <td className="px-4 py-3">
                <p className="text-zinc-800 dark:text-zinc-200">
                  {tx.from_token} → {tx.to_token}
                </p>
                <a
                  href={`https://www.okx.com/explorer/xlayer/tx/${tx.tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-vault-500 hover:text-vault-400 font-mono"
                >
                  {tx.tx_hash.slice(0, 10)}…
                </a>
              </td>
              <td className="px-4 py-3 text-right font-semibold text-zinc-800 dark:text-zinc-200">
                ${tx.value_usd.toFixed(0)}
              </td>
              <td className="px-4 py-3 text-right capitalize text-zinc-400">
                {tx.agent}
              </td>
              <td className="px-4 py-3 text-right">
                <span
                  className={clsx(
                    "text-xs px-2 py-0.5 rounded-full capitalize",
                    STATUS_STYLES[tx.status]
                  )}
                >
                  {tx.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-xs text-zinc-600">
                {formatDistanceToNow(parseISO(tx.timestamp), { addSuffix: true })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
