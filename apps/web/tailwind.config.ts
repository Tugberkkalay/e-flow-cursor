import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Display"',
          '"SF Pro Text"',
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        background: "#F7F8FA",
        surface: "#FFFFFF",
        "surface-hover": "#F3F4F6",
        border: "#E5E7EB",
        "border-subtle": "#F0F1F3",
        accent: {
          DEFAULT: "#1A1F36",
          soft: "#EEF0F8",
          muted: "#6B7280",
        },
        primary: {
          DEFAULT: "#1A1F36",
          hover: "#0F1221",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F3F4F6",
          foreground: "#1A1F36",
        },
        destructive: {
          DEFAULT: "#EF4444",
          foreground: "#FFFFFF",
          soft: "#FEF2F2",
        },
        success: {
          DEFAULT: "#22C55E",
          soft: "#F0FDF4",
          foreground: "#166534",
        },
        warning: {
          DEFAULT: "#F59E0B",
          soft: "#FFFBEB",
          foreground: "#92400E",
        },
        info: {
          DEFAULT: "#3B82F6",
          soft: "#EFF6FF",
          foreground: "#1D4ED8",
        },
        muted: {
          DEFAULT: "#F9FAFB",
          foreground: "#6B7280",
        },
        node: {
          trigger: "#E0E7FF",
          "trigger-border": "#6366F1",
          human: "#DCFCE7",
          "human-border": "#22C55E",
          approval: "#FEF9C3",
          "approval-border": "#EAB308",
          logic: "#F3E8FF",
          "logic-border": "#A855F7",
          data: "#E0F2FE",
          "data-border": "#0EA5E9",
          integration: "#FEE2E2",
          "integration-border": "#EF4444",
          compliance: "#FFEDD5",
          "compliance-border": "#F97316",
          event: "#F1F5F9",
          "event-border": "#94A3B8",
        },
      },
      borderRadius: {
        xs: "4px",
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "12px",
        xl: "16px",
        "2xl": "20px",
        "3xl": "24px",
      },
      boxShadow: {
        xs: "0 1px 2px rgba(0,0,0,0.04)",
        sm: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        DEFAULT: "0 2px 8px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.05)",
        md: "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)",
        lg: "0 8px 24px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.05)",
        xl: "0 16px 40px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06)",
        node: "0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)",
        "node-selected": "0 0 0 2px #1A1F36, 0 4px 12px rgba(26,31,54,0.15)",
      },
      transitionTimingFunction: {
        apple: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
      },
      animation: {
        "fade-in": "fadeIn 150ms cubic-bezier(0.25,0.46,0.45,0.94)",
        "slide-in-right": "slideInRight 200ms cubic-bezier(0.25,0.46,0.45,0.94)",
        "slide-in-up": "slideInUp 150ms cubic-bezier(0.25,0.46,0.45,0.94)",
        "scale-in": "scaleIn 150ms cubic-bezier(0.25,0.46,0.45,0.94)",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideInRight: { from: { transform: "translateX(12px)", opacity: "0" }, to: { transform: "translateX(0)", opacity: "1" } },
        slideInUp: { from: { transform: "translateY(8px)", opacity: "0" }, to: { transform: "translateY(0)", opacity: "1" } },
        scaleIn: { from: { transform: "scale(0.96)", opacity: "0" }, to: { transform: "scale(1)", opacity: "1" } },
      },
    },
  },
  plugins: [],
};

export default config;
