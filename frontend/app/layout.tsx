// =============================================================================
// XVault Root Layout
// =============================================================================

import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";
import LayoutShell from "@/components/layout/LayoutShell";
import { WSProvider } from "@/components/layout/WSProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "XVault — Autonomous DeFi Treasury",
  description:
    "Multi-agent AI treasury management on OKX X Layer. Five specialized agents collaborate to maximize yield and minimize risk.",
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "XVault",
    description: "Autonomous DeFi Treasury Management",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          disableTransitionOnChange
        >
          <WSProvider>
            <LayoutShell>{children}</LayoutShell>
          </WSProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
