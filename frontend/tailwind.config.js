/**
 * Tailwind config — Stock Valuation frontend.
 *
 * Visual language is defined by the design spec (authoritative) as a dark,
 * serious financial-analysis theme. Every color is exposed as a CSS variable
 * (see src/index.css) so a second theme later is a variable swap, not a
 * rewrite. Both the spec token names (bg/surface/text/...) and the shadcn/ui
 * semantic aliases (background/card/primary/...) are mapped here.
 *
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1rem",
      screens: { "2xl": "1440px" },
    },
    extend: {
      colors: {
        // Spec color tokens (dark theme)
        bg: "var(--bg)",
        surface: "var(--surface)",
        border: "var(--border)",
        text: "var(--text)",
        "text-muted": "var(--text-muted)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        positive: "var(--positive)",
        negative: "var(--negative)",
        warning: "var(--warning)",

        // shadcn/ui semantic aliases (also defined as CSS variables)
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        input: "var(--input)",
        ring: "var(--ring)",

        // Chart series literals (ECharts reads these from CSS variables at runtime)
        chart: {
          line: "var(--primary)",
          bar: "var(--chart-bar)",
          positive: "var(--positive)",
          negative: "var(--negative)",
          warning: "var(--warning)",
        },
      },
      fontFamily: {
        sans: ["Vazirmatn", "Tahoma", "sans-serif"],
        mono: ["'JetBrains Mono Variable'", "'JetBrains Mono'", "ui-monospace", "monospace"],
        numeric: ["'JetBrains Mono Variable'", "'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      fontSize: {
        // Body minimum 15px; table numbers 14px (spec "Shape and spacing")
        body: ["15px", { lineHeight: "1.6" }],
        "table-num": ["14px", { lineHeight: "1.4" }],
      },
      borderRadius: {
        card: "var(--radius)",
        lg: "calc(var(--radius) - 2px)",
        md: "calc(var(--radius) - 4px)",
        sm: "calc(var(--radius) - 6px)",
      },
      spacing: {
        // 8px spacing grid
        grid: "8px",
        colgap: "24px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.18s ease-out",
        "accordion-up": "accordion-up 0.18s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
