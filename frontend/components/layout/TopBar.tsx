"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";
import { useWSConnection } from "@/hooks/useWSConnection";
import {
  Wifi, WifiOff, ExternalLink, Sun, Moon, Menu, Wallet, LogOut,
  Mail, Shield, Loader2, CheckCircle2, X, Copy, Check,
} from "lucide-react";

interface Props {
  onMenuClick?: () => void;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Wallet types ─────────────────────────────────────────────────────────────

type WalletState =
  | { status: "idle" }
  | { status: "connecting" }
  | { status: "connected"; address: string; providerName: string };

type AgenticWalletState =
  | { step: "closed" }
  | { step: "choose" }                       // choose wallet type
  | { step: "email"; email: string }          // enter email
  | { step: "otp"; email: string; code: string; sending: boolean }  // enter OTP
  | { step: "verifying" }
  | { step: "connected"; address: string; email: string };

// ── EIP-1193 provider hook (MetaMask / OKX extension) ───────────────────────

function getProvider(): { provider: EIP1193Provider; name: string } | null {
  if (typeof window === "undefined") return null;
  if (window.okxwallet?.ethereum) return { provider: window.okxwallet.ethereum, name: "OKX" };
  if (window.ethereum) {
    const name = window.ethereum.isMetaMask ? "MetaMask" : "Wallet";
    return { provider: window.ethereum, name };
  }
  return null;
}

function useWalletConnect() {
  const [wallet, setWallet] = useState<WalletState>({ status: "idle" });

  const connect = useCallback(async () => {
    const detected = getProvider();
    if (!detected) return;
    setWallet({ status: "connecting" });
    try {
      const accounts = (await detected.provider.request({
        method: "eth_requestAccounts",
      })) as string[];
      if (accounts.length > 0)
        setWallet({ status: "connected", address: accounts[0], providerName: detected.name });
      else setWallet({ status: "idle" });
    } catch {
      setWallet({ status: "idle" });
    }
  }, []);

  const disconnect = useCallback(() => setWallet({ status: "idle" }), []);
  return { wallet, connect, disconnect };
}

function shortenAddress(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

// ── Agentic Wallet Modal ─────────────────────────────────────────────────────

function AgenticWalletModal({
  state,
  setState,
  onConnected,
}: {
  state: AgenticWalletState;
  setState: (s: AgenticWalletState) => void;
  onConnected: (address: string, email: string) => void;
}) {
  const codeInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");

  if (state.step === "closed") return null;

  const close = () => { setState({ step: "closed" }); setError(""); };

  const sendOtp = async (email: string) => {
    setError("");
    setState({ step: "otp", email, code: "", sending: true });
    try {
      const res = await fetch(`${API}/api/wallet/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Failed to send OTP" }));
        throw new Error(data.detail || "Failed to send OTP");
      }
      setState({ step: "otp", email, code: "", sending: false });
      setTimeout(() => codeInputRef.current?.focus(), 100);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to send OTP");
      setState({ step: "email", email });
    }
  };

  const verifyOtp = async (email: string, code: string) => {
    setError("");
    setState({ step: "verifying" });
    try {
      const res = await fetch(`${API}/api/wallet/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Verification failed");
      const address = data.xlayer_address || data.evm_address;
      if (!address) throw new Error("No wallet address returned");
      setState({ step: "connected", address, email });
      onConnected(address, email);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Verification failed");
      setState({ step: "otp", email, code: "", sending: false });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md mx-4 bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-vault-500" />
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Connect Wallet</h2>
          </div>
          <button onClick={close} className="p-1 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 pb-6">
          {error && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {/* Step: Choose wallet type */}
          {state.step === "choose" && (
            <div className="space-y-3">
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
                Choose how to connect to XVault
              </p>
              <button
                onClick={() => setState({ step: "email", email: "" })}
                className="w-full flex items-center gap-3 p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:border-vault-500 dark:hover:border-vault-500 hover:bg-vault-50 dark:hover:bg-vault-900/20 transition-all group"
              >
                <div className="w-10 h-10 rounded-lg bg-vault-100 dark:bg-vault-900/40 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-vault-600 dark:text-vault-400" />
                </div>
                <div className="text-left">
                  <div className="font-medium text-zinc-900 dark:text-white group-hover:text-vault-600 dark:group-hover:text-vault-400 transition-colors">
                    Agentic Wallet (Email)
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    OKX Onchain OS — no extension needed
                  </div>
                </div>
                <span className="ml-auto text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                  Recommended
                </span>
              </button>

              <button
                onClick={() => {
                  close();
                  // Trigger browser wallet connect via parent
                  const detected = getProvider();
                  if (detected) {
                    detected.provider.request({ method: "eth_requestAccounts" }).catch(() => {});
                  } else {
                    window.open("https://www.okx.com/web3/build/docs/devportal/wallet-extension", "_blank");
                  }
                }}
                className="w-full flex items-center gap-3 p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-all group"
              >
                <div className="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-zinc-500" />
                </div>
                <div className="text-left">
                  <div className="font-medium text-zinc-900 dark:text-white">
                    Browser Wallet
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    MetaMask, OKX Wallet extension
                  </div>
                </div>
              </button>
            </div>
          )}

          {/* Step: Enter email */}
          {state.step === "email" && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (state.email.includes("@")) sendOtp(state.email);
              }}
              className="space-y-4"
            >
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Enter your email to login with OKX Agentic Wallet
              </p>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  type="email"
                  autoFocus
                  placeholder="you@example.com"
                  value={state.email}
                  onChange={(e) => setState({ ...state, email: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-vault-500 focus:border-transparent text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setState({ step: "choose" })}
                  className="px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-sm text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={!state.email.includes("@")}
                  className="flex-1 py-2.5 rounded-xl bg-vault-600 hover:bg-vault-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
                >
                  Send OTP
                </button>
              </div>
            </form>
          )}

          {/* Step: Enter OTP */}
          {state.step === "otp" && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (state.code.length >= 4) verifyOtp(state.email, state.code);
              }}
              className="space-y-4"
            >
              {state.sending ? (
                <div className="flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending OTP to {state.email}...
                </div>
              ) : (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  Enter the verification code sent to <span className="font-medium text-zinc-700 dark:text-zinc-300">{state.email}</span>
                </p>
              )}
              <input
                ref={codeInputRef}
                type="text"
                inputMode="numeric"
                autoFocus
                maxLength={8}
                placeholder="Enter OTP code"
                value={state.code}
                onChange={(e) => setState({ ...state, code: e.target.value.replace(/\D/g, "") })}
                disabled={state.sending}
                className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-vault-500 focus:border-transparent text-center text-2xl tracking-[0.3em] font-mono disabled:opacity-50"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setState({ step: "email", email: state.email })}
                  className="px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-sm text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={state.code.length < 4 || state.sending}
                  className="flex-1 py-2.5 rounded-xl bg-vault-600 hover:bg-vault-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
                >
                  Verify
                </button>
              </div>
              <button
                type="button"
                onClick={() => sendOtp(state.email)}
                className="w-full text-xs text-zinc-400 hover:text-vault-500 transition-colors"
              >
                Didn&apos;t receive it? Resend OTP
              </button>
            </form>
          )}

          {/* Step: Verifying */}
          {state.step === "verifying" && (
            <div className="flex flex-col items-center py-6 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-vault-500" />
              <p className="text-sm text-zinc-500 dark:text-zinc-400">Verifying and connecting wallet...</p>
            </div>
          )}

          {/* Step: Connected */}
          {state.step === "connected" && (
            <div className="flex flex-col items-center py-4 gap-3">
              <CheckCircle2 className="w-10 h-10 text-emerald-500" />
              <p className="text-sm font-medium text-zinc-900 dark:text-white">Wallet Connected!</p>
              <div className="px-3 py-1.5 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-600 dark:text-zinc-400">
                {state.address}
              </div>
              <p className="text-xs text-zinc-400">X Layer (Chain ID: 196)</p>
              <button
                onClick={close}
                className="mt-2 px-6 py-2 rounded-xl bg-vault-600 hover:bg-vault-500 text-white text-sm font-medium transition-colors"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── TopBar Component ─────────────────────────────────────────────────────────

export default function TopBar({ onMenuClick }: Props) {
  const { isConnected, reconnect } = useWSConnection();
  const { theme, setTheme } = useTheme();
  const { wallet, disconnect: disconnectBrowser } = useWalletConnect();
  const [mounted, setMounted] = useState(false);
  const [agenticModal, setAgenticModal] = useState<AgenticWalletState>({ step: "closed" });
  const [agenticWallet, setAgenticWallet] = useState<{ address: string; email: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => setMounted(true), []);

  // On mount, check if there's an existing agentic wallet session
  useEffect(() => {
    fetch(`${API}/api/wallet/status`)
      .then((r) => r.json())
      .then((data) => {
        if (data.logged_in && data.xlayer_address) {
          setAgenticWallet({ address: data.xlayer_address, email: data.email || "" });
        }
      })
      .catch(() => {});
  }, []);

  const handleAgenticConnected = useCallback((address: string, email: string) => {
    setAgenticWallet({ address, email });
  }, []);

  const handleAgenticDisconnect = useCallback(async () => {
    try {
      await fetch(`${API}/api/wallet/logout`, { method: "POST" });
    } catch {}
    setAgenticWallet(null);
    setAgenticModal({ step: "closed" });
  }, []);

  const openConnectModal = useCallback(() => {
    setAgenticModal({ step: "choose" });
  }, []);

  // Determine which wallet is connected (agentic takes priority)
  const connectedWallet = agenticWallet
    ? { address: agenticWallet.address, provider: "Agentic" }
    : wallet.status === "connected"
    ? { address: wallet.address, provider: wallet.providerName }
    : null;

  return (
    <>
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

          {/* Wallet button */}
          {mounted && (
            <>
              {connectedWallet ? (
                <div className="flex items-center gap-1.5">
                  <div
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-vault-100 dark:bg-vault-900/40 border border-vault-200 dark:border-vault-700/40 text-xs text-vault-700 dark:text-vault-400 font-mono cursor-default"
                    title={connectedWallet.address}
                  >
                    {connectedWallet.provider === "Agentic" ? (
                      <Shield className="w-3 h-3 shrink-0 text-vault-600 dark:text-vault-400" />
                    ) : (
                      <Wallet className="w-3 h-3 shrink-0" />
                    )}
                    <span>{shortenAddress(connectedWallet.address)}</span>
                    <span className="hidden sm:inline text-vault-600 font-sans">
                      · {connectedWallet.provider}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(connectedWallet.address);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    title="Copy address"
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-vault-500 hover:bg-vault-100 dark:hover:bg-vault-900/30 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={agenticWallet ? handleAgenticDisconnect : disconnectBrowser}
                    title="Disconnect wallet"
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={openConnectModal}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-vault-600 hover:bg-vault-500 disabled:opacity-60 text-white text-xs font-medium transition-colors"
                >
                  <Wallet className="w-3 h-3" />
                  <span className="hidden sm:inline">Connect Wallet</span>
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

      {/* Agentic Wallet Modal */}
      <AgenticWalletModal
        state={agenticModal}
        setState={setAgenticModal}
        onConnected={handleAgenticConnected}
      />
    </>
  );
}
