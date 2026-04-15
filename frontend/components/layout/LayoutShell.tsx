// =============================================================================
// Layout Shell — client component that owns mobile-sidebar state
// Keeps layout.tsx a server component while enabling interactive sidebar toggle
// =============================================================================

"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function LayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        mobileOpen={sidebarOpen}
        onMobileClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <TopBar onMenuClick={() => setSidebarOpen((v) => !v)} />
        <main className="flex-1 overflow-y-auto bg-slate-100 dark:bg-zinc-950 dark:bg-grid-dark dark:bg-grid overflow-x-hidden">
          <div className="min-h-full p-4 md:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
