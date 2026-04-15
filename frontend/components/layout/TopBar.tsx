"use client";

import { useCallback, useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { useWSConnection } from "@/hooks/useWSConnection";
import { Wifi, WifiOff, ExternalLink, Sun, Moon, Menu, Wallet, LogOut } from "lucide-react";

interface Props {
  onMenuClick?: () => void;
}

// ── OKX Wallet hook ─────────────────────────────────────────────────────────

type WalletState =
  | { status: "idle" }
  | { status: "unavailable" }
  | { status: "connecting" }
  | { status: "connected"; address: string };

function useOKXWallet() {
  const [wallet, setWallet] = useState<WalletState>({ status: "idle" });

  // After mount, check if extension is present
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!window.okxwallet) {
      setWallet({ status: "unavailable" });
    }
    // If already permitted, try to re-use the existing connection
    window.okxwallet?.ethereum
      ?.request({ method: "eth_accounts" })
      .then((raw) => {
        const accounts = raw as string[];
        if (accounts.length > 0) {
          setWallet({ status: "connected", address: accounts[0] });
        }
      })
      .catch(() => {});

    // Listen for account changes
    const handler = (...args: unknown[]) => {
      const accounts = args[0] as string[];
      if (accounts.length === 0) setWallet({ status: "idle" });
      else setWallet({ status: "connected", address: accounts[0] });
    };
    window.okxwallet?.ethereum?.on("accountsChanged", handler);
    return () => {
      window.okxwallet?.ethereum?.removeListener("accountsChanged", handler);
    };
  }, []);

  const connect = useCallback(async () => {
    if (!window.okxwallet) {
      window.open("https://www.okx.com/web3/build/docs/devportal/wallet-extension", "_blank");
      return;
    }
    setWallet({ status: "connecting" });
    try {
      const accounts = (await window.okxwallet.ethereum.request({
        method: "eth_requestAccounts",
      })) as string[];
      if (accounts.length > 0) {
        setWallet({ status: "connected", address: accounts[0] });
      }
    } catch {
      setWallet({ status: "idle" });
    }
  }, []);

  const disconnect = useCallback(() => {
    setWallet({ status: "idle" });
  }, []);

  return { wallet, connect, disconnect };
}

function shortenAddress(addr: string) {
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function TopBar({ onMenuClick }: Props) {
  const { isConnected, reconnect } = useWSConnection();
  const { theme, setTheme } = useTheme();
  const { wallet, connect, disconnect } = useOKXWallet();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="h-14 md:h-16 flex items-center justify-between px-4 md:px-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/50 backdrop-blur-sm shrink-0">
      {/* Left: hamburger + network badges */}
      <div className="flex items-center gap-2 md:gap-3">
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

      {/* Right: WS status, wallet, theme toggle, explorer */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* WebSocket status */}
        <button
          onClick={!isConnected ? reconnect : undefined}
          className={`flex items-center gap-1.5 text-xs transition-colors ${
            isConnected
              ? "text-emerald-500 dark:text-emerald-400"
              : "text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 cursor-pointer"
          }`}
        >
          {isConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          <span className="hidden sm:inline">{isConnected ? "Live" : "Reconnect"}</span>
        </button>

        {/* OKX Wallet button — only after mount to avoid SSR mismatch */}
        {mounted && (
          <>
            {wallet.status === "connected" ? (
              <div className="flex items-center gap-1.5">
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-vault-900/40 border border-vault-700/40 text-xs text-vault-400 font-mono">
                  <Wallet className="w-3 h-3 shrink-0" />
                  <span className="hidden xs:inline">{shortenAddress(wallet.address)}</span>
                </div>
                <button
                  onClick={disconnect}
                  title="Disconnect wallet"
                  className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-900/20 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : wallet.status === "unavailable" ? (
              <a
                href="https://www.okx.com/web3/build/docs/devportal/wallet-extension"
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-zinc-700 text-xs text-zinc-500 hover:text-zinc-300 hover:border-zinc-500 transition-colors"
              >
                <Wallet className="w-3 h-3" />
                Install OKX Wallet
              </a>
            ) : (
              <button
                onClick={connect}
                disabled={wallet.status === "connecting"}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-vault-600 hover:bg-vault-500 disabled:opacity-60 text-white text-xs font-medium transition-colors"
              >
                <Wallet className="w-3 h-3" />
                <span className="hidden sm:inline">
                  {wallet.status === "connecting" ? "Connecting…" : "Connect Wallet"}
                </span>
              </button>
            )}
          </>
        )}

        {/* Theme toggle */}
        {mounted && (
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        )}

        {/* OKX Explorer */}
        <a
          href="https://www.okx.com/explorer/xlayer"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:flex items-center gap-1 text-xs text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors"
        >
          Explorer
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
}
