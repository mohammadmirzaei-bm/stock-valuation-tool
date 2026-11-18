/**
 * Tailwind config — Stock Valuation frontend.
 *
 * Visual language: Cursor-inspired warm light theme (cream canvas, warm ink,
 * orange brand accent). Every color is a CSS variable (see src/index.css) so
 * the theme — and ECharts, which reads the same variables — stays in sync.
 * Both the palette token names (bg/surface/text/...) and the shadcn/ui
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
        // Every color consumes a solid CSS token (see src/index.css) through
        // color-mix so opacity modifiers (bg-primary/10, border-positive/40)
        // compose alpha AND the Qoder Nudge `--site-*` appearance controls
        // restyle the whole app. At alpha 1 color-mix is byte-identical to the
        // solid token; at alpha p it equals rgb(token / p).
        bg: "color-mix(in srgb, var(--bg) calc(<alpha-value> * 100%), transparent)",
        surface: "color-mix(in srgb, var(--surface) calc(<alpha-value> * 100%), transparent)",
        "surface-2": "color-mix(in srgb, var(--surface-2) calc(<alpha-value> * 100%), transparent)",
        "surface-3": "color-mix(in srgb, var(--surface-3) calc(<alpha-value> * 100%), transparent)",
        border: "color-mix(in srgb, var(--border) calc(<alpha-value> * 100%), transparent)",
        text: "color-mix(in srgb, var(--text) calc(<alpha-value> * 100%), transparent)",
        "text-muted": "color-mix(in srgb, var(--text-muted) calc(<alpha-value> * 100%), transparent)",
        primary: {
          DEFAULT: "color-mix(in srgb, var(--primary) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--primary-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        brand: "color-mix(in srgb, var(--brand) calc(<alpha-value> * 100%), transparent)",
        positive: "color-mix(in srgb, var(--positive) calc(<alpha-value> * 100%), transparent)",
        negative: "color-mix(in srgb, var(--negative) calc(<alpha-value> * 100%), transparent)",
        warning: "color-mix(in srgb, var(--warning) calc(<alpha-value> * 100%), transparent)",

        // shadcn/ui semantic aliases (also solid CSS variables)
        background: "color-mix(in srgb, var(--background) calc(<alpha-value> * 100%), transparent)",
        foreground: "color-mix(in srgb, var(--foreground) calc(<alpha-value> * 100%), transparent)",
        card: {
          DEFAULT: "color-mix(in srgb, var(--card) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--card-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        popover: {
          DEFAULT: "color-mix(in srgb, var(--popover) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--popover-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        secondary: {
          DEFAULT: "color-mix(in srgb, var(--secondary) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--secondary-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        muted: {
          DEFAULT: "color-mix(in srgb, var(--muted) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--muted-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        accent: {
          DEFAULT: "color-mix(in srgb, var(--accent) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--accent-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        destructive: {
          DEFAULT: "color-mix(in srgb, var(--destructive) calc(<alpha-value> * 100%), transparent)",
          foreground: "color-mix(in srgb, var(--destructive-foreground) calc(<alpha-value> * 100%), transparent)",
        },
        input: "color-mix(in srgb, var(--input) calc(<alpha-value> * 100%), transparent)",
        ring: "color-mix(in srgb, var(--ring) calc(<alpha-value> * 100%), transparent)",

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
        // Type ramp scales with the Qoder Nudge typography multiplier
        // (--site-type, default 1). Sizes and rem line-heights are calc-wrapped
        // so the default (multiplier 1) is byte-identical to Tailwind's stock
        // ramp, while every text utility scales proportionally without clipping.
        xs: ["calc(0.75rem * var(--site-type, 1))", { lineHeight: "calc(1rem * var(--site-type, 1))" }],
        sm: ["calc(0.875rem * var(--site-type, 1))", { lineHeight: "calc(1.25rem * var(--site-type, 1))" }],
        base: ["calc(1rem * var(--site-type, 1))", { lineHeight: "calc(1.5rem * var(--site-type, 1))" }],
        lg: ["calc(1.125rem * var(--site-type, 1))", { lineHeight: "calc(1.75rem * var(--site-type, 1))" }],
        xl: ["calc(1.25rem * var(--site-type, 1))", { lineHeight: "calc(1.75rem * var(--site-type, 1))" }],
        "2xl": ["calc(1.5rem * var(--site-type, 1))", { lineHeight: "calc(2rem * var(--site-type, 1))" }],
        "3xl": ["calc(1.875rem * var(--site-type, 1))", { lineHeight: "calc(2.25rem * var(--site-type, 1))" }],
        "4xl": ["calc(2.25rem * var(--site-type, 1))", { lineHeight: "calc(2.5rem * var(--site-type, 1))" }],
        "5xl": ["calc(3rem * var(--site-type, 1))", { lineHeight: "1" }],
        "6xl": ["calc(3.75rem * var(--site-type, 1))", { lineHeight: "1" }],
        "7xl": ["calc(4.5rem * var(--site-type, 1))", { lineHeight: "1" }],
        "8xl": ["calc(6rem * var(--site-type, 1))", { lineHeight: "1" }],
        "9xl": ["calc(8rem * var(--site-type, 1))", { lineHeight: "1" }],
        // Body minimum 15px; table numbers 14px (spec "Shape and spacing")
        body: ["calc(15px * var(--site-type, 1))", { lineHeight: "1.6" }],
        "table-num": ["calc(14px * var(--site-type, 1))", { lineHeight: "1.4" }],
      },
      borderRadius: {
        card: "var(--radius)",
        lg: "calc(var(--radius) - 2px)",
        md: "calc(var(--radius) - 4px)",
        sm: "calc(var(--radius) - 6px)",
      },
      boxShadow: {
        ambient: "var(--shadow-ambient)",
        elevated: "var(--shadow-elevated)",
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
