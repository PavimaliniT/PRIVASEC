/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: "#0b0f17",
          card: "#111827",
          border: "#1f293d",
          accent: "#06b6d4",
          neon: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
          purple: "#8b5cf6"
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"]
      }
    },
  },
  plugins: [],
}
