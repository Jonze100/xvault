// =============================================================================
// Sidebar Navigation — desktop static + mobile off-canvas drawer
// =============================================================================

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Vault,
  Bot,
  Sword,
  Settings,
  Activity,
  X,
} from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/treasury", label: "Treasury", icon: Vault },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/war-room", label: "War Room", icon: Sword },
  { href: "/settings", label: "Settings", icon: Settings },
];

interface Props {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export default function Sidebar({ mobileOpen = false, onMobileClose }: Props) {
  const pathname = usePathname();

  const navLinks = (fullLabels: boolean) =>
    NAV_ITEMS.map(({ href, label, icon: Icon }) => {
      const isActive = pathname.startsWith(href);
      return (
        <Link
          key={href}
          href={href}
          onClick={onMobileClose}
          className={clsx(
            "flex items-center gap-3 px-2 py-2 rounded-lg text-sm transition-all",
            isActive
              ? "bg-vault-900/60 text-vault-400 border border-vault-800/50"
              : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800"
          )}
        >
          <Icon className="w-4 h-4 shrink-0" />
          {fullLabels ? (
            <span>{label}</span>
          ) : (
            <span className="hidden lg:block">{label}</span>
          )}
        </Link>
      );
    });

  return (
    <>
      {/* ── Desktop sidebar (hidden on mobile) ─────────────────────────── */}
      <aside className="hidden md:flex md:w-16 lg:w-56 flex-col bg-zinc-900 border-r border-zinc-800 shrink-0">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-zinc-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vault-500 to-vault-700 flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="hidden lg:block text-sm font-bold text-zinc-100 vault-glow">
              XVault
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navLinks(false)}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800">
          <p className="hidden lg:block text-xs text-zinc-600">
            OKX X Layer · v0.1.0
          </p>
        </div>
      </aside>

      {/* ── Mobile drawer (off-canvas, z-30, above backdrop z-20) ──────── */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 w-64 flex flex-col bg-zinc-900 border-r border-zinc-800 transition-transform duration-300 ease-in-out md:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header with close button */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-zinc-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vault-500 to-vault-700 flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-bold text-zinc-100 vault-glow">
              XVault
            </span>
          </div>
          <button
            onClick={onMobileClose}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Nav — full labels in drawer */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navLinks(true)}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800">
          <p className="text-xs text-zinc-600">OKX X Layer · v0.1.0</p>
        </div>
      </aside>
    </>
  );
}
