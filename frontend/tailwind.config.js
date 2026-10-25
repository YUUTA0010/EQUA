/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: {
          950: "#080c14",
          900: "#0d1220",
          800: "#131a2b",
          700: "#1c2440",
          600: "#2a3355",
        },
        accent: {
          400: "#5fd4ff",
          500: "#2cb8f0",
          600: "#1a94c9",
        },
        signal: {
          amber: "#f5a623",
          green: "#3ddc97",
          red: "#ff6b6b",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 30px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};
