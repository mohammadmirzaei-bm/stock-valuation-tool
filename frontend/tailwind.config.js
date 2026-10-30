/**
 * پیکربندی Tailwind — آینه بصری داشبورد Streamlit برای فرانت‌اند React.
 *
 * منابع استخراج:
 *   - `.streamlit/config.toml`  → رنگ‌های رابط، معنایی و پالت نمودارها
 *   - `ui/charts.py`            → رنگ‌های Plotly نمودارها و فونت ۱۲ پیکسلی
 *   - `ui/theme.py`             → فونت و ساختار RTL (در `src/index.css`)
 *
 * توجه: پالت نمودارها در `ui/charts.py` آبی پیش‌فرض Plotly
 * `rgb(55, 128, 191)` است که با رنگ اصلی تم (`#1D4ED8`) یکی نیست؛
 * هر دو در دسترس‌اند تا طراح آگاهانه انتخاب کند.
 *
 * @type {import('tailwindcss').Config}
 */

// رنگ دسته‌ای نمودارها (chartCategoricalColors در config.toml)
const chartCategorical = [
  "#1D4ED8",
  "#0D9488",
  "#7C3AED",
  "#DC2626",
  "#D97706",
  "#0284C7",
  "#64748B",
  "#C2410C",
];

// رنگ ترتیبی نمودارها (chartSequentialColors در config.toml)
const chartSequential = [
  "#EFF6FF",
  "#DBEAFE",
  "#BFDBFE",
  "#93C5FD",
  "#60A5FA",
  "#3B82F6",
  "#2563EB",
  "#1D4ED8",
  "#1E40AF",
  "#1E3A8A",
];

module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // رنگ‌های پایه رابط
        primary: "#1D4ED8",
        link: "#1D4ED8",
        canvas: "#FFFFFF",
        surface: "#F1F5F9",
        panel: "#F8FAFC",
        border: "#E2E8F0",
        ink: "#0F172A",

        // رنگ‌های معنایی شاخص‌های مالی
        positive: "#15803D",
        negative: "#B91C1C",
        caution: "#A16207",
        warning: "#C2410C",
        accent: "#6D28D9",
        muted: "#64748B",

        // رنگ‌های نمودار (Plotly در ui/charts.py)
        chart: {
          bar: "rgba(55, 128, 191, 0.7)",
          "bar-stroke": "rgba(55, 128, 191, 1)",
          "bar-alt": "rgba(255, 193, 7, 0.7)",
          line: "#0000FF",
          benchmark: "#ADD8E6",
          marker: "#FF0000",
        },
      },
      fontFamily: {
        // همین ترتیب در ui/charts.py برای فونت نمودارها استفاده می‌شد
        sans: ["Vazirmatn", "Tahoma", "sans-serif"],
      },
      fontSize: {
        // اندازه فونت نمودارهای Plotly
        chart: "12px",
      },
      borderRadius: {
        // baseRadius و buttonRadius در config.toml
        DEFAULT: "8px",
      },
    },
  },
  plugins: [],
};

// برای کتابخانه‌های چارت (Recharts/Plotly.js) که آرایه رنگ می‌خواهند:
//   import { chartCategorical, chartSequential } from "../tailwind.config";
module.exports.chartCategorical = chartCategorical;
module.exports.chartSequential = chartSequential;
