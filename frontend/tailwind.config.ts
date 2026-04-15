import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // XVault brand palette
        vault: {
          50: "#f0fdf9",
          100: "#ccfbef",
          200: "#99f6e0",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },
        // Agent accent colors
        agent: {
          signal: "#3b82f6",    // blue
          risk: "#f59e0b",      // amber
          execution: "#10b981", // emerald
          portfolio: "#8b5cf6", // violet
          economy: "#f43f5e",   // rose
        },
        // Status colors
        status: {
          active: "#22c55e",
          idle: "#94a3b8",
          thinking: "#f59e0b",
          error: "#ef4444",
          success: "#22c55e",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "slide-up": "slideUp 0.3s ease-out",
        "fade-in": "fadeIn 0.2s ease-out",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px rgb(20 184 166 / 0.3)" },
          "100%": { boxShadow: "0 0 20px rgb(20 184 166 / 0.8)" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      backgroundImage: {
        "grid-dark": "linear-gradient(rgba(20, 184, 166, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(20, 184, 166, 0.05) 1px, transparent 1px)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-vault": "linear-gradient(135deg, #0f766e 0%, #1e1b4b 100%)",
      },
      backgroundSize: {
        grid: "32px 32px",
      },
    },
  },
  plugins: [],
};

export default config;
