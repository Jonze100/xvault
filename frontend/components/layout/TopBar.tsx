// =============================================================================
// Top Bar — Connection Status, Network Info, Theme Toggle, Hamburger Menu
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { useWSConnection } from "@/hooks/useWSConnection";
import { Wifi, WifiOff, ExternalLink, Sun, Moon, Menu } from "lucide-react";

interface Props {
  onMenuClick?: () => void;
}

export default function TopBar({ onMenuClick }: Props) {
  const { isConnected, reconnect } = useWSConnection();
  const { theme, setTheme } = useTheme();
  // Avoid hydration mismatch — only render theme toggle after mount
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="h-14 md:h-16 flex items-center justify-between px-4 md:px-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/50 backdrop-blur-sm shrink-0">
      {/* Left: hamburger (mobile) + network badges */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* Hamburger — mobile only */}
        <button
          onClick={onMenuClick}
          className="md:hidden p-1.5 rounded-lg text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          aria-label="Open navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="hidden sm:inline">OKX X Layer</span>
          <span className="sm:hidden">XLayer</span>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
          Chain ID: 196
        </div>
      </div>

      {/* Right: WS status, theme toggle, explorer link */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* WebSocket status */}
        <button
          onClick={!isConnected ? reconnect : undefined}
          className={`flex items-center gap-1.5 text-xs transition-colors ${
            isConnected
              ? "text-emerald-500 dark:text-emerald-400"
              : "text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 cursor-pointer"
          }`}
        >
          {isConnected ? (
            <Wifi className="w-3.5 h-3.5" />
          ) : (
            <WifiOff className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline">
            {isConnected ? "Live" : "Reconnect"}
          </span>
        </button>

        {/* Light / Dark toggle */}
        {mounted && (
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </button>
        )}

        {/* OKX Explorer link */}
        <a
          href="https://www.okx.com/explorer/xlayer"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden sm:flex items-center gap-1 text-xs text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors"
        >
          Explorer
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
}
