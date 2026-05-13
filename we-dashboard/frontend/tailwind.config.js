/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0d12",
        panel: "#11141b",
        panel2: "#161a24",
        border: "#232a39",
        accent: "#7c5cff",
        accent2: "#22d3ee",
        good: "#22c55e",
        warn: "#f59e0b",
        bad: "#ef4444",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Arial"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};
