import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1a1f",
        shell: "#f4efe6",
        accent: "#ff6b2c",
        pine: "#0f5c4b",
        mist: "#d7e7df",
        steel: "#4d5f66",
      },
      fontFamily: {
        display: ["Georgia", "Cambria", "Times New Roman", "serif"],
        body: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 20px 60px rgba(15, 26, 31, 0.12)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(15,26,31,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(15,26,31,0.06) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
} satisfies Config;
