import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0f17",
        panel: "#111827",
        border: "#1f2937",
        accent: "#00d9a3",
        danger: "#ff5566",
      },
    },
  },
  plugins: [],
};
export default config;
